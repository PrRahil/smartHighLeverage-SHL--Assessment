"""
Streamlit App for SHL GenAI Recommendation Engine
Entry point for Streamlit Community Cloud deployment
"""

import streamlit as st
import sys
from pathlib import Path

# Add the frontend directory to the path
current_dir = Path(__file__).parent
frontend_dir = current_dir / "frontend"
sys.path.insert(0, str(frontend_dir))

# Import and run the main app
try:
    from app import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    st.error(f"Error importing app: {e}")
    st.info("Please ensure all dependencies are installed and the frontend/app.py file exists.")