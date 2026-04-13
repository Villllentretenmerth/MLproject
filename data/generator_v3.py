import json
import random
import uuid
from dataclasses import dataclass, asdict
from typing import List

random.seed(42)

NUM_RESUMES = 80
NUM_VACANCIES = 80

RESUMES_JSONL = "resumes.jsonl"
VACANCIES_JSONL = "vacancies.jsonl"
RESUMES_TXT = "resumes.txt"
VACANCIES_TXT = "vacancies.txt"

SKILL_GROUPS = {
    "python_backend": [
        "Python", "FastAPI", "Django", "Flask", "asyncio", "PostgreSQL",
        "Redis", "RabbitMQ", "Kafka", "Docker", "Kubernetes", "CI/CD",
        "Pytest", "AWS", "Azure", "MongoDB", "ClickHouse"
    ],
    "java_backend": [
        "Java", "Spring Boot", "Hibernate", "Kafka", "PostgreSQL",
        "Docker", "Kubernetes", "Microservices", "JUnit", "Redis"
    ],
    "data_analytics": [
        "Python", "SQL", "Pandas", "Power BI", "Tableau", "Excel",
        "Statistics", "Data Visualization", "ETL", "A/B testing"
    ],
    "qa": [
        "Python", "SQL", "Selenium", "Pytest", "Postman",
        "API testing", "Manual testing", "Test Design", "Jira"
    ],
    "management": [
        "Agile", "Scrum", "Kanban", "Jira", "Confluence",
        "Risk Management", "Budgeting", "Stakeholder Management",
        "Roadmap Planning", "Team Leadership"
    ],
    "devops_platform": [
        "Docker", "Kubernetes", "CI/CD", "Terraform",
        "AWS", "Azure", "Linux", "Monitoring", "Kafka", "PostgreSQL"
    ]
}

DOMAINS = [
    "fintech", "edtech", "ecommerce", "ml_platform", "enterprise", "b2b_saas"
]

EDUCATION_POOL = [
    "ИТМО, Программная инженерия",
    "МГТУ им. Баумана, Информатика и системы управления",
    "МФТИ, Прикладная математика и информатика",
    "НГУ, Механико-математический факультет",
    "НИУ МГСУ, Промышленное и гражданское строительство",
    "СПбГУ, Прикладная математика",
    "ВШЭ, Бизнес-информатика"
]

FIRST_NAMES = [
    "Алексей", "Мария", "Иван", "Елена", "Дмитрий", "Анна",
    "Павел", "Ольга", "Никита", "Светлана", "Максим", "Екатерина"
]

LAST_NAMES = [
    "Иванов", "Петров", "Сидорова", "Кузнецов", "Смирнова",
    "Попов", "Волкова", "Федоров", "Морозова", "Орлов"
]

COMPANIES = [
    "TechNova", "DataPulse", "CloudCore", "FinMatrix",
    "ScaleHub", "QuantumApps", "ProductWave", "NextLayer"
]

WORK_FORMATS = ["Удаленно", "Офис", "Гибрид"]
EMPLOYMENT_TYPES = ["Полная", "Контракт", "Полная"]
SENIORITY_LEVELS = ["Junior", "Middle", "Senior", "Lead"]

ROLE_TEMPLATES = {
    "python_backend": [
        "Python Developer", "Backend Python Developer",
        "Senior Python Developer", "Lead Python Developer"
    ],
    "java_backend": [
        "Java Developer", "Senior Java Developer", "Backend Java Engineer"
    ],
    "data_analytics": [
        "Data Analyst", "Junior Data Analyst", "Product Analyst"
    ],
    "qa": [
        "QA Engineer", "Junior QA Engineer", "Python QA Engineer"
    ],
    "management": [
        "IT Project Manager", "Delivery Manager", "Engineering Manager"
    ],
    "devops_platform": [
        "DevOps Engineer", "Platform Engineer", "Senior DevOps Engineer"
    ]
}

