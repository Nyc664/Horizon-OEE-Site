@echo off
title Horizon OEE Seguro - Backend Local
cd /d "%~dp0"

echo.
echo ==========================================
echo  HORIZON OEE SEGURO - BACKEND LOCAL
echo ==========================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    %PYTHON_CMD% -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
python -m pip install --upgrade pip

if exist requirements.txt (
    pip install -r requirements.txt
) else (
    pip install -r requirements-security.txt
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo.
        echo ATENCAO: foi criado backend\.env baseado no .env.example.
        echo Edite o .env e coloque suas chaves reais quando for usar Supabase pelo backend.
        echo.
    )
)

echo.
echo Iniciando servidor em:
echo http://127.0.0.1:8000
echo.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause
