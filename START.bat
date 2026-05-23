@echo off
title OnlineBazar — React + Django REST Framework
color 0A

echo.
echo  ============================================
echo   OnlineBazar — MCA Project
echo   Ankit Sharma (34) ^& Niraj Kumar (8)
echo  ============================================
echo.

:: ── Check Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b
)

:: ── Check Node ────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b
)

:: ── Backend Setup ─────────────────────────────────────────────
echo [1/4] Setting up Backend...
cd backend

if not exist venv (
    echo       Creating virtual environment...
    python -m venv venv
)

echo       Activating virtual environment...
call venv\Scripts\activate.bat

echo       Installing Python dependencies...
pip install -r requirements.txt -q

echo       Running migrations...
python manage.py migrate

echo       [DONE] Backend ready!
echo.

:: ── Start Django in new window ────────────────────────────────
echo [2/4] Starting Django server on http://localhost:8000 ...
start "OnlineBazar Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python manage.py runserver"

:: ── Frontend Setup ────────────────────────────────────────────
cd ..\frontend
echo [3/4] Setting up Frontend...

if not exist node_modules (
    echo       Installing npm packages (first time only, please wait)...
    npm install
) else (
    echo       node_modules found, skipping install.
)

echo       [DONE] Frontend ready!
echo.

:: ── Start React in new window ─────────────────────────────────
echo [4/4] Starting React app on http://localhost:3000 ...
start "OnlineBazar Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: ── Done ──────────────────────────────────────────────────────
echo.
echo  ============================================
echo   Both servers are starting up!
echo.
echo   Backend  →  http://localhost:8000
echo   API      →  http://localhost:8000/api/
echo   Frontend →  http://localhost:3000
echo  ============================================
echo.
echo  Two new windows have opened.
echo  Press any key to open the app in your browser...
pause >nul

start http://localhost:3000
