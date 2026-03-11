import json
import os
import random

random.seed(42)

N_RESUMES = 72

BASE_DIR = "data"
VAC_DIR = os.path.join(BASE_DIR, "vacancies")
RES_JSON_DIR = os.path.join(BASE_DIR, "resumes", "json")
RES_TXT_DIR = os.path.join(BASE_DIR, "resumes", "txt")

for d in [VAC_DIR, RES_JSON_DIR, RES_TXT_DIR]:
    os.makedirs(d, exist_ok=True)

TAXONOMY = {
    "global_skills": {
        "soft": ["коммуникация", "командная работа", "ответственность", "самостоятельность", "тайм-менеджмент", "критическое мышление"],
        "tools": ["Git", "Jira", "Confluence", "Notion", "Miro", "Slack"],
        "langs": ["English A2", "English B1", "English B2"]
    },
    "synonyms": {
        "Python": ["python", "py"],
        "FastAPI": ["fastapi", "Fast Api"],
        "Django": ["django"],
        "REST": ["rest", "REST API", "rest api"],
        "SQL": ["sql", "SQL-запросы", "T-SQL"],
        "PostgreSQL": ["Postgres", "postgres", "PSQL", "pgsql"],
        "MySQL": ["mysql"],
        "Redis": ["redis"],
        "Docker": ["docker", "контейнеризация", "containers"],
        "Kubernetes": ["k8s", "kubernetes"],
        "Linux": ["linux", "ubuntu", "debian"],
        "CI/CD": ["ci/cd", "cicd", "пайплайн", "pipeline"],
        "GitLab CI": ["gitlab ci", "GitlabCI"],
        "RabbitMQ": ["rabbitmq", "очереди сообщений", "message queue"],
        "Kafka": ["kafka"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "Scikit-learn": ["sklearn", "scikit learn", "scikit-learn"],
        "Power BI": ["powerbi", "PowerBI"],
        "Tableau": ["tableau"],
        "Excel": ["ms excel", "excel"],
        "ETL": ["etl", "ELT", "data pipeline"],
        "Airflow": ["airflow", "Apache Airflow"],
        "Testing": ["тестирование", "qa", "quality assurance"],
        "API testing": ["postman", "api testing", "тестирование api"],
        "PyTest": ["pytest", "py.test"],
        "Selenium": ["selenium", "seleniun"],
        "Playwright": ["playwright"],
        "Agile": ["agile", "scrum", "kanban"],
        "Figma": ["figma"],
        "User Research": ["ux research", "исследования пользователей", "custdev", "кастдев"],
        "Wireframing": ["вайрфреймы", "wireframes"],
        "Prototyping": ["прототипирование", "prototype", "prototypes"],
        "Design System": ["дизайн-система", "design system"],
        "UI Design": ["ui", "ui design", "интерфейсы"],
        "UX Design": ["ux", "ux design", "пользовательские сценарии"],
        "Usability Testing": ["usability", "юзабилити тестирование", "usability testing"],
        "Accessibility": ["a11y", "accessibility", "доступность"],
        "Information Architecture": ["ia", "информационная архитектура"],
        "Git": ["git", "Git"]
    },
    "roles": {
        "Python Backend": {
            "must_have": ["Python", "REST", "SQL", "PostgreSQL", "Docker", "Linux"],
            "nice_to_have": ["FastAPI", "Django", "Redis", "CI/CD", "GitLab CI", "RabbitMQ", "Kafka", "Kubernetes"]
        },
        "Data Analyst": {
            "must_have": ["SQL", "Excel", "Power BI", "Python", "Pandas"],
            "nice_to_have": ["Tableau", "ETL", "Airflow", "NumPy", "Scikit-learn"]
        },
        "QA Engineer": {
            "must_have": ["Testing", "API testing", "SQL", "Git"],
            "nice_to_have": ["PyTest", "Selenium", "Playwright", "CI/CD", "Linux"]
        },
        "DevOps": {
            "must_have": ["Linux", "Docker", "CI/CD", "GitLab CI", "Kubernetes"],
            "nice_to_have": ["Terraform", "Ansible", "Prometheus", "Grafana", "Helm"]
        },
        "Project Manager": {
            "must_have": ["Agile", "Jira", "коммуникация", "тайм-менеджмент"],
            "nice_to_have": ["Confluence", "управление рисками", "фасилитация", "продуктовое мышление", "stakeholder management"]
        },
        "UX/UI Designer": {
            "must_have": ["Figma", "UX Design", "UI Design", "Wireframing", "Prototyping"],
            "nice_to_have": ["User Research", "Usability Testing", "Design System", "Accessibility", "Information Architecture"]
        }
    }
}

VACANCIES = [
    {
        "id": "vac_101",
        "title": "Python Backend Developer (FastAPI)",
        "department": "Platform",
        "location": "Remote",
        "level": "middle",
        "must_have": [{"skill": "Python", "weight": 4}, {"skill": "FastAPI", "weight": 3}, {"skill": "REST", "weight": 3},
                      {"skill": "SQL", "weight": 3}, {"skill": "PostgreSQL", "weight": 3}, {"skill": "Docker", "weight": 2}, {"skill": "Linux", "weight": 2}],
        "nice_to_have": [{"skill": "Redis", "weight": 1}, {"skill": "CI/CD", "weight": 1}, {"skill": "RabbitMQ", "weight": 1}, {"skill": "Kubernetes", "weight": 1}],
        "description_text": "Разработка REST API на FastAPI, работа с Postgres, контейнеризация docker. Плюсом Redis, CI/CD, очереди сообщений, k8s."
    },
    {
        "id": "vac_102",
        "title": "Junior Python Backend Developer (Django)",
        "department": "Core",
        "location": "Remote",
        "level": "junior",
        "must_have": [{"skill": "Python", "weight": 4}, {"skill": "Django", "weight": 3}, {"skill": "SQL", "weight": 3}, {"skill": "PostgreSQL", "weight": 2}],
        "nice_to_have": [{"skill": "Docker", "weight": 1}, {"skill": "REST", "weight": 1}, {"skill": "CI/CD", "weight": 1}],
        "description_text": "Разработка серверной части на Django, работа с БД, API, базовые практики dev."
    },
    {
        "id": "vac_201",
        "title": "Data Analyst (SQL, BI)",
        "department": "Analytics",
        "location": "Berlin / Hybrid",
        "level": "junior",
        "must_have": [{"skill": "SQL", "weight": 4}, {"skill": "Excel", "weight": 3}, {"skill": "Power BI", "weight": 3},
                      {"skill": "Python", "weight": 2}, {"skill": "Pandas", "weight": 2}],
        "nice_to_have": [{"skill": "ETL", "weight": 1}, {"skill": "Airflow", "weight": 1}, {"skill": "Tableau", "weight": 1}],
        "description_text": "SQL-запросы, отчётность и дашборды в Power BI, работа с Excel. Плюсом ETL/Airflow/Tableau."
    },
    {
        "id": "vac_202",
        "title": "Junior Data Analyst (SQL + Excel)",
        "department": "Analytics",
        "location": "Remote",
        "level": "junior",
        "must_have": [{"skill": "SQL", "weight": 4}, {"skill": "Excel", "weight": 4}],
        "nice_to_have": [{"skill": "Power BI", "weight": 2}, {"skill": "Python", "weight": 1}, {"skill": "Pandas", "weight": 1}],
        "description_text": "Выгрузки, отчётность, SQL/Excel. Плюсом Power BI и базовый Python/pandas."
    },
    {
        "id": "vac_301",
        "title": "QA Engineer (Manual + API)",
        "department": "QA",
        "location": "Remote",
        "level": "middle",
        "must_have": [{"skill": "Testing", "weight": 4}, {"skill": "API testing", "weight": 3}, {"skill": "SQL", "weight": 2}, {"skill": "Git", "weight": 2}],
        "nice_to_have": [{"skill": "PyTest", "weight": 1}, {"skill": "Playwright", "weight": 1}, {"skill": "CI/CD", "weight": 1}, {"skill": "Linux", "weight": 1}],
        "description_text": "Функциональное/регрессионное тестирование, API testing (Postman), SQL-проверки. Плюсом pytest/playwright и CI/CD."
    },
    {
        "id": "vac_501",
        "title": "DevOps Engineer (CI/CD, Docker, Kubernetes)",
        "department": "Infrastructure",
        "location": "Remote",
        "level": "middle",
        "must_have": [{"skill": "Linux", "weight": 3}, {"skill": "Docker", "weight": 3}, {"skill": "CI/CD", "weight": 3},
                      {"skill": "GitLab CI", "weight": 2}, {"skill": "Kubernetes", "weight": 3}],
        "nice_to_have": [{"skill": "Prometheus", "weight": 1}, {"skill": "Grafana", "weight": 1}, {"skill": "Terraform", "weight": 1}],
        "description_text": "Сборка и деплой, пайплайны, контейнеры, k8s окружения, мониторинг."
    },
    {
        "id": "vac_601",
        "title": "Project Manager (IT / Agile)",
        "department": "Delivery",
        "location": "Berlin / Hybrid",
        "level": "middle",
        "must_have": [{"skill": "Agile", "weight": 3}, {"skill": "Jira", "weight": 3}, {"skill": "коммуникация", "weight": 3}, {"skill": "тайм-менеджмент", "weight": 2}],
        "nice_to_have": [{"skill": "Confluence", "weight": 1}, {"skill": "управление рисками", "weight": 1}, {"skill": "фасилитация", "weight": 1}],
        "description_text": "Ведение проекта, планирование спринтов, управление ожиданиями, риски, коммуникации."
    },
    {
        "id": "vac_701",
        "title": "UX/UI Designer (Figma)",
        "department": "Product Design",
        "location": "Remote",
        "level": "middle",
        "must_have": [{"skill": "Figma", "weight": 4}, {"skill": "UX Design", "weight": 3}, {"skill": "UI Design", "weight": 3},
                      {"skill": "Wireframing", "weight": 2}, {"skill": "Prototyping", "weight": 2}],
        "nice_to_have": [{"skill": "User Research", "weight": 1}, {"skill": "Usability Testing", "weight": 1}, {"skill": "Design System", "weight": 1}, {"skill": "Accessibility", "weight": 1}],
        "description_text": "Проектирование UX-flow, прототипирование, дизайн UI в Figma. Плюсом исследования и участие в дизайн-системе."
    }
]

FIRST_NAMES = ["Артём", "Мария", "Никита", "Елена", "Дмитрий", "Анна", "Игорь", "Ольга", "Сергей", "Ирина"]
LAST_NAMES = ["Иванов", "Петрова", "Сидоров", "Кузнецова", "Смирнов", "Попова", "Волков", "Соколова", "Морозов", "Новикова"]
CITIES = ["Berlin", "Potsdam", "Munich", "Hamburg", "Leipzig"]
LEVELS = ["junior", "middle", "senior"]

def pick_synonym(skill: str) -> str:
    syns = TAXONOMY["synonyms"].get(skill, [])
    variants = [skill] + syns
    return random.choice(variants)

def sample_skills(role: str, quality: str):
    must = TAXONOMY["roles"][role]["must_have"]
    nice = TAXONOMY["roles"][role]["nice_to_have"]

    if quality == "strong":
        must_k = max(1, int(0.85 * len(must)))
        nice_k = max(0, int(0.45 * len(nice)))
    elif quality == "medium":
        must_k = max(1, int(0.60 * len(must)))
        nice_k = max(0, int(0.20 * len(nice)))
    elif quality == "weak":
        must_k = max(1, int(0.30 * len(must)))
        nice_k = max(0, int(0.10 * len(nice)))
    else:  # mismatch
        must_k = 0
        nice_k = 0

    skills = set(random.sample(must, k=must_k)) if must_k > 0 else set()
    if nice_k > 0:
        skills.update(random.sample(nice, k=min(nice_k, len(nice))))

    # noise from other roles
    other_roles = [r for r in TAXONOMY["roles"].keys() if r != role]
    noise_pool = []
    for r in other_roles:
        noise_pool += TAXONOMY["roles"][r]["must_have"] + TAXONOMY["roles"][r]["nice_to_have"]
    noise_pool = list(dict.fromkeys(noise_pool))

    noise_n = {"strong": 2, "medium": 3, "weak": 5, "mismatch": 9}[quality]
    if noise_pool:
        skills.update(random.sample(noise_pool, k=min(noise_n, len(noise_pool))))

    return sorted(skills)

def make_projects(role, skills):
    base = {
        "Python Backend": [
            ("REST сервис", "CRUD API, авторизация, интеграции", ["Python", "REST", "SQL", "PostgreSQL"]),
            ("Сервис уведомлений", "очереди, ретраи, фоновые задачи", ["Python", "RabbitMQ", "Docker", "Linux"])
        ],
        "Data Analyst": [
            ("Дашборды продаж", "Power BI отчёты, витрины данных", ["SQL", "Power BI", "Excel"]),
            ("Аналитика поведения", "сегментации, отчётность, выгрузки", ["Python", "Pandas", "SQL"])
        ],
        "QA Engineer": [
            ("Регресс веб-сервиса", "чек-листы, тест-кейсы, баг-репорты", ["Testing", "API testing", "SQL"]),
            ("Автотесты (база)", "smoke e2e, отчётность", ["PyTest", "Playwright", "CI/CD"])
        ],
        "DevOps": [
            ("CI/CD для сервиса", "пайплайны сборки и деплой", ["CI/CD", "GitLab CI", "Docker"]),
            ("Kubernetes окружение", "деплой, конфиги, сервисы", ["Kubernetes", "Linux", "Docker"])
        ],
        "Project Manager": [
            ("Ведение проекта", "спринты, риски, коммуникация", ["Agile", "Jira", "коммуникация"]),
            ("Процессы команды", "фасилитация и улучшение потока задач", ["тайм-менеджмент", "Confluence"])
        ],
        "UX/UI Designer": [
            ("Редизайн личного кабинета", "пользовательские сценарии, прототипы, UI", ["Figma", "UX Design", "UI Design", "Wireframing", "Prototyping"]),
            ("Дизайн-система", "компоненты, гайдлайны, доступность", ["Design System", "Accessibility", "Figma"])
        ]
    }

    candidates = base.get(role, [])
    selected = random.sample(candidates, k=min(2, len(candidates))) if candidates else []
    projects = []
    for name, summary, stack in selected:
        stack2 = list(dict.fromkeys([s for s in stack if s in skills] + stack))[:7]
        projects.append({"name": name, "summary": summary, "stack": stack2})
    return projects

def make_resume_text(fio, city, email, phone, target_role, level, skills, projects, exp_years):
    skills_text = ", ".join(pick_synonym(s) for s in skills)

    bullets = [
        "Участие в командной разработке, оценка задач, взаимодействие со стейкхолдерами.",
        "Поддержка качества: ревью, документация, улучшения процессов.",
        "Работа с требованиями, приоритизация, поиск и устранение проблем."
    ]
    random.shuffle(bullets)

    proj_lines = []
    for i, p in enumerate(projects, 1):
        stack_text = ", ".join(pick_synonym(s) for s in p["stack"])
        proj_lines.append(f"{i}) {p['name']} — {p['summary']}\nСтек: {stack_text}")

    return (
        f"{fio}, {city}\n"
        f"Email: {email} | Тел.: {phone}\n"
        f"Цель: {target_role} ({level})\n\n"
        f"Навыки:\n- {skills_text}\n\n"
        f"Опыт:\n2022–2026 {target_role} — CompanyX\n- {bullets[0]}\n- {bullets[1]}\n\n"
        f"Проекты:\n" + "\n\n".join(proj_lines) + "\n\n"
        f"Стаж: {exp_years} лет\n"
    )

def save_taxonomy_and_vacancies():
    with open(os.path.join(BASE_DIR, "skills_taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(TAXONOMY, f, ensure_ascii=False, indent=2)

    for v in VACANCIES:
        with open(os.path.join(VAC_DIR, f"{v['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(v, f, ensure_ascii=False, indent=2)

def make_resumes(n=N_RESUMES):
    roles = list(TAXONOMY["roles"].keys())

    # распределение “качества” для тестирования скоринга
    qualities = (["strong"] * int(0.28 * n)) + (["medium"] * int(0.33 * n)) + (["weak"] * int(0.25 * n))
    while len(qualities) < n:
        qualities.append("mismatch")
    qualities = qualities[:n]
    random.shuffle(qualities)

    for i in range(1, n + 1):
        quality = qualities[i - 1]

        fio = f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)}"
        city = random.choice(CITIES)
        email = f"user{i:03d}@example.com"
        phone = f"+49 151 {i:07d}"

        target_role = random.choice(roles)

        if quality == "mismatch":
            skill_source_role = random.choice([r for r in roles if r != target_role])
            skills = sample_skills(skill_source_role, "strong")
        else:
            skills = sample_skills(target_role, quality)

        level = random.choices(LEVELS, weights=[4, 4, 2])[0]
        exp_years = {"junior": random.randint(0, 1), "middle": random.randint(2, 4), "senior": random.randint(5, 9)}[level]

        projects = make_projects(target_role, skills)
        resume_text = make_resume_text(fio, city, email, phone, target_role, level, skills, projects, exp_years)

        resume = {
            "id": f"res_{i:03d}",
            "fio": fio,
            "city": city,
            "email": email,
            "phone": phone,
            "target_role": target_role,
            "level": level,
            "experience_years": exp_years,
            "quality_label": quality,
            "expected_score_range": {"strong": [80, 100], "medium": [55, 80], "weak": [20, 55], "mismatch": [0, 20]}[quality],
            "skills": skills,
            "projects": projects,
            "education": [{"place": "Университет", "program": "Информатика", "year": random.randint(2016, 2025)}],
            "certificates": random.sample(
                ["курс Python", "курс SQL", "курс Docker", "курс Power BI", "курс QA", "курс DevOps", "курс Figma", "курс PM"],
                k=random.randint(0, 3)
            ),
            "text": resume_text
        }

        with open(os.path.join(RES_JSON_DIR, f"{resume['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(resume, f, ensure_ascii=False, indent=2)
        with open(os.path.join(RES_TXT_DIR, f"{resume['id']}.txt"), "w", encoding="utf-8") as f:
            f.write(resume_text)

if __name__ == "__main__":
    save_taxonomy_and_vacancies()
    make_resumes(N_RESUMES)
    print(f"Готово! Сгенерировано: {N_RESUMES} резюме + taxonomy + {len(VACANCIES)} вакансий в папке data/.")