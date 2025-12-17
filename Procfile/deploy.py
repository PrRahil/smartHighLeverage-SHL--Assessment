#!/usr/bin/env python3
"""
Deployment startup script for SHL Assessment Recommendation Engine
This script starts both backend and frontend services properly for deployment
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "1"
    ])
    return backend_process

def start_frontend():
    """Start the Streamlit frontend"""
    print("🌐 Starting Streamlit frontend...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ])
    return frontend_process

def check_backend_health(max_attempts=30):
    """Check if backend is healthy"""
    import requests
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is healthy!")
                return True
        except:
            pass
        
        print(f"⏳ Waiting for backend... ({attempt + 1}/{max_attempts})")
        time.sleep(2)
    
    return False

def main():
    """Main deployment function"""
    print("🎯 SHL Assessment Recommendation Engine - Deployment Startup")
    print("=" * 60)
    
    # Start backend
    backend_process = start_backend()
    
    # Wait for backend to be healthy
    if not check_backend_health():
        print("❌ Backend failed to start properly")
        backend_process.terminate()
        sys.exit(1)
    
    # Start frontend
    frontend_process = start_frontend()
    
    print("\n✅ Both services started successfully!")
    print("📱 Frontend: http://localhost:8501")
    print("🔧 Backend API: http://localhost:8000")
    print("\nPress Ctrl+C to stop all services...")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()