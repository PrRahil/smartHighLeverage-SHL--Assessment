#!/usr/bin/env python3
"""
Simple script to run both FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def run_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI Backend on port 8000...")
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ], cwd=Path(__file__).parent)

def run_frontend():
    """Start the Streamlit frontend"""
    print("🌐 Starting Streamlit Frontend on port 8501...")
    return subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/app.py", "--server.port", "8501"
    ], cwd=Path(__file__).parent)

def main():
    print("🎯 SHL GenAI Recommendation Engine")
    print("=" * 50)
    
    try:
        # Start backend
        backend_process = run_backend()
        time.sleep(5)  # Wait for backend to start
        
        # Start frontend
        frontend_process = run_frontend()
        time.sleep(3)  # Wait for frontend to start
        
        print("\n✅ Both services started!")
        print("📊 FastAPI Backend: http://localhost:8000")
        print("📊 API Documentation: http://localhost:8000/docs")
        print("🌐 Streamlit Frontend: http://localhost:8501")
        
        print("\nPress Ctrl+C to stop both services...")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        try:
            backend_process.terminate()
            frontend_process.terminate()
        except:
            pass
        print("✅ Services stopped!")

if __name__ == "__main__":
    main()