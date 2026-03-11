import json
import random
import uuid
from pathlib import Path

OUTPUT_JSONL = "synthetic_resume_job_dataset.jsonl"
OUTPUT_JSON = "synthetic_resume_job_dataset.json"

NUM_VACANCIES = 5   #тут ставить сколько вакансий будет сгенерировано

#здесь ставить кол-во кандидатов на каждую вакансию
CANDIDATE_DISTRIBUTION = (
    ["strong"] * 2 +
    ["good"] * 4 +
    ["borderline"] * 5 +
    ["weak"] * 5 +
    ["mismatch"] * 4
)

#инглиш левел
ENGLISH_LEVELS = {"A2": 1, "B1": 2, "B2": 3, "C1": 4}

#опыт
SENIORITY_LEVELS = {
    "Junior": 1,
    "Junior-Middle": 2,
    "Middle": 3,
    "Senior": 4,
    "Lead": 5
}

#сюда позже надо будет грузить роли из базы данных, но пока что так будет
ROLE_LIBRARY = {
    "Data Engineer": {
        "core_skills": ["Python", "SQL", "Airflow"],
        "optional_skills": ["Spark", "Docker", "Kafka", "dbt"],
        "related_titles": ["Data Engineer", "ETL Developer", "Analytics Engineer"],
        "domains": ["Fintech", "E-commerce", "SaaS", "Healthcare"]
    },
    "Frontend Developer": {
        "core_skills": ["JavaScript", "TypeScript", "React"],
        "optional_skills": ["Next.js", "Redux", "Jest", "Cypress"],
        "related_titles": ["Frontend Developer", "Frontend Engineer", "UI Engineer"],
        "domains": ["E-commerce", "Media", "SaaS", "EdTech"]
    },
    "Backend Developer": {
        "core_skills": ["Python", "SQL", "REST"],
        "optional_skills": ["Docker", "PostgreSQL", "Redis", "FastAPI"],
        "related_titles": ["Backend Developer", "Backend Engineer", "Software Engineer"],
        "domains": ["Fintech", "SaaS", "Logistics", "Healthcare"]
    },
    "Data Analyst": {
        "core_skills": ["SQL", "Excel", "Tableau"],
        "optional_skills": ["Python", "Power BI", "Pandas", "Looker"],
        "related_titles": ["Data Analyst", "BI Analyst", "Product Analyst"],
        "domains": ["Fintech", "Retail", "SaaS", "Telecom"]
    }
}

#шум
NOISE_SKILLS = [
    "Git", "Linux", "Jira", "Agile", "REST", "NoSQL",
    "Pandas", "CI/CD", "Scrum", "API", "Testing"
]

UNRELATED_SKILLS = [
    "Photoshop", "Figma", "Recruiting", "Salesforce",
    "Copywriting", "SEO", "Customer Support"
]

UNRELATED_TITLES = [
    "Support Specialist", "Designer", "Sales Manager",
    "Marketing Specialist", "Recruiter"
]

#тексты вакансий
TEXT_VARIANTS_VACANCY = [
    "We are looking for a {seniority} {role} to join our {domain} team. "
    "Required skills: {required_skills}. Nice to have: {optional_skills}. "
    "You should have at least {min_experience_years} years of experience. "
    "English level: {english_level}. Work format: {location_mode}.",

    "As a {role}, you will work on projects in the {domain} domain. "
    "Must-have: {required_skills}. Preferred: {optional_skills}. "
    "Required experience: {min_experience_years}+ years. "
    "Expected seniority: {seniority}. English: {english_level}.",

    "Hiring: {role} ({seniority}). "
    "Core stack includes {required_skills}. Additional advantage: {optional_skills}. "
    "Minimum commercial experience: {min_experience_years} years. "
    "Mode: {location_mode}. Domain: {domain}. English: {english_level}."
]

#тексты резюме
TEXT_VARIANTS_RESUME = [
    "{current_title} with {experience_years} years of experience. "
    "Worked in domains: {domains}. Skills: {skills}. "
    "Seniority: {seniority}. English: {english_level}. Preferred work format: {location_mode}.",

    "Professional Summary: {current_title} experienced in {skills}. "
    "Total experience: {experience_years} years. "
    "Worked mostly in {domains}. English level: {english_level}.",

    "{current_title}. "
    "Hands-on background with {skills}. "
    "Commercial experience: {experience_years} years. "
    "Seniority level: {seniority}. Domain exposure: {domains}."
]




def random_choice(seq):
    return random.choice(seq)

def fit_level(value_map, candidate_value, required_value):
    gap = value_map[candidate_value] - value_map[required_value]
    if gap >= 0:
        return 1.0
    if gap == -1:
        return 0.7
    if gap == -2:
        return 0.4
    return 0.0

def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


#генерация

def generate_vacancy(role_name: str) -> dict:
    tpl = ROLE_LIBRARY[role_name]

    seniority = random_choice(["Junior", "Junior-Middle", "Middle", "Senior"])
    min_experience_years = random.randint(1, 6)

    required_skills = tpl["core_skills"][:]
    optional_count = random.randint(1, min(3, len(tpl["optional_skills"])))
    optional_skills = random.sample(tpl["optional_skills"], k=optional_count)

    vacancy = {
        "role": role_name,
        "seniority": seniority,
        "required_skills": required_skills,
        "optional_skills": optional_skills,
        "min_experience_years": min_experience_years,
        "english_level": random_choice(["B1", "B2", "C1"]),
        "domain": random_choice(tpl["domains"]),
        "location_mode": random_choice(["Remote", "Hybrid", "Onsite"])
    }
    return vacancy


def generate_resume_for_vacancy(vacancy: dict, candidate_type: str) -> dict:
    role_name = vacancy["role"]
    tpl = ROLE_LIBRARY[role_name]

    req = vacancy["required_skills"]
    opt = vacancy["optional_skills"]

    if candidate_type == "strong":
        matched_req = req[:] if random.random() < 0.8 else random.sample(req, k=max(1, len(req) - 1))
        matched_opt = random.sample(opt, k=random.randint(1, len(opt))) if opt else []
        exp = random.randint(vacancy["min_experience_years"], vacancy["min_experience_years"] + 4)
        seniority = random_choice(
            [vacancy["seniority"], "Senior", "Lead"] if vacancy["seniority"] != "Lead" else ["Lead"]
        )
        english = vacancy["english_level"]
        title = random_choice(tpl["related_titles"])
        domains = [vacancy["domain"]]

    elif candidate_type == "good":
        matched_req = random.sample(req, k=max(1, len(req) - 1))
        matched_opt = random.sample(opt, k=random.randint(0, len(opt))) if opt else []
        exp = max(1, random.randint(vacancy["min_experience_years"] - 1, vacancy["min_experience_years"] + 2))
        seniority = vacancy["seniority"] if random.random() < 0.6 else "Junior-Middle"
        english = random_choice([vacancy["english_level"], "B1"])
        title = random_choice(tpl["related_titles"])
        domains = [random_choice(tpl["domains"])]

    elif candidate_type == "borderline":
        matched_req = random.sample(req, k=max(1, len(req) // 2))
        matched_opt = random.sample(opt, k=1) if opt and random.random() < 0.5 else []
        exp = max(0, vacancy["min_experience_years"] - random.randint(1, 2))
        seniority = "Junior-Middle" if vacancy["seniority"] in ["Middle", "Senior"] else "Junior"
        english = "B1"
        title = random_choice(tpl["related_titles"])
        domains = [random_choice(tpl["domains"])]

    elif candidate_type == "weak":
        pool = list(set(req + opt))
        matched_req = random.sample(pool, k=min(max(1, len(pool) // 3), 2))
        matched_opt = []
        exp = max(0, vacancy["min_experience_years"] - random.randint(2, 4))
        seniority = "Junior"
        english = random_choice(["A2", "B1"])
        title = "Software Developer"
        domains = [random_choice(["Retail", "Gaming", "Education", "Marketing"])]

    elif candidate_type == "mismatch":
        matched_req = random.sample(UNRELATED_SKILLS, k=2)
        matched_opt = []
        exp = random.randint(0, 3)
        seniority = "Junior"
        english = random_choice(["A2", "B1"])
        title = random_choice(UNRELATED_TITLES)
        domains = [random_choice(["Retail", "Marketing", "Education", "Hospitality"])]

    else:
        raise ValueError(f"Unknown candidate_type: {candidate_type}")

    noise = random.sample(NOISE_SKILLS, k=random.randint(1, 3))
    skills = list(set(matched_req + matched_opt + noise))

    resume = {
        "current_title": title,
        "seniority": seniority,
        "skills": skills,
        "experience_years": exp,
        "english_level": english,
        "domains": domains,
        "location_mode": random_choice(["Remote", "Hybrid", "Onsite"])
    }
    return resume


#скоринг

def score_pair(vacancy: dict, resume: dict) -> dict:
    req = set(vacancy["required_skills"])
    opt = set(vacancy["optional_skills"])
    skills = set(resume["skills"])

    matched_required = len(req & skills)
    matched_optional = len(opt & skills)

    required_skill_match = matched_required / max(1, len(req))
    optional_skill_match = matched_optional / max(1, len(opt))
    experience_fit = min(resume["experience_years"] / max(1, vacancy["min_experience_years"]), 1.0)
    seniority_fit = fit_level(SENIORITY_LEVELS, resume["seniority"], vacancy["seniority"])
    english_fit = fit_level(ENGLISH_LEVELS, resume["english_level"], vacancy["english_level"])
    domain_fit = 1.0 if vacancy["domain"] in resume["domains"] else 0.0

    score = 100 * (
        0.45 * required_skill_match +
        0.15 * optional_skill_match +
        0.20 * experience_fit +
        0.10 * seniority_fit +
        0.05 * english_fit +
        0.05 * domain_fit
    )

    missing_required = len(req) - matched_required
    if missing_required >= 2:
        score *= 0.6
    elif missing_required == 1:
        score *= 0.85

    if seniority_fit == 0.0:
        score *= 0.8

    score = round(clamp(score), 1)

    if score >= 80:
        label_class = "strong_fit"
    elif score >= 60:
        label_class = "fit"
    elif score >= 40:
        label_class = "borderline"
    else:
        label_class = "reject"

    label_binary = 1 if score >= 60 else 0

    reasons = []
    for skill in vacancy["required_skills"]:
        if skill in skills:
            reasons.append(f"matched_{skill.lower().replace('/', '_')}")
        else:
            reasons.append(f"missing_{skill.lower().replace('/', '_')}")

    if resume["experience_years"] < vacancy["min_experience_years"]:
        reasons.append("experience_below_required")
    else:
        reasons.append("experience_ok")

    if vacancy["domain"] in resume["domains"]:
        reasons.append("domain_matched")
    else:
        reasons.append("domain_not_matched")

    return {
        "score": score,
        "label_binary": label_binary,
        "label_class": label_class,
        "features_debug": {
            "required_skill_match": round(required_skill_match, 2),
            "optional_skill_match": round(optional_skill_match, 2),
            "experience_fit": round(experience_fit, 2),
            "seniority_fit": round(seniority_fit, 2),
            "english_fit": round(english_fit, 2),
            "domain_fit": round(domain_fit, 2)
        },
        "reasons": reasons
    }


#рендер текста

def render_vacancy_text(vacancy: dict) -> str:
    template = random_choice(TEXT_VARIANTS_VACANCY)
    return template.format(
        role=vacancy["role"],
        seniority=vacancy["seniority"],
        required_skills=", ".join(vacancy["required_skills"]),
        optional_skills=", ".join(vacancy["optional_skills"]) if vacancy["optional_skills"] else "None",
        min_experience_years=vacancy["min_experience_years"],
        english_level=vacancy["english_level"],
        domain=vacancy["domain"],
        location_mode=vacancy["location_mode"]
    )

def render_resume_text(resume: dict) -> str:
    template = random_choice(TEXT_VARIANTS_RESUME)
    return template.format(
        current_title=resume["current_title"],
        experience_years=resume["experience_years"],
        domains=", ".join(resume["domains"]),
        skills=", ".join(resume["skills"]),
        seniority=resume["seniority"],
        english_level=resume["english_level"],
        location_mode=resume["location_mode"]
    )


#делаем датасет

def build_dataset(num_vacancies: int) -> list:
    dataset = []

    for vac_idx in range(num_vacancies):
        role_name = random_choice(list(ROLE_LIBRARY.keys()))
        vacancy = generate_vacancy(role_name)

        vacancy_id = f"vac_{vac_idx:05d}"
        group_id = vacancy_id

        for cand_idx, candidate_type in enumerate(CANDIDATE_DISTRIBUTION):
            resume = generate_resume_for_vacancy(vacancy, candidate_type)
            scoring = score_pair(vacancy, resume)

            record = {
                "pair_id": f"{vacancy_id}_cand_{cand_idx:03d}_{uuid.uuid4().hex[:6]}",
                "vacancy_id": vacancy_id,
                "candidate_id": make_id("cand"),
                "group_id": group_id,

                "vacancy_structured": vacancy,
                "resume_structured": resume,

                "features_debug": scoring["features_debug"],
                "score": scoring["score"],
                "label_binary": scoring["label_binary"],
                "label_class": scoring["label_class"],
                "candidate_type": candidate_type,
                "reasons": scoring["reasons"],

                "vacancy_text": render_vacancy_text(vacancy),
                "resume_text": render_resume_text(resume)
            }
            dataset.append(record)

    return dataset


def save_jsonl(records: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def save_json(records: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


#мэин
random.seed(42)

dataset = build_dataset(NUM_VACANCIES)

save_jsonl(dataset, OUTPUT_JSONL)
save_json(dataset, OUTPUT_JSON)

print(f"Saved {len(dataset)} records")
print(f"JSONL: {Path(OUTPUT_JSONL).resolve()}")
print(f"JSON : {Path(OUTPUT_JSON).resolve()}")
print("\nExample record:\n")
print(json.dumps(dataset[0], ensure_ascii=False, indent=2))