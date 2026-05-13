# Candidate Scoring MVP

Веб-приложение для подбора кандидатов под вакансию. Проект позволяет добавлять вакансии, загружать резюме и запускать скоринг кандидатов по навыкам, опыту и семантической близости текста.

## Возможности

- добавление вакансии через веб-форму;
- добавление резюме вручную;
- загрузка резюме в формате TXT или PDF;
- скоринг всех резюме под выбранную вакансию;
- просмотр результата: общий score, совпадение ключевых слов, семантическая оценка, найденные и недостающие обязательные навыки;
- REST API для работы с вакансиями, резюме и скорингом.

## Технологии

- Python;
- FastAPI;
- Uvicorn;
- Jinja2;
- SQLite;
- scikit-learn;
- sentence-transformers / transformers / torch.

## Структура проекта

```text
MLproject-main/
├── data/                 # данные вакансий, резюме и генератор тестовых данных
├── db/                   # локальная база данных SQLite
├── program/              # основной backend-код приложения
│   ├── api.py            # FastAPI-приложение и endpoints
│   ├── database.py       # работа с базой данных
│   ├── importers.py      # импорт вакансий и резюме
│   ├── scoring.py        # логика скоринга
│   └── text_utils.py     # обработка текста
├── static/               # CSS и статические файлы
├── templates/            # HTML-шаблоны
├── first_lauch.bat       # установка зависимостей
├── launch.bat            # запуск сайта
├── requirements.txt      # зависимости Python
└── README.md
```

## Установка и запуск на Windows

Перед первым запуском нужен установленный Python.

Создайте виртуальное окружение в корне проекта:

```bat
python -m venv .venv
```

Установите зависимости:

```bat
first_lauch.bat
```

Запустите сайт:

```bat
launch.bat
```

После запуска откройте в браузере:

```text
http://127.0.0.1:8000
```

## Ручной запуск

Если запускать без `.bat`-файлов:

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn program.api:app --reload --host 127.0.0.1 --port 8000
```

## Основные API endpoints

- `GET /` - веб-интерфейс приложения;
- `POST /vacancies` - создать вакансию через API;
- `GET /vacancies/{vacancy_id}` - получить данные вакансии;
- `POST /resumes/upload` - загрузить резюме TXT или PDF;
- `POST /resumes/manual` - добавить резюме текстом;
- `GET /db/summary` - получить статистику базы данных;
- `POST /score/vacancies/{vacancy_id}` - оценить все резюме для вакансии;
- `POST /score/vacancies/{vacancy_id}/resumes/{resume_id}` - оценить одно резюме под вакансию.
