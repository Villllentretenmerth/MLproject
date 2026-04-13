from __future__ import annotations

import re
from pathlib import Path


def clean_text(text: str):
    text = text.replace('\x00', ' ')
    text = text.replace('\r', '\n')
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_text_from_txt(path: str | Path):
    return Path(path).read_text(encoding='utf-8', errors='ignore')


def extract_text_from_pdf(path: str | Path):
    try:
        from pypdf import PdfReader
    except Exception as exc:  
        raise RuntimeError('установите pypdf') from exc

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or '')
    return '\n'.join(parts).strip()


def extract_text(path: str | Path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == '.txt':
        return extract_text_from_txt(path), 'TXT'
    if suffix == '.pdf':
        return extract_text_from_pdf(path), 'PDF'
    raise ValueError(f'Неподдерживаемый формат: {suffix}')


def infer_candidate_name(text: str, fallback_name: str):
    first_line = clean_text(text).split('\n')[0].strip()
    if 2 <= len(first_line) <= 120:
        return first_line
    return fallback_name
