@echo off
title SHL Assessment Recommendation Engine
color 0A
echo.
echo ========================================
echo   SHL GenAI Recommendation Engine
echo ========================================
echo.
echo Starting services...
echo.

REM Kill any existing processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM streamlit.exe 2>nul

REM Wait a moment
timeout /t 3 /nobreak >nul

echo [1/2] Starting FastAPI Backend...
start "SHL Backend" cmd /k "cd /d %~dp0 && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to initialize
echo [1/2] Waiting for backend to initialize...
timeout /t 15 /nobreak >nul

echo [2/2] Starting Streamlit Frontend...
start "SHL Frontend" cmd /k "cd /d %~dp0 && python -m streamlit run frontend/app.py --server.port 8501"

REM Wait for both to start
timeout /t 8 /nobreak >nul

echo.
echo ========================================
echo           Services Started!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend:    http://localhost:8501
echo.
echo Opening frontend in browser...
start http://localhost:8501

echo.
echo Both services are running in separate windows.
echo Close this window or press any key to continue...
pause >nul