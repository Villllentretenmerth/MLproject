from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .database import DEFAULT_DB_PATH, get_connection, init_db
from .importers import import_vacancy_json
from .text_utils import clean_text

app = FastAPI(title='Candidate Scoring MVP - API')
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
init_db(DEFAULT_DB_PATH)

@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/vacancies')
def create_vacancy(payload: dict[str, Any]):
    tmp_path = UPLOAD_DIR / 'vacancy_from_api.json'
    import json
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    vacancy_id = import_vacancy_json(tmp_path)
    return {'vacancy_id': vacancy_id, 'message': 'Vacancy saved'}


@app.post('/resumes/upload')
async def upload_resume(file: UploadFile = File(...)):
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in {'.txt', '.pdf'}:
        raise HTTPException(status_code=400, detail='Поддерживаются только TXT и PDF')

    data = await file.read()
    target = UPLOAD_DIR / (file.filename or 'resume.txt')
    target.write_bytes(data)

    from .importers import import_resume_file
    resume_id = import_resume_file(target)
    return {'resume_id': resume_id, 'filename': target.name, 'message': 'Resume saved'}


@app.post('/resumes/manual')
def create_resume_from_text(full_name: str = Form(...), resume_text: str = Form(...)):
    text = clean_text(resume_text)
    with get_connection(DEFAULT_DB_PATH) as conn:
        cur = conn.execute('INSERT INTO candidates(full_name) VALUES (?)', (full_name,))
        candidate_id = int(cur.lastrowid)
        cur = conn.execute(
            'INSERT INTO resumes(candidate_id, source_type, source_name, raw_text, cleaned_text) VALUES (?, ?, ?, ?, ?)',
            (candidate_id, 'MANUAL', f'{full_name}.txt', resume_text, text),
        )
        resume_id = int(cur.lastrowid)
        conn.commit()
    return {'resume_id': resume_id, 'message': 'Manual resume saved'}


@app.get('/db/summary')
def db_summary() -> dict[str, int]:
    result: dict[str, int] = {}
    with get_connection(DEFAULT_DB_PATH) as conn:
        for table in ['vacancies', 'candidates', 'resumes', 'skills', 'vacancy_skill_requirements']:
            result[table] = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    return result
