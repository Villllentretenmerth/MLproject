from __future__ import annotations

import json
import re
from pathlib import Path

from .database import get_connection, init_db, DEFAULT_DB_PATH
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
    conn.execute(
        'INSERT OR IGNORE INTO skills(name, category) VALUES (?, ?)',
        (skill_name, category),
    )
    row = conn.execute('SELECT id FROM skills WHERE name = ?', (skill_name,)).fetchone()
    return int(row['id'])


def load_taxonomy(db_path: str | Path = DEFAULT_DB_PATH, taxonomy_path: str | Path = DEFAULT_TAXONOMY_PATH):
    with open(taxonomy_path, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)

    with get_connection(db_path) as conn:
        for skill_name, aliases in taxonomy.get('synonyms', {}).items():
            skill_id = ensure_skill(conn, skill_name)
            for alias in aliases:
                conn.execute(
                    'INSERT OR IGNORE INTO skill_aliases(skill_id, alias) VALUES (?, ?)',
                    (skill_id, alias.lower().strip()),
                )
        conn.commit()


def import_vacancy_json(path: str | Path, db_path: str | Path = DEFAULT_DB_PATH):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))

    title = payload['title']
    description = payload.get('raw_text') or title
    required_skills = payload.get('required_skills', [])
    optional_skills = payload.get('optional_skills', [])

    with get_connection(db_path) as conn:
        cur = conn.execute(
            'INSERT INTO vacancies(title, description) VALUES (?, ?)',
            (title, description),
        )
        vacancy_id = int(cur.lastrowid)

        for skill_name in required_skills:
            skill_id = ensure_skill(conn, skill_name)
            conn.execute(
                '''
                INSERT OR REPLACE INTO vacancy_skill_requirements
                (vacancy_id, skill_id, is_required, weight)
                VALUES (?, ?, ?, ?)
                ''',
                (vacancy_id, skill_id, 1, 1.0),
            )

        for skill_name in optional_skills:
            skill_id = ensure_skill(conn, skill_name)
            conn.execute(
                '''
                INSERT OR REPLACE INTO vacancy_skill_requirements
                (vacancy_id, skill_id, is_required, weight)
                VALUES (?, ?, ?, ?)
                ''',
                (vacancy_id, skill_id, 0, 1.0),
            )

        conn.commit()

    return vacancy_id


def import_all_vacancies(vacancies_dir: str | Path = DEFAULT_VACANCIES_DIR, db_path: str | Path = DEFAULT_DB_PATH):
    total = 0
    for path in sorted(Path(vacancies_dir).glob('*.json')):
        if path.name == 'index.json':
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