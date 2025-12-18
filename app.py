#!/usr/bin/env python3
"""
Streamlit App - Main entry point for deployment
Runs the SHL frontend with fallback demo mode when backend is not available
"""

import sys
from pathlib import Path
import streamlit as st

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "frontend"))

# Import with fallback
try:
    # Try to import the main frontend app
    from frontend.app import main as frontend_main
    frontend_available = True
except ImportError:
    frontend_available = False

def demo_mode():
    """Simple demo mode for Streamlit deployment"""
    st.set_page_config(
        page_title="SHL GenAI Recommendation Engine",
        page_icon="🎯",
        layout="wide"
    )
    
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2E86C1;
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🎯 SHL GenAI Recommendation Engine</h1>', unsafe_allow_html=True)
    
    st.info("""
    ### 📋 Demo Mode Active
    This is a demonstration version of the SHL Assessment Recommendation System.
    
    **Features:**
    - AI-powered assessment recommendations
    - Support for technical and soft skill assessments
    - Direct links to SHL assessment catalog
    - Intelligent query analysis
    """)
    
    # Input form
    st.header("🔍 Find Your Assessment")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        job_role = st.text_input("Job Role/Position", placeholder="e.g., Software Developer, Manager")
        skills = st.multiselect("Key Skills Required", [
            "Programming", "Leadership", "Communication", "Problem Solving",
            "Analytical Thinking", "Team Management", "Customer Service"
        ])
        query = st.text_area("Additional Requirements", placeholder="Any specific assessment needs...")
        
        if st.button("Get Recommendations", type="primary"):
            if job_role:
                st.success(f"✅ Found recommendations for: {job_role}")
                
                # Demo recommendations
                recommendations = [
                    {
                        "name": "Cognitive Ability Assessment",
                        "url": "https://www.shl.com/en/assessments/cognitive-ability/",
                        "description": "Measures reasoning and problem-solving abilities"
                    },
                    {
                        "name": "Personality Assessment",
                        "url": "https://www.shl.com/en/assessments/personality/",
                        "description": "Evaluates personality traits and behavioral preferences"
                    },
                    {
                        "name": "Situational Judgment Test",
                        "url": "https://www.shl.com/en/assessments/situational-judgment/",
                        "description": "Assesses decision-making in work scenarios"
                    }
                ]
                
                st.subheader("📋 Recommended Assessments:")
                
                for i, rec in enumerate(recommendations, 1):
                    st.markdown(f"""
                    **{i}. {rec['name']}**  
                    {rec['description']}  
                    🔗 [View Assessment]({rec['url']})
                    """)
            else:
                st.error("Please enter a job role")
    
    with col2:
        st.info("""
        **About SHL:**
        - Global leader in talent assessment
        - 🧠 Cognitive assessments
        - 👤 Personality tests
        - 🎯 Situational judgment
        - 💼 Skills evaluation
        """)
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        🎯 SHL GenAI Recommendation Engine | Powered by AI
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main entry point"""
    if frontend_available:
        try:
            # Try to run the full frontend
            frontend_main()
        except Exception as e:
            st.error(f"Frontend error: {e}")
            st.info("Falling back to demo mode...")
            demo_mode()
    else:
        # Run demo mode if frontend not available
        demo_mode()

if __name__ == "__main__":
    main()