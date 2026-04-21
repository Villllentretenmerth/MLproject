from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from .database import DEFAULT_DB_PATH, get_connection, init_db
from .importers import import_resume_file, import_vacancy_json
from .scoring import (
    VacancyRequirement,
    calculate_score,
    get_vacancy_payload,
    score_all_resumes_for_vacancy,
    score_resume_against_vacancy,
)
from .text_utils import clean_text

app = FastAPI(title="Candidate Scoring MVP")

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

init_db(DEFAULT_DB_PATH)


class SkillInput(BaseModel):
    skill: str = Field(..., description="Название навыка")
    weight: float = Field(default=1.0, description="Вес навыка")
    min_years: float | None = Field(default=None, description="Минимальный опыт в годах")
    aliases: list[str] = Field(default_factory=list, description="Синонимы навыка")


class ScoreTextRequest(BaseModel):
    vacancy_text: str = Field(..., description="Текст вакансии")
    resume_text: str = Field(..., description="Текст резюме")
    backend: str = Field(default="auto", description="auto | hf")
    model_name: str | None = Field(default=None, description="Необязательное имя HF-модели")
    vacancy_min_years: float | None = Field(default=None, description="Минимальный общий опыт по вакансии")
    required_skills: list[SkillInput] = Field(default_factory=list)
    optional_skills: list[SkillInput] = Field(default_factory=list)


def build_requirements_from_request(payload: ScoreTextRequest):
    requirements: list[VacancyRequirement] = []
    seq_id = 1

    for item in payload.required_skills:
        aliases = [item.skill, *item.aliases]
        requirements.append(
            VacancyRequirement(
                skill_id=seq_id,
                skill_name=item.skill,
                is_required=True,
                weight=float(item.weight),
                min_years=item.min_years,
                aliases=sorted(set(a.strip() for a in aliases if a and a.strip()), key=len, reverse=True),
            )
        )
        seq_id += 1

    for item in payload.optional_skills:
        aliases = [item.skill, *item.aliases]
        requirements.append(
            VacancyRequirement(
                skill_id=seq_id,
                skill_name=item.skill,
                is_required=False,
                weight=float(item.weight),
                min_years=item.min_years,
                aliases=sorted(set(a.strip() for a in aliases if a and a.strip()), key=len, reverse=True),
            )
        )
        seq_id += 1

    return requirements


@app.post("/vacancies")
def create_vacancy(payload: dict[str, Any]):
    tmp_path = BASE_DIR / "data" / "vacancies" / "vacancy_from_api.json"
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    vacancy_id = import_vacancy_json(tmp_path)
    return {"vacancy_id": vacancy_id, "message": "Vacancy saved"}


@app.get("/vacancies/{vacancy_id}")
def get_vacancy(vacancy_id: int):
    try:
        vacancy = get_vacancy_payload(vacancy_id, db_path=DEFAULT_DB_PATH)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "id": vacancy["id"],
        "title": vacancy["title"],
        "description": vacancy["description"],
        "raw_text": vacancy.get("raw_text"),
        "min_years_experience": vacancy.get("min_years_experience"),
        "requirements": [
            {
                "skill_id": req.skill_id,
                "skill_name": req.skill_name,
                "is_required": req.is_required,
                "weight": req.weight,
                "min_years": req.min_years,
                "aliases": req.aliases,
            }
            for req in vacancy["requirements"]
        ],
    }


@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".pdf"}:
        raise HTTPException(status_code=400, detail="Поддерживаются только TXT и PDF")

    data = await file.read()
    target = BASE_DIR / "data" / "resumes" / (file.filename or "resume.txt")
    target.write_bytes(data)

    resume_id = import_resume_file(target)
    return {"resume_id": resume_id, "filename": target.name, "message": "Resume saved"}


@app.post("/resumes/manual")
def create_resume_from_text(full_name: str = Form(...), resume_text: str = Form(...)):
    text = clean_text(resume_text)
    with get_connection(DEFAULT_DB_PATH) as conn:
        cur = conn.execute("INSERT INTO candidates(full_name) VALUES (?)", (full_name,))
        candidate_id = int(cur.lastrowid)

        cur = conn.execute(
            """
            INSERT INTO resumes(candidate_id, source_type, source_name, raw_text, cleaned_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, "MANUAL", f"{full_name}.txt", resume_text, text),
        )
        resume_id = int(cur.lastrowid)
        conn.commit()

    return {"resume_id": resume_id, "message": "Manual resume saved"}


@app.get("/db/summary")
def db_summary():
    result: dict[str, int] = {}
    with get_connection(DEFAULT_DB_PATH) as conn:
        for table in [
            "vacancies",
            "candidates",
            "resumes",
            "skills",
            "skill_aliases",
            "vacancy_skill_requirements",
            "scores",
            "score_skill_matches",
        ]:
            result[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return result


@app.post("/score/vacancies/{vacancy_id}/resumes/{resume_id}")
def score_single_resume(
    vacancy_id: int,
    resume_id: int,
    backend: str = Query(default="auto", description="auto | hf"),
    model_name: str | None = Query(default=None),
):
    try:
        return score_resume_against_vacancy(
            vacancy_id=vacancy_id,
            resume_id=resume_id,
            db_path=DEFAULT_DB_PATH,
            backend=backend,
            model_name=model_name,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "Unsupported semantic backend" in message else 404
        raise HTTPException(status_code=status_code, detail=message) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/score/vacancies/{vacancy_id}")
def score_vacancy(
    vacancy_id: int,
    backend: str = Query(default="auto", description="auto | hf"),
    model_name: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1),
):
    try:
        items = score_all_resumes_for_vacancy(
            vacancy_id=vacancy_id,
            db_path=DEFAULT_DB_PATH,
            backend=backend,
            model_name=model_name,
            limit=limit,
        )
        return {
            "vacancy_id": vacancy_id,
            "backend": backend,
            "limit": limit,
            "total": len(items),
            "items": items,
        }
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "Unsupported semantic backend" in message else 404
        raise HTTPException(status_code=status_code, detail=message) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
