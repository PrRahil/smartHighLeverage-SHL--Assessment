# Streamlit Deployment Configuration
# For platforms like Streamlit Cloud, Heroku, etc.

# Entry point for Streamlit deployment
# Use: streamlit run frontend/app.py

# For backend deployment, use:
# uvicorn main:app --host 0.0.0.0 --port $PORT

# Alternative entry points:
# 1. For combined deployment: python deploy.py
# 2. For frontend only: streamlit run frontend/app.py --server.port 8501
# 3. For backend only: uvicorn main:app --host 0.0.0.0 --port 8000