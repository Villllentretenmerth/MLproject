from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

init_db(DEFAULT_DB_PATH)


def parse_skill_lines(value: str, default_weight: float):
    items: list[dict[str, Any]] = []
    for raw_item in value.replace(",", "\n").splitlines():
        skill = raw_item.strip()
        if not skill:
            continue
        items.append({"skill": skill, "weight": default_weight})
    return items


def list_vacancies():
    with get_connection(DEFAULT_DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT
                v.id,
                v.title,
                v.min_years_experience,
                COUNT(vsr.skill_id) AS requirements_count
            FROM vacancies v
            LEFT JOIN vacancy_skill_requirements vsr ON vsr.vacancy_id = v.id
            GROUP BY v.id
            ORDER BY v.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_resumes():
    with get_connection(DEFAULT_DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT
                r.id,
                c.full_name,
                r.source_type,
                r.source_name,
                r.created_at
            FROM resumes r
            JOIN candidates c ON c.id = r.candidate_id
            ORDER BY r.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_summary_counts():
    result: dict[str, int] = {}
    with get_connection(DEFAULT_DB_PATH) as conn:
        for table in ["vacancies", "candidates", "resumes", "skills", "scores"]:
            result[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return result


def render_index(
    request: Request,
    message: str | None = None,
    error: str | None = None,
    score_results: list[dict[str, Any]] | None = None,
):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "summary": get_summary_counts(),
            "vacancies": list_vacancies(),
            "resumes": list_resumes(),
            "message": message,
            "error": error,
            "score_results": score_results or [],
        },
    )


@app.get("/", response_class=HTMLResponse)
def web_index(request: Request, message: str | None = Query(default=None)):
    return render_index(request, message=message)


@app.post("/ui/vacancies")
def web_create_vacancy(
    title: str = Form(...),
    description: str = Form(...),
    min_years_experience: float | None = Form(default=None),
    required_skills: str = Form(default=""),
    optional_skills: str = Form(default=""),
):
    payload = {
        "title": title,
        "description": description,
        "min_years_experience": min_years_experience,
        "required_skills": parse_skill_lines(required_skills, default_weight=2.0),
        "optional_skills": parse_skill_lines(optional_skills, default_weight=1.0),
    }
    tmp_path = BASE_DIR / "data" / "vacancies" / "vacancy_from_ui.json"
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    vacancy_id = import_vacancy_json(tmp_path)
    return RedirectResponse(f"/?message=Вакансия {vacancy_id} сохранена", status_code=303)


@app.post("/ui/resumes/manual")
def web_create_resume_manual(full_name: str = Form(...), resume_text: str = Form(...)):
    response = create_resume_from_text(full_name=full_name, resume_text=resume_text)
    return RedirectResponse(f"/?message=Резюме {response['resume_id']} сохранено", status_code=303)


@app.post("/ui/resumes/upload")
async def web_upload_resume(file: UploadFile = File(...)):
    response = await upload_resume(file=file)
    return RedirectResponse(f"/?message=Резюме {response['resume_id']} загружено", status_code=303)


@app.post("/ui/score", response_class=HTMLResponse)
def web_score_vacancy(
    request: Request,
    vacancy_id: int = Form(...),
    limit: int | None = Form(default=10),
):
    try:
        results = score_all_resumes_for_vacancy(
            vacancy_id=vacancy_id,
            db_path=DEFAULT_DB_PATH,
            limit=limit,
        )
    except (ValueError, RuntimeError) as exc:
        return render_index(request, error=str(exc))

    return render_index(
        request,
        message=f"Скоринг вакансии {vacancy_id} выполнен",
        score_results=results,
    )


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
