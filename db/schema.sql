PRAGMA foreign_keys = ON;

-- Вакансии
CREATE TABLE IF NOT EXISTS vacancies (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  external_id           TEXT UNIQUE,
  title                 TEXT NOT NULL,
  role                  TEXT,
  track                 TEXT,
  seniority             TEXT,
  company               TEXT,
  work_format           TEXT,
  employment_type       TEXT,
  domain                TEXT,
  min_years_experience  REAL,
  raw_text              TEXT,
  description           TEXT NOT NULL,
  created_at            TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at            TEXT
);
CREATE INDEX IF NOT EXISTS idx_vacancies_role ON vacancies(role);
CREATE INDEX IF NOT EXISTS idx_vacancies_track ON vacancies(track);
CREATE INDEX IF NOT EXISTS idx_vacancies_seniority ON vacancies(seniority);

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
  source_type     TEXT NOT NULL CHECK (source_type IN ('TXT','PDF','MANUAL')),
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
CREATE INDEX IF NOT EXISTS idx_resume_skills_resume ON resume_skills(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_skills_skill ON resume_skills(skill_id);

-- Итоговый score
CREATE TABLE IF NOT EXISTS scores (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  vacancy_id              INTEGER NOT NULL,
  resume_id               INTEGER NOT NULL,
  score                   REAL NOT NULL CHECK (score >= 0 AND score <= 100),
  keyword_score           REAL,
  semantic_score          REAL,
  matched_required        INTEGER NOT NULL DEFAULT 0,
  matched_optional        INTEGER NOT NULL DEFAULT 0,
  required_weight_matched REAL NOT NULL DEFAULT 0,
  required_weight_total   REAL NOT NULL DEFAULT 0,
  optional_weight_matched REAL NOT NULL DEFAULT 0,
  optional_weight_total   REAL NOT NULL DEFAULT 0,
  explanation             TEXT,
  created_at              TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(vacancy_id, resume_id),
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
  proof           TEXT,
  PRIMARY KEY (score_id, skill_id),
  FOREIGN KEY(score_id) REFERENCES scores(id) ON DELETE CASCADE,
  FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_score_matches_score ON score_skill_matches(score_id);