TASK_SNIPPETS = {
    "python_backend": [
        "Проектирование и разработка масштабируемых backend-сервисов",
        "Оптимизация производительности и рефакторинг legacy-модулей",
        "Разработка и поддержка API",
        "Code Review и внедрение инженерных практик",
        "Менторство middle-разработчиков"
    ],
    "java_backend": [
        "Разработка высоконагруженных микросервисов",
        "Оптимизация существующего Java-кода",
        "Интеграция через брокеры сообщений",
        "Проектирование сервисной архитектуры",
        "Покрытие кода тестами"
    ],
    "data_analytics": [
        "Подготовка аналитических отчетов",
        "Анализ продуктовых метрик",
        "Построение дашбордов",
        "Формирование гипотез и A/B тестов",
        "Сбор и очистка данных"
    ],
    "qa": [
        "Написание тест-кейсов",
        "Проверка API и интеграций",
        "Автоматизация тестирования",
        "Регресс и smoke testing",
        "Заведение дефектов и контроль фиксов"
    ],
    "management": [
        "Управление delivery команды",
        "Коммуникация со стейкхолдерами",
        "Управление рисками и сроками",
        "Планирование roadmap",
        "Координация нескольких команд"
    ],
    "devops_platform": [
        "Поддержка CI/CD пайплайнов",
        "Автоматизация инфраструктуры",
        "Работа с контейнерной платформой",
        "Наблюдаемость и мониторинг",
        "Повышение надежности систем"
    ]
}

PLUS_SNIPPETS = {
    "python_backend": [
        "Опыт работы с NoSQL",
        "Опыт работы с ClickHouse",
        "Open Source вклад",
        "Понимание frontend-части"
    ],
    "java_backend": [
        "Опыт миграции monolith to microservices",
        "Знание DDD",
        "Опыт performance tuning JVM"
    ],
    "data_analytics": [
        "Опыт работы в продуктовой аналитике",
        "Знание Python для анализа данных",
        "Опыт построения прогнозных моделей"
    ],
    "qa": [
        "Опыт нагрузочного тестирования",
        "Опыт CI интеграции тестов",
        "Базовое понимание backend-разработки"
    ],
    "management": [
        "Опыт в fintech",
        "Технический бэкграунд",
        "Управление распределенными командами"
    ],
    "devops_platform": [
        "Опыт работы с Kafka",
        "Опыт FinOps",
        "Опыт построения internal platform"
    ]
}


@dataclass
class Resume:
    resume_id: str
    full_name: str
    desired_position: str
    track: str
    seniority: str
    years_experience: int
    education: str
    domain: str
    skills: List[str]
    summary: str
    raw_text: str


@dataclass
class Vacancy:
    vacancy_id: str
    title: str
    track: str
    seniority: str
    min_years_experience: int
    company: str
    work_format: str
    employment_type: str
    domain: str
    required_skills: List[str]
    optional_skills: List[str]
    tasks: List[str]
    raw_text: str


def sample_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def sample_seniority(years: int) -> str:
    if years <= 1:
        return "Junior"
    if years <= 4:
        return "Middle"
    if years <= 8:
        return "Senior"
    return "Lead"


def pick_track() -> str:
    return random.choices(
        population=list(SKILL_GROUPS.keys()),
        weights=[25, 15, 12, 12, 10, 10],
        k=1
    )[0]


def choose_skills(track: str, min_k: int = 4, max_k: int = 8) -> List[str]:
    pool = SKILL_GROUPS[track][:]
    k = min(len(pool), random.randint(min_k, min(max_k, len(pool))))
    return random.sample(pool, k)


def build_resume_text(resume: Resume) -> str:
    return (
        f"{resume.desired_position} ({resume.seniority})\n"
        f"Желаемая должность: {resume.desired_position}\n"
        f"Образование: {resume.education}\n"
        f"Опыт работы: {resume.years_experience} лет.\n"
        f"Ключевые навыки: {', '.join(resume.skills)}.\n"
        f"Домен: {resume.domain}.\n"
        f"О себе: {resume.summary}"
    )


def build_vacancy_text(vacancy: Vacancy) -> str:
    return (
        f"Вакансия: {vacancy.title}\n"
        f"Компания: {vacancy.company}\n"
        f"Формат работы: {vacancy.work_format}\n"
        f"Занятость: {vacancy.employment_type}\n"
        f"Опыт работы: от {vacancy.min_years_experience} лет\n"
        f"Домен: {vacancy.domain}\n\n"
        f"Ваши задачи:\n" +
        "\n".join([f"— {task}" for task in vacancy.tasks]) + "\n\n"
        f"Наши ожидания:\n" +
        "\n".join([f"— {skill}" for skill in vacancy.required_skills]) + "\n\n"
        f"Будет плюсом:\n" +
        "\n".join([f"— {skill}" for skill in vacancy.optional_skills])
    )


def generate_resume() -> Resume:
    track = pick_track()

    if track in ["data_analytics", "qa"]:
        years = random.randint(0, 6)
    else:
        years = random.randint(1, 12)

    seniority = sample_seniority(years)
    desired_position = random.choice(ROLE_TEMPLATES[track])
    domain = random.choice(DOMAINS)
    skills = choose_skills(track, min_k=4, max_k=8)

    summary_pool = [
        "Сильный технический кругозор",
        "Внимателен к качеству решений",
        "Быстро погружаюсь в новую предметную область",
        "Ориентируюсь на бизнес-результат",
        "Люблю работать в команде",
        "Ответственно подхожу к срокам и качеству"
    ]

    summary = ". ".join(random.sample(summary_pool, k=3)) + "."

    resume = Resume(
        resume_id=str(uuid.uuid4()),
        full_name=sample_name(),
        desired_position=desired_position,
        track=track,
        seniority=seniority,
        years_experience=years,
        education=random.choice(EDUCATION_POOL),
        domain=domain,
        skills=skills,
        summary=summary,
        raw_text=""
    )
    resume.raw_text = build_resume_text(resume)
    return resume


def generate_vacancy() -> Vacancy:
    track = pick_track()
    seniority = random.choices(
        SENIORITY_LEVELS, weights=[20, 35, 35, 10], k=1
    )[0]

    if seniority == "Junior":
        min_exp = 0
    elif seniority == "Middle":
        min_exp = random.randint(2, 4)
    elif seniority == "Senior":
        min_exp = random.randint(5, 8)
    else:
        min_exp = random.randint(7, 12)

    required_skills = choose_skills(track, min_k=4, max_k=7)
    optional_skills = random.sample(
        PLUS_SNIPPETS[track],
        k=min(len(PLUS_SNIPPETS[track]), random.randint(1, 3))
    )
    tasks = random.sample(TASK_SNIPPETS[track], k=4)

    title = random.choice(ROLE_TEMPLATES[track])
    if seniority not in title:
        title = f"{seniority} {title}"

    vacancy = Vacancy(
        vacancy_id=str(uuid.uuid4()),
        title=title,
        track=track,
        seniority=seniority,
        min_years_experience=min_exp,
        company=random.choice(COMPANIES),
        work_format=random.choice(WORK_FORMATS),
        employment_type=random.choice(EMPLOYMENT_TYPES),
        domain=random.choice(DOMAINS),
        required_skills=required_skills,
        optional_skills=optional_skills,
        tasks=tasks,
        raw_text=""
    )
    vacancy.raw_text = build_vacancy_text(vacancy)
    return vacancy


def save_jsonl(rows, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")


def save_resumes_txt(rows, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for idx, row in enumerate(rows, start=1):
            f.write("=" * 70 + "\n")
            f.write(f"RESUME #{idx}\n")
            f.write(f"resume_id: {row.resume_id}\n")
            f.write(f"candidate: {row.full_name}\n\n")
            f.write(row.raw_text.strip() + "\n")
            f.write("\n")


def save_vacancies_txt(rows, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for idx, row in enumerate(rows, start=1):
            f.write("=" * 70 + "\n")
            f.write(f"VACANCY #{idx}\n")
            f.write(f"vacancy_id: {row.vacancy_id}\n\n")
            f.write(row.raw_text.strip() + "\n")
            f.write("\n")


#мэин
resumes = [generate_resume() for _ in range(NUM_RESUMES)]
vacancies = [generate_vacancy() for _ in range(NUM_VACANCIES)]

save_jsonl(resumes, RESUMES_JSONL)
save_jsonl(vacancies, VACANCIES_JSONL)
save_resumes_txt(resumes, RESUMES_TXT)
save_vacancies_txt(vacancies, VACANCIES_TXT)

print(f"Generated resumes: {len(resumes)}")
print(f"Generated vacancies: {len(vacancies)}")
print(f"Saved: {RESUMES_JSONL}, {VACANCIES_JSONL}, {RESUMES_TXT}, {VACANCIES_TXT}")


