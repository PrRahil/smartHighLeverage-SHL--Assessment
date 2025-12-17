"""
Streamlit App for SHL GenAI Recommendation Engine
Standalone version for Streamlit Community Cloud deployment
"""

import streamlit as st
import pandas as pd
import json
from typing import List, Dict, Optional
import os
import sys
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "src"))

# Page configuration
st.set_page_config(
    page_title="SHL GenAI Recommendation Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .assessment-card {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 2px solid #2E86C1;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(46, 134, 193, 0.1);
    }
    .stButton > button {
        background-color: #2E86C1;
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """Load sample assessment data"""
    return {
        "assessments": [
            {
                "title": "Cognitive Ability Test",
                "description": "Measures reasoning, problem-solving, and logical thinking abilities.",
                "types": ["Numerical", "Verbal", "Abstract"],
                "link": "https://www.shl.com/cognitive-ability"
            },
            {
                "title": "Personality Assessment",
                "description": "Evaluates personality traits and behavioral preferences.",
                "types": ["OPQ32", "Motivation Questionnaire"],
                "link": "https://www.shl.com/personality"
            },
            {
                "title": "Situational Judgment Test",
                "description": "Assesses decision-making in workplace scenarios.",
                "types": ["Management", "Customer Service", "Sales"],
                "link": "https://www.shl.com/situational-judgment"
            }
        ]
    }

def main():
    """Main Streamlit application"""
    
    st.markdown('<h1 class="main-header">🎯 SHL GenAI Recommendation Engine</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to the SHL Assessment Recommendation System
    This AI-powered platform helps you find the most suitable SHL assessments based on your requirements.
    """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        mode = st.selectbox(
            "Select Mode",
            ["Demo Mode", "API Mode (requires backend)"],
            help="Demo mode works standalone, API mode requires the FastAPI backend"
        )
        
        if mode == "API Mode (requires backend)":
            api_url = st.text_input("Backend API URL", value="http://localhost:8000")
            
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Find Your Assessment")
        
        # Input form
        with st.form("recommendation_form"):
            job_role = st.text_input(
                "Job Role/Position",
                placeholder="e.g., Software Developer, Sales Manager, Customer Support"
            )
            
            industry = st.selectbox(
                "Industry",
                ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", "Other"]
            )
            
            company_size = st.selectbox(
                "Company Size",
                ["Startup (1-50)", "Medium (51-500)", "Large (501-5000)", "Enterprise (5000+)"]
            )
            
            skills_required = st.multiselect(
                "Key Skills Required",
                ["Leadership", "Problem Solving", "Communication", "Analytical Thinking", 
                 "Customer Service", "Sales", "Technical", "Creative"]
            )
            
            additional_requirements = st.text_area(
                "Additional Requirements (optional)",
                placeholder="Any specific requirements or preferences..."
            )
            
            submitted = st.form_submit_button("Get Recommendations")
        
        if submitted and job_role:
            with st.spinner("🤖 Generating personalized recommendations..."):
                
                if mode == "Demo Mode":
                    # Demo recommendations
                    st.success("✅ Recommendations generated successfully!")
                    
                    data = load_sample_data()
                    
                    st.subheader("📋 Recommended SHL Assessments")
                    
                    for i, assessment in enumerate(data["assessments"], 1):
                        with st.container():
                            st.markdown(f"""
                            <div class="assessment-card">
                                <div class="assessment-title">{i}. {assessment['title']}</div>
                                <p><strong>Description:</strong> {assessment['description']}</p>
                                <p><strong>Assessment Types:</strong> {', '.join(assessment['types'])}</p>
                                <p><strong>Match Score:</strong> {95 - i*5}% (Based on: {job_role}, {industry})</p>
                                <a href="{assessment['link']}" target="_blank" class="assessment-link">
                                    📖 Learn More
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                
                elif mode == "API Mode (requires backend)":
                    try:
                        import requests
                        
                        payload = {
                            "job_role": job_role,
                            "industry": industry,
                            "company_size": company_size,
                            "skills_required": skills_required,
                            "additional_requirements": additional_requirements
                        }
                        
                        response = requests.post(f"{api_url}/recommend", json=payload, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Recommendations received from API!")
                            
                            if "recommendations" in result:
                                st.subheader("📋 API Recommendations")
                                for rec in result["recommendations"]:
                                    st.write(rec)
                            else:
                                st.write(result)
                        else:
                            st.error(f"API Error: {response.status_code}")
                            st.write("Falling back to demo mode...")
                            
                    except Exception as e:
                        st.error(f"Cannot connect to backend API: {e}")
                        st.info("💡 Tip: Make sure your FastAPI backend is running on the specified URL")
    
    with col2:
        st.subheader("ℹ️ About SHL")
        st.info("""
        **SHL** is a global leader in talent assessment and development solutions.
        
        **Key Assessment Types:**
        - 🧠 Cognitive Ability Tests
        - 👤 Personality Assessments  
        - 🎯 Situational Judgment Tests
        - 💼 Skills-Based Evaluations
        - 🎓 Learning Agility Tests
        """)
        
        st.subheader("🚀 How It Works")
        st.markdown("""
        1. **Input** your job requirements
        2. **AI analyzes** your needs
        3. **Get personalized** assessment recommendations
        4. **Access** detailed information and links
        """)
        
        # System status
        with st.expander("🔧 System Status"):
            st.write("**Frontend:** ✅ Active")
            if mode == "API Mode (requires backend)":
                st.write("**Backend API:** ❓ Check connection")
            else:
                st.write("**Mode:** 🎮 Demo Mode")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🎯 SHL GenAI Recommendation Engine | Built with Streamlit & FastAPI</p>
        <p>For more information, visit <a href="https://www.shl.com" target="_blank">SHL.com</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()