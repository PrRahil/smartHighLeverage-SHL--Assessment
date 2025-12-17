#!/bin/bash

# Start backend server in background
echo "Starting FastAPI backend server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 5

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run frontend/app.py --server.port 8501