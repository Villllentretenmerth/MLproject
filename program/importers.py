from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .database import DEFAULT_DB_PATH, get_connection, init_db
from .text_utils import clean_text, extract_text, infer_candidate_name

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_VACANCIES_DIR = BASE_DIR / 'data' / 'vacancies'
DEFAULT_RESUMES_DIR = BASE_DIR / 'data' / 'resumes'
DEFAULT_TAXONOMY_PATH = BASE_DIR / 'data' / 'skills_taxonomy.json'
DEFAULT_JSONL_PATH = BASE_DIR / 'data' / 'synthetic_resume_job_dataset.jsonl'


def slugify(value: str):
    value = value.lower().strip()
    value = re.sub(r'[^a-zа-я0-9]+', '_', value, flags=re.IGNORECASE)
    return value.strip('_')


def ensure_skill(conn, skill_name: str, category: str | None = None):
    normalized = clean_text(skill_name)
    conn.execute(
        'INSERT OR IGNORE INTO skills(name, category) VALUES (?, ?)',
        (normalized, category),
    )
    if category:
        conn.execute('UPDATE skills SET category = COALESCE(category, ?) WHERE name = ?', (category, normalized))
    row = conn.execute('SELECT id FROM skills WHERE name = ?', (normalized,)).fetchone()
    return int(row['id'])


def _normalize_alias(alias: str):
    return clean_text(alias).lower()


def load_taxonomy(db_path: str | Path = DEFAULT_DB_PATH, taxonomy_path: str | Path = DEFAULT_TAXONOMY_PATH):
    with open(taxonomy_path, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)

    with get_connection(db_path) as conn:
        for skill_name in taxonomy.get('global_skills', []):
            ensure_skill(conn, skill_name)

        for skill_name, aliases in taxonomy.get('synonyms', {}).items():
            skill_id = ensure_skill(conn, skill_name)
            conn.execute(
                'INSERT OR IGNORE INTO skill_aliases(skill_id, alias) VALUES (?, ?)',
                (skill_id, _normalize_alias(skill_name)),
            )
            for alias in aliases:
                conn.execute(
                    'INSERT OR IGNORE INTO skill_aliases(skill_id, alias) VALUES (?, ?)',
                    (skill_id, _normalize_alias(alias)),
                )
        conn.commit()


def _infer_role(payload: dict[str, Any]):
    for key in ('role', 'track', 'title'):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_description(payload: dict[str, Any]):
    parts: list[str] = []
    for field in ('description', 'description_text', 'raw_text'):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
            break
    tasks = payload.get('tasks') or []
    if isinstance(tasks, list) and tasks:
        parts.append('Задачи: ' + '; '.join(str(item).strip() for item in tasks if str(item).strip()))
    return '\n'.join(parts).strip() or str(payload.get('title', '')).strip()


def _skill_items(payload: dict[str, Any], field_name: str, default_required: bool):
    items = payload.get(field_name) or []
    normalized: list[dict[str, Any]] = []
    default_weight = 2.0 if default_required else 1.0

    for item in items:
        if isinstance(item, str):
            skill = item.strip()
            if not skill:
                continue
            normalized.append({'skill': skill, 'weight': default_weight, 'is_required': default_required, 'min_years': None})
            continue

        if isinstance(item, dict):
            skill = str(item.get('skill') or item.get('name') or '').strip()
            if not skill:
                continue
            normalized.append(
                {
                    'skill': skill,
                    'weight': float(item.get('weight', default_weight)),
                    'is_required': bool(item.get('is_required', default_required)),
                    'min_years': item.get('min_years'),
                }
            )
    return normalized


def import_vacancy_json(path: str | Path, db_path: str | Path = DEFAULT_DB_PATH):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    title = str(payload['title']).strip()
    description = _extract_description(payload)
    role = _infer_role(payload)

    required_items = _skill_items(payload, 'required_skills', True) + _skill_items(payload, 'must_have', True)
    optional_items = _skill_items(payload, 'optional_skills', False) + _skill_items(payload, 'nice_to_have', False)

    external_id = payload.get('vacancy_id')
    if external_id is not None:
        external_id = str(external_id)

    with get_connection(db_path) as conn:
        existing = None
        if external_id:
            existing = conn.execute('SELECT id FROM vacancies WHERE external_id = ?', (external_id,)).fetchone()

        if existing:
            vacancy_id = int(existing['id'])
            conn.execute(
                '''
                UPDATE vacancies
                SET title = ?, role = ?, track = ?, seniority = ?, company = ?, work_format = ?,
                    employment_type = ?, domain = ?, min_years_experience = ?, raw_text = ?, description = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                ''',
                (
                    title,
                    role,
                    payload.get('track'),
                    payload.get('seniority'),
                    payload.get('company'),
                    payload.get('work_format'),
                    payload.get('employment_type'),
                    payload.get('domain'),
                    payload.get('min_years_experience'),
                    payload.get('raw_text'),
                    description,
                    vacancy_id,
                ),
            )
            conn.execute('DELETE FROM vacancy_skill_requirements WHERE vacancy_id = ?', (vacancy_id,))
        else:
            cur = conn.execute(
                '''
                INSERT INTO vacancies(
                    external_id, title, role, track, seniority, company, work_format, employment_type,
                    domain, min_years_experience, raw_text, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    external_id,
                    title,
                    role,
                    payload.get('track'),
                    payload.get('seniority'),
                    payload.get('company'),
                    payload.get('work_format'),
                    payload.get('employment_type'),
                    payload.get('domain'),
                    payload.get('min_years_experience'),
                    payload.get('raw_text'),
                    description,
                ),
            )
            vacancy_id = int(cur.lastrowid)

        for item in required_items + optional_items:
            skill_id = ensure_skill(conn, item['skill'])
            conn.execute(
                '''
                INSERT OR REPLACE INTO vacancy_skill_requirements(vacancy_id, skill_id, is_required, weight, min_years)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    vacancy_id,
                    skill_id,
                    1 if item['is_required'] else 0,
                    float(item.get('weight', 1.0)),
                    item.get('min_years'),
                ),
            )

        conn.commit()
    return vacancy_id


def import_all_vacancies(vacancies_dir: str | Path = DEFAULT_VACANCIES_DIR, db_path: str | Path = DEFAULT_DB_PATH):
    total = 0
    for path in sorted(Path(vacancies_dir).glob('*.json')):
        if path.name == 'index.json':
            continue
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(payload, dict) or 'title' not in payload:
            continue
        import_vacancy_json(path, db_path=db_path)
        total += 1
    return total


def import_resume_file(path: str | Path, db_path: str | Path = DEFAULT_DB_PATH, source_type: str | None = None):
    text, detected_type = extract_text(path)
    cleaned = clean_text(text)
    path = Path(path)
    fallback_name = path.stem.replace('_', ' ').strip()
    full_name = infer_candidate_name(cleaned, fallback_name)

    with get_connection(db_path) as conn:
        cur = conn.execute('INSERT INTO candidates(full_name) VALUES (?)', (full_name,))
        candidate_id = int(cur.lastrowid)
        cur = conn.execute(
            'INSERT INTO resumes(candidate_id, source_type, source_name, raw_text, cleaned_text) VALUES (?, ?, ?, ?, ?)',
            (candidate_id, source_type or detected_type, path.name, text, cleaned),
        )
        resume_id = int(cur.lastrowid)
        conn.commit()
    return resume_id


def import_all_resumes(resumes_dir: str | Path = DEFAULT_RESUMES_DIR, db_path: str | Path = DEFAULT_DB_PATH):
    total = 0
    for path in sorted(Path(resumes_dir).iterdir()):
        if path.is_file() and path.suffix.lower() in {'.txt', '.pdf'}:
            import_resume_file(path, db_path=db_path)
            total += 1
    return total


def bootstrap_project(db_path: str | Path = DEFAULT_DB_PATH):
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()

    init_db(db_path=db_path)
    load_taxonomy(db_path=db_path)
    vacancies_loaded = import_all_vacancies(db_path=db_path)
    resumes_loaded = import_all_resumes(db_path=db_path)
    return {
        'vacancies_loaded': vacancies_loaded,
        'resumes_loaded': resumes_loaded,
    }