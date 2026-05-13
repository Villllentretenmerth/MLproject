from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / 'db' / 'hr.db'
SCHEMA_PATH = BASE_DIR / 'db' / 'schema.sql'


def get_connection(db_path: str | Path = DEFAULT_DB_PATH):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH, schema_path: str | Path = SCHEMA_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = Path(schema_path).read_text(encoding='utf-8')
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def execute_many(conn: sqlite3.Connection, sql: str, rows: Iterable[tuple]):
    conn.executemany(sql, rows)
    conn.commit()
