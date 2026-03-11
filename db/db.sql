PRAGMA foreign_keys = ON;

-- Вакансии
CREATE TABLE IF NOT EXISTS vacancies (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  title           TEXT NOT NULL,
  description     TEXT NOT NULL,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT
);

-- Кандидаты
CREATE TABLE IF NOT EXISTS candidates (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name       TEXT NOT NULL,
  email           TEXT,
  phone           TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Резюме
CREATE TABLE IF NOT EXISTS resumes (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id    INTEGER NOT NULL,
  source_type     TEXT NOT NULL CHECK (source_type IN ('TXT','PDF','MANUAL','SYNTH')),
  source_name     TEXT,
  raw_text        TEXT NOT NULL,
  cleaned_text    TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_resumes_candidate ON resumes(candidate_id);

-- Навыки
CREATE TABLE IF NOT EXISTS skills (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  name            TEXT NOT NULL UNIQUE,
  category        TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Синонимы навыков
CREATE TABLE IF NOT EXISTS skill_aliases (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  skill_id        INTEGER NOT NULL,
  alias           TEXT NOT NULL,
  UNIQUE(skill_id, alias),
  FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_skill_aliases_alias ON skill_aliases(alias);

-- Требования вакансии: skill + обязательность + вес
CREATE TABLE IF NOT EXISTS vacancy_skill_requirements (
  vacancy_id      INTEGER NOT NULL,
  skill_id        INTEGER NOT NULL,
  is_required     INTEGER NOT NULL DEFAULT 1 CHECK (is_required IN (0,1)),
  weight          REAL NOT NULL DEFAULT 1.0,
  min_years       REAL,
  PRIMARY KEY (vacancy_id, skill_id),
  FOREIGN KEY(vacancy_id) REFERENCES vacancies(id) ON DELETE CASCADE,
  FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_vsr_vacancy ON vacancy_skill_requirements(vacancy_id);

-- Навыки, найденные в резюме
CREATE TABLE IF NOT EXISTS resume_skills (
  resume_id       INTEGER NOT NULL,
  skill_id        INTEGER NOT NULL,
  occurrences     INTEGER NOT NULL DEFAULT 1,
  confidence      REAL,
  PRIMARY KEY (resume_id, skill_id),
  FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
  FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Запуск скоринга (мета)
CREATE TABLE IF NOT EXISTS scoring_runs (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  algorithm       TEXT NOT NULL,       -- keywords, tfidf_cosine
  algorithm_ver   TEXT NOT NULL,       -- 0.1, 0.2...
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Параметры запуска (ключ-значение)
CREATE TABLE IF NOT EXISTS scoring_run_params (
  scoring_run_id  INTEGER NOT NULL,
  param_key       TEXT NOT NULL,
  param_value     TEXT NOT NULL,
  PRIMARY KEY (scoring_run_id, param_key),
  FOREIGN KEY(scoring_run_id) REFERENCES scoring_runs(id) ON DELETE CASCADE
);

-- Итоговый score
CREATE TABLE IF NOT EXISTS scores (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  scoring_run_id  INTEGER NOT NULL,
  vacancy_id      INTEGER NOT NULL,
  resume_id       INTEGER NOT NULL,
  score           REAL NOT NULL CHECK (score >= 0 AND score <= 100),
  matched_required INTEGER NOT NULL DEFAULT 0,
  matched_optional INTEGER NOT NULL DEFAULT 0,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(scoring_run_id, vacancy_id, resume_id),
  FOREIGN KEY(scoring_run_id) REFERENCES scoring_runs(id) ON DELETE CASCADE,
  FOREIGN KEY(vacancy_id) REFERENCES vacancies(id) ON DELETE CASCADE,
  FOREIGN KEY(resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_scores_vacancy ON scores(vacancy_id);
CREATE INDEX IF NOT EXISTS idx_scores_score ON scores(score DESC);

-- Объяснимость: какие навыки совпали и откуда
CREATE TABLE IF NOT EXISTS score_skill_matches (
  score_id        INTEGER NOT NULL,
  skill_id        INTEGER NOT NULL,
  match_type      TEXT NOT NULL CHECK (match_type IN ('required','optional')),
  evidence        TEXT,                -- фрагмент/слово-алиас/примечание 
  PRIMARY KEY (score_id, skill_id),
  FOREIGN KEY(score_id) REFERENCES scores(id) ON DELETE CASCADE,
  FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_score_matches_score ON score_skill_matches(score_id);