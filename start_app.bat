@echo off
echo ========================================
echo SHL GenAI Recommendation Engine
echo ========================================
echo.
echo Step 1: Starting FastAPI Backend...
echo.
start "FastAPI Backend" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 10 /nobreak >nul

echo Step 2: Starting Streamlit Frontend...
echo.
start "Streamlit Frontend" cmd /k "python -m streamlit run frontend/app.py --server.port 8501"

echo.
echo ========================================
echo Services Starting...
echo ========================================
echo FastAPI Backend: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Streamlit Frontend: http://localhost:8501
echo ========================================
echo.
echo Press any key to open the web interface...
pause >nul

start http://localhost:8501