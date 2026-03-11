import sqlite3
import sys

def norm(s: str) -> str:
    return " ".join(s.strip().lower().split())

ROLES = ["Python Backend", "Data Analyst", "QA Engineer", "DevOps", "Project Manager", "UX/UI Designer"]

SKILLS = [
    # backend / infra
    ("Python", "tech"),
    ("FastAPI", "tech"),
    ("Django", "tech"),
    ("REST", "tech"),
    ("SQL", "tech"),
    ("PostgreSQL", "tech"),
    ("MySQL", "tech"),
    ("Redis", "tech"),
    ("Docker", "tech"),
    ("Kubernetes", "tech"),
    ("Linux", "tech"),
    ("CI/CD", "process"),
    ("GitLab CI", "tool"),
    ("RabbitMQ", "tech"),
    ("Kafka", "tech"),
    ("Git", "tool"),

    # data
    ("Excel", "tool"),
    ("Power BI", "tool"),
    ("Tableau", "tool"),
    ("Pandas", "tech"),
    ("NumPy", "tech"),
    ("Scikit-learn", "tech"),
    ("ETL", "process"),
    ("Airflow", "tool"),

    # QA
    ("Testing", "qa"),
    ("API testing", "qa"),
    ("PyTest", "qa"),
    ("Selenium", "qa"),
    ("Playwright", "qa"),

    # PM
    ("Agile", "process"),
    ("Jira", "tool"),
    ("Confluence", "tool"),
    ("коммуникация", "soft"),
    ("тайм-менеджмент", "soft"),
    ("управление рисками", "soft"),
    ("фасилитация", "soft"),
    ("продуктовое мышление", "soft"),

    # UX/UI
    ("Figma", "design"),
    ("UX Design", "design"),
    ("UI Design", "design"),
    ("Wireframing", "design"),
    ("Prototyping", "design"),
    ("User Research", "design"),
    ("Usability Testing", "design"),
    ("Design System", "design"),
    ("Accessibility", "design"),
    ("Information Architecture", "design"),
]

ALIASES = {
    "Python": ["python", "py"],
    "FastAPI": ["fastapi", "fast api"],
    "REST": ["rest api", "rest"],
    "PostgreSQL": ["postgres", "postgresql", "psql", "pgsql"],
    "Docker": ["docker", "контейнеризация", "containers"],
    "Kubernetes": ["k8s", "kubernetes"],
    "CI/CD": ["cicd", "ci cd", "pipeline", "пайплайн"],
    "GitLab CI": ["gitlabci", "gitlab ci"],
    "API testing": ["postman", "api tests", "тестирование api"],
    "Power BI": ["powerbi", "power bi"],
    "Scikit-learn": ["sklearn", "scikit learn", "scikit-learn"],
    "UX Design": ["ux", "ux design"],
    "UI Design": ["ui", "ui design"],
    "Wireframing": ["wireframes", "вайрфреймы"],
    "Prototyping": ["prototype", "prototypes", "прототипирование"],
    "User Research": ["ux research", "custdev", "кастдев", "исследования пользователей"],
    "Accessibility": ["a11y", "accessibility", "доступность"],
    "Information Architecture": ["ia", "информационная архитектура"],
    "Git": ["git"],
    "Jira": ["jira"],
    "Confluence": ["confluence"],
    "Figma": ["figma"],
}

ROLE_SKILLS = {
    "Python Backend": [
        ("Python", "must", 4),
        ("REST", "must", 3),
        ("SQL", "must", 3),
        ("PostgreSQL", "must", 3),
        ("Docker", "must", 2),
        ("Linux", "must", 2),
        ("FastAPI", "nice", 2),
        ("Django", "nice", 1),
        ("Redis", "nice", 1),
        ("CI/CD", "nice", 1),
        ("GitLab CI", "nice", 1),
        ("RabbitMQ", "nice", 1),
        ("Kafka", "nice", 1),
        ("Kubernetes", "nice", 1),
        ("Git", "nice", 1),
    ],
    "Data Analyst": [
        ("SQL", "must", 4),
        ("Excel", "must", 3),
        ("Power BI", "must", 3),
        ("Python", "must", 2),
        ("Pandas", "must", 2),
        ("Tableau", "nice", 1),
        ("ETL", "nice", 1),
        ("Airflow", "nice", 1),
        ("NumPy", "nice", 1),
        ("Scikit-learn", "nice", 1),
    ],
    "QA Engineer": [
        ("Testing", "must", 4),
        ("API testing", "must", 3),
        ("SQL", "must", 2),
        ("Git", "must", 2),
        ("PyTest", "nice", 1),
        ("Playwright", "nice", 1),
        ("Selenium", "nice", 1),
        ("CI/CD", "nice", 1),
        ("Linux", "nice", 1),
    ],
    "DevOps": [
        ("Linux", "must", 3),
        ("Docker", "must", 3),
        ("Kubernetes", "must", 3),
        ("CI/CD", "must", 3),
        ("GitLab CI", "must", 2),
        ("Git", "nice", 1),
        ("Prometheus", "nice", 1),  
        ("Grafana", "nice", 1),     
    ],
    "Project Manager": [
        ("Agile", "must", 3),
        ("Jira", "must", 3),
        ("коммуникация", "must", 3),
        ("тайм-менеджмент", "must", 2),
        ("Confluence", "nice", 1),
        ("управление рисками", "nice", 1),
        ("фасилитация", "nice", 1),
        ("продуктовое мышление", "nice", 1),
    ],
    "UX/UI Designer": [
        ("Figma", "must", 4),
        ("UX Design", "must", 3),
        ("UI Design", "must", 3),
        ("Wireframing", "must", 2),
        ("Prototyping", "must", 2),
        ("User Research", "nice", 1),
        ("Usability Testing", "nice", 1),
        ("Design System", "nice", 1),
        ("Accessibility", "nice", 1),
        ("Information Architecture", "nice", 1),
    ],
}


VACANCIES = [
    # Backend
    ("Python Backend", "Python Backend Developer (FastAPI)", "Platform", "Remote", "middle",
     "Разработка REST API на FastAPI, работа с Postgres, контейнеризация Docker. Плюсом Redis, CI/CD, очереди, k8s."),
    ("Python Backend", "Junior Python Backend Developer (Django)", "Core", "Remote", "junior",
     "Разработка на Django, работа с БД, API, базовые практики разработки."),

    # Data
    ("Data Analyst", "Data Analyst (SQL, BI)", "Analytics", "Berlin / Hybrid", "junior",
     "SQL-запросы, отчётность и дашборды в Power BI, работа с Excel. Плюсом ETL/Airflow/Tableau."),
    ("Data Analyst", "Junior Data Analyst (SQL + Excel)", "Analytics", "Remote", "junior",
     "Выгрузки, отчётность, SQL/Excel. Плюсом Power BI и базовый Python/pandas."),

    # QA
    ("QA Engineer", "QA Engineer (Manual + API)", "QA", "Remote", "middle",
     "Функциональное/регрессионное тестирование, API testing (Postman), SQL-проверки. Плюсом pytest/playwright, CI/CD."),

    # DevOps
    ("DevOps", "DevOps Engineer (CI/CD, Docker, Kubernetes)", "Infrastructure", "Remote", "middle",
     "Сборка и деплой, пайплайны, контейнеры, k8s окружения, мониторинг."),

    # PM
    ("Project Manager", "Project Manager (IT / Agile)", "Delivery", "Berlin / Hybrid", "middle",
     "Ведение проекта, планирование спринтов, управление ожиданиями, риски, коммуникации."),

    # UX
    ("UX/UI Designer", "UX/UI Designer (Figma)", "Product Design", "Remote", "middle",
     "Проектирование UX-flow, прототипирование, дизайн UI в Figma. Плюсом исследования и участие в дизайн-системе."),
]