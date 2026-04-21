from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .database import DEFAULT_DB_PATH, get_connection
from .text_utils import clean_text

TOKEN_BOUNDARY = r"(?<!\w){token}(?!\w)"


@dataclass
class VacancyRequirement:
    skill_id: int
    skill_name: str
    is_required: bool
    weight: float
    min_years: float | None
    aliases: list[str]


@dataclass
class ScoreResult:
    score: float
    keyword_score: float
    semantic_score: float
    required_coverage: float
    optional_coverage: float
    matched_required: int
    total_required: int
    matched_optional: int
    total_optional: int
    required_weight_matched: float
    required_weight_total: float
    optional_weight_matched: float
    optional_weight_total: float
    experience_years: float | None
    required_experience_years: float | None
    experience_shortfall_years: float
    experience_penalty: float
    found_skills: list[dict[str, Any]]
    missing_required_skills: list[str]
    backend: str
    language: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def norm(text: str):
    return clean_text(text or "").casefold().replace("ё", "е")


def detect_language(text: str):
    sample = text[:3000]
    cyr = len(re.findall(r"[а-яА-ЯёЁ]", sample))
    lat = len(re.findall(r"[a-zA-Z]", sample))
    return "ru" if cyr >= lat else "en"


def alias_pattern(alias: str):
    normalized = re.escape(alias.casefold().replace("ё", "е"))
    return re.compile(
        TOKEN_BOUNDARY.format(token=normalized),
        flags=re.IGNORECASE | re.UNICODE,
    )


def find_alias_mentions(text: str, aliases: list[str]):
    normalized_text = norm(text)
    evidences: list[dict[str, Any]] = []

    for alias in sorted(set(a.strip() for a in aliases if a and a.strip()), key=len, reverse=True):
        pattern = alias_pattern(alias)
        for match in pattern.finditer(normalized_text):
            start, end = match.span()
            left = max(0, start - 40)
            right = min(len(normalized_text), end + 40)
            evidences.append(
                {
                    "alias": alias,
                    "start": start,
                    "end": end,
                    "snippet": normalized_text[left:right].strip(),
                }
            )

    dedup: dict[tuple[str, int, int], dict[str, Any]] = {}
    for item in evidences:
        dedup[(item["alias"], item["start"], item["end"])] = item
    return sorted(dedup.values(), key=lambda x: (x["start"], x["end"]))


@lru_cache(maxsize=4)
def load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


@lru_cache(maxsize=4)
def load_hf_encoder(model_name: str):
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    return tokenizer, model


def hf_similarity(
    vacancy_text: str,
    resume_text: str,
    language: str,
    model_name: str | None = None,
):
    vacancy_text = clean_text(vacancy_text or "").strip()
    resume_text = clean_text(resume_text or "").strip()
    if not vacancy_text or not resume_text:
        return 0.0, "hf:empty"

    if language == "ru":
        choosen_model = model_name or "ai-forever/sbert_large_nlu_ru"
        model = load_sentence_transformer(choosen_model)
        embeddings = model.encode(
            [vacancy_text, resume_text],
            normalize_embeddings=True,
        )
        score = sum(float(a * b) for a, b in zip(embeddings[0], embeddings[1]))
        return max(0.0, min(1.0, score)), f"hf:{choosen_model}"

    choosen_model = model_name or "FacebookAI/xlm-roberta-base"

    import torch
    import torch.nn.functional as F

    tokenizer, model = load_hf_encoder(choosen_model)
    batch = tokenizer(
        [vacancy_text, resume_text],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = model(**batch)

    token_embeddings = outputs.last_hidden_state
    attention = batch["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
    summed = (token_embeddings * attention).sum(dim=1)
    counts = attention.sum(dim=1).clamp(min=1e-9)
    sentence_embeddings = F.normalize(summed / counts, p=2, dim=1)

    score = float(torch.matmul(sentence_embeddings[0], sentence_embeddings[1]).item())
    return max(0.0, min(1.0, score)), f"hf:{choosen_model}"


def semantic_similarity(
    vacancy_text: str,
    resume_text: str,
    backend: str = "auto",
    language: str | None = None,
    model_name: str | None = None,):
    language = language or detect_language(f"{vacancy_text}\n{resume_text}")
    selected_backend = "hf" if backend == "auto" else backend

    if selected_backend == "hf":
        return hf_similarity(
            vacancy_text=vacancy_text,
            resume_text=resume_text,
            language=language,
            model_name=model_name,
        )

    raise ValueError(f"Unsupported semantic backend: {backend}")


def extract_experience_years(text: str) -> float | None:
    normalized = clean_text(text or "")
    patterns = [
        r"опыт\s+работы\s*[:\-]?\s*(\d+(?:[\.,]\d+)?)\s*(?:лет|года|год)",
        r"experience\s*[:\-]?\s*(\d+(?:[\.,]\d+)?)\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE | re.UNICODE)
        if not match:
            continue
        value = match.group(1).replace(",", ".")
        try:
            years = float(value)
        except ValueError:
            continue
        return max(0.0, years)
    return None


def resolve_required_experience_years(
    requirements: list[VacancyRequirement],
    vacancy_min_years: float | None = None,
) -> float | None:
    values: list[float] = []
    if vacancy_min_years is not None:
        values.append(float(vacancy_min_years))
    values.extend(float(req.min_years) for req in requirements if req.min_years is not None)
    return max(values) if values else None


def calculate_experience_penalty(
    experience_years: float | None,
    required_experience_years: float | None,
) -> tuple[float, float]:
    if required_experience_years is None or experience_years is None:
        return 1.0, 0.0

    shortfall = max(0.0, required_experience_years - experience_years)
    if shortfall <= 0:
        return 1.0, 0.0

    penalty = max(0.45, 1.0 - 0.12 * shortfall)
    return penalty, shortfall


def get_vacancy_payload(
    vacancy_id: int,
    db_path: str | Path = DEFAULT_DB_PATH,):
    with get_connection(db_path) as conn:
        vacancy = conn.execute(
            """
            SELECT id, title, description, raw_text, min_years_experience
            FROM vacancies
            WHERE id = ?
            """,
            (vacancy_id,),
        ).fetchone()
        if vacancy is None:
            raise ValueError(f"Vacancy {vacancy_id} not found")

        rows = conn.execute(
            """
            SELECT
                vsr.skill_id,
                s.name AS skill_name,
                vsr.is_required,
                vsr.weight,
                vsr.min_years,
                GROUP_CONCAT(sa.alias, '||') AS aliases
            FROM vacancy_skill_requirements vsr
            JOIN skills s ON s.id = vsr.skill_id
            LEFT JOIN skill_aliases sa ON sa.skill_id = s.id
            WHERE vsr.vacancy_id = ?
            GROUP BY vsr.skill_id, s.name, vsr.is_required, vsr.weight, vsr.min_years
            ORDER BY vsr.is_required DESC, vsr.weight DESC, s.name ASC
            """,
            (vacancy_id,),
        ).fetchall()

    requirements: list[VacancyRequirement] = []
    for row in rows:
        aliases = [a.strip() for a in (row["aliases"] or "").split("||") if a and a.strip()]
        if row["skill_name"] not in aliases:
            aliases.append(row["skill_name"])

        requirements.append(
            VacancyRequirement(
                skill_id=int(row["skill_id"]),
                skill_name=str(row["skill_name"]),
                is_required=bool(row["is_required"]),
                weight=float(row["weight"]),
                min_years=float(row["min_years"]) if row["min_years"] is not None else None,
                aliases=sorted(set(aliases), key=len, reverse=True),
            )
        )

    return {
        "id": int(vacancy["id"]),
        "title": vacancy["title"],
        "description": vacancy["description"],
        "raw_text": vacancy["raw_text"],
        "requirements": requirements,
        "min_years_experience": float(vacancy["min_years_experience"]) if vacancy["min_years_experience"] is not None else None,
    }


def get_resume_payload(
    resume_id: int,
    db_path: str | Path = DEFAULT_DB_PATH,):
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                r.id AS resume_id,
                r.cleaned_text,
                r.raw_text,
                r.source_name,
                c.full_name
            FROM resumes r
            JOIN candidates c ON c.id = r.candidate_id
            WHERE r.id = ?
            """,
            (resume_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"Resume {resume_id} not found")

    full_name = row["full_name"]
    raw_text = row["raw_text"] or ""

    if str(full_name).casefold().startswith("resume_id:"):
        for line in raw_text.splitlines():
            line = line.strip()
            if line.casefold().startswith("candidate:"):
                full_name = line.split(":", 1)[1].strip() or full_name
                break

    return {
        "resume_id": int(row["resume_id"]),
        "full_name": full_name,
        "source_name": row["source_name"],
        "text": row["cleaned_text"] or row["raw_text"] or "",
    }


def calculate_score(
    resume_text: str,
    vacancy_text: str,
    requirements: list[VacancyRequirement],
    backend: str = "auto",
    language: str | None = None,
    model_name: str | None = None,
    vacancy_min_years: float | None = None,
):
    resume_text = clean_text(resume_text or "")
    vacancy_text = clean_text(vacancy_text or "")
    language = language or detect_language(f"{vacancy_text}\n{resume_text}")

    required_items = [r for r in requirements if r.is_required]
    optional_items = [r for r in requirements if not r.is_required]

    experience_years = extract_experience_years(resume_text)
    required_experience_years = resolve_required_experience_years(
        requirements=requirements,
        vacancy_min_years=vacancy_min_years,
    )

    required_weight_total = sum(max(r.weight, 0.0) for r in required_items)
    optional_weight_total = sum(max(r.weight, 0.0) for r in optional_items)

    required_weight_matched = 0.0
    optional_weight_matched = 0.0
    matched_required = 0
    matched_optional = 0
    found_skills: list[dict[str, Any]] = []
    missing_required_skills: list[str] = []

    for req in requirements:
        evidences = find_alias_mentions(resume_text, req.aliases)
        matched = bool(evidences)

        if matched:
            payload = {
                "skill_id": req.skill_id,
                "skill": req.skill_name,
                "is_required": req.is_required,
                "weight": req.weight,
                "occurrences": len(evidences),
                "proofs": [item["alias"] for item in evidences[:5]],
                "snippets": [item["snippet"] for item in evidences[:3]],
            }
            found_skills.append(payload)

            if req.is_required:
                required_weight_matched += req.weight
                matched_required += 1
            else:
                optional_weight_matched += req.weight
                matched_optional += 1
        elif req.is_required:
            missing_required_skills.append(req.skill_name)

    total_weight = required_weight_total + optional_weight_total
    matched_weight = required_weight_matched + optional_weight_matched
    keyword_score = (matched_weight / total_weight) if total_weight > 0 else 0.0

    required_coverage = (
        required_weight_matched / required_weight_total if required_weight_total > 0 else 1.0
    )
    optional_coverage = (
        optional_weight_matched / optional_weight_total if optional_weight_total > 0 else 0.0
    )

    semantic_score, backend_used = semantic_similarity(
        vacancy_text=vacancy_text,
        resume_text=resume_text,
        backend=backend,
        language=language,
        model_name=model_name,
    )

    missing_penalty = 1.0
    if required_items:
        missing_ratio = len(missing_required_skills) / len(required_items)
        missing_penalty = max(0.5, 1.0 - 0.35 * missing_ratio)

    experience_penalty, experience_shortfall_years = calculate_experience_penalty(
        experience_years=experience_years,
        required_experience_years=required_experience_years,
    )

    final_score = (
        100.0
        * (0.65 * keyword_score + 0.35 * semantic_score)
        * missing_penalty
        * experience_penalty
    )
    final_score = round(max(0.0, min(100.0, final_score)), 2)

    return ScoreResult(
        score=final_score,
        keyword_score=round(keyword_score, 4),
        semantic_score=round(semantic_score, 4),
        required_coverage=round(required_coverage, 4),
        optional_coverage=round(optional_coverage, 4),
        matched_required=matched_required,
        total_required=len(required_items),
        matched_optional=matched_optional,
        total_optional=len(optional_items),
        required_weight_matched=round(required_weight_matched, 4),
        required_weight_total=round(required_weight_total, 4),
        optional_weight_matched=round(optional_weight_matched, 4),
        optional_weight_total=round(optional_weight_total, 4),
        experience_years=round(experience_years, 2) if experience_years is not None else None,
        required_experience_years=round(required_experience_years, 2) if required_experience_years is not None else None,
        experience_shortfall_years=round(experience_shortfall_years, 2),
        experience_penalty=round(experience_penalty, 4),
        found_skills=sorted(found_skills, key=lambda x: (-float(x["weight"]), x["skill"])),
        missing_required_skills=missing_required_skills,
        backend=backend_used,
        language=language,
    )


def save_score(
    vacancy_id: int,
    resume_id: int,
    result: ScoreResult,
    db_path: str | Path = DEFAULT_DB_PATH,):
    explanation = {
        "backend": result.backend,
        "language": result.language,
        "experience_years": result.experience_years,
        "required_experience_years": result.required_experience_years,
        "experience_shortfall_years": result.experience_shortfall_years,
        "experience_penalty": result.experience_penalty,
        "found_skills": [
            {
                "skill": item["skill"],
                "is_required": item["is_required"],
                "weight": item["weight"],
                "occurrences": item["occurrences"],
                "proofs": item["proofs"],
                "snippets": item["snippets"],
            }
            for item in result.found_skills
        ],
        "missing_required_skills": result.missing_required_skills,
    }

    with get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM scores WHERE vacancy_id = ? AND resume_id = ?",
            (vacancy_id, resume_id),
        ).fetchone()

        if existing is None:
            cur = conn.execute(
                """
                INSERT INTO scores(
                    vacancy_id,
                    resume_id,
                    score,
                    keyword_score,
                    semantic_score,
                    matched_required,
                    matched_optional,
                    required_weight_matched,
                    required_weight_total,
                    optional_weight_matched,
                    optional_weight_total,
                    explanation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vacancy_id,
                    resume_id,
                    result.score,
                    result.keyword_score,
                    result.semantic_score,
                    result.matched_required,
                    result.matched_optional,
                    result.required_weight_matched,
                    result.required_weight_total,
                    result.optional_weight_matched,
                    result.optional_weight_total,
                    json.dumps(explanation, ensure_ascii=False),
                ),
            )
            score_id = int(cur.lastrowid)
        else:
            score_id = int(existing["id"])
            conn.execute(
                """
                UPDATE scores
                SET
                    score = ?,
                    keyword_score = ?,
                    semantic_score = ?,
                    matched_required = ?,
                    matched_optional = ?,
                    required_weight_matched = ?,
                    required_weight_total = ?,
                    optional_weight_matched = ?,
                    optional_weight_total = ?,
                    explanation = ?,
                    created_at = datetime('now')
                WHERE id = ?
                """,
                (
                    result.score,
                    result.keyword_score,
                    result.semantic_score,
                    result.matched_required,
                    result.matched_optional,
                    result.required_weight_matched,
                    result.required_weight_total,
                    result.optional_weight_matched,
                    result.optional_weight_total,
                    json.dumps(explanation, ensure_ascii=False),
                    score_id,
                ),
            )
            conn.execute("DELETE FROM score_skill_matches WHERE score_id = ?", (score_id,))

        for item in result.found_skills:
            conn.execute(
                """
                INSERT OR REPLACE INTO score_skill_matches(score_id, skill_id, match_type, proof)
                VALUES (?, ?, ?, ?)
                """,
                (
                    score_id,
                    int(item["skill_id"]),
                    "required" if item["is_required"] else "optional",
                    ", ".join(item["proofs"][:3]),
                ),
            )

        conn.commit()

    return score_id


def score_resume_against_vacancy(
    vacancy_id: int,
    resume_id: int,
    db_path: str | Path = DEFAULT_DB_PATH,
    backend: str = "auto",
    model_name: str | None = None,):
    vacancy = get_vacancy_payload(vacancy_id, db_path=db_path)
    resume = get_resume_payload(resume_id, db_path=db_path)

    result = calculate_score(
        resume_text=resume["text"],
        vacancy_text=vacancy["raw_text"] or vacancy["description"],
        requirements=vacancy["requirements"],
        backend=backend,
        model_name=model_name,
        vacancy_min_years=vacancy.get("min_years_experience"),
    )

    score_id = save_score(vacancy_id, resume_id, result, db_path=db_path)

    return {
        "score_id": score_id,
        "vacancy_id": vacancy_id,
        "vacancy_title": vacancy["title"],
        "resume_id": resume_id,
        "candidate_name": resume["full_name"],
        **result.to_dict(),
    }


def score_all_resumes_for_vacancy(
    vacancy_id: int,
    db_path: str | Path = DEFAULT_DB_PATH,
    backend: str = "auto",
    model_name: str | None = None,
    limit: int | None = None,):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT id FROM resumes ORDER BY id").fetchall()

    results = [
        score_resume_against_vacancy(
            vacancy_id=vacancy_id,
            resume_id=int(row["id"]),
            db_path=db_path,
            backend=backend,
            model_name=model_name,
        )
        for row in rows
    ]

    results.sort(key=lambda x: (-float(x["score"]), x["candidate_name"]))
    return results[:limit] if limit is not None else results