@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found: .venv\Scripts\activate.bat
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m uvicorn program.api:app --reload --host 127.0.0.1 --port 8000

pause
