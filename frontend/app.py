"""
Streamlit Frontend for SHL GenAI Recommendation Engine
Web interface to test the assessment recommendation system
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Add src to path for direct RAG access
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.config import config
from src.rag_engine import SHLRAGEngine
from src.utils.helpers import setup_logging

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
    .query-box {
        background-color: #F8F9FA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86C1;
        margin: 1rem 0;
    }
    .assessment-card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 1px solid #E3E6F0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .assessment-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 0.5rem;
    }
    .assessment-meta {
        font-size: 0.9rem;
        color: #7B68EE;
        margin: 0.25rem 0;
    }
    .test-type-badge {
        background-color: #E8F4FD;
        color: #2E86C1;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin: 0.1rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    """Streamlit application for SHL recommendations"""
    
    def __init__(self):
        self.api_base_url = f"http://{config.HOST}:{config.PORT}"
        self.rag_engine = None
        
    def initialize_rag_engine(self):
        """Initialize RAG engine for direct access"""
        if self.rag_engine is None:
            self.rag_engine = SHLRAGEngine()
            if self.rag_engine.initialize():
                self.rag_engine.load_data()
                return True
        return self.rag_engine is not None and self.rag_engine.data_loaded
    
    def get_recommendations_api(self, query: str) -> Optional[List[Dict]]:
        """Get recommendations via FastAPI"""
        try:
            response = requests.post(
                f"{self.api_base_url}/recommend",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("recommended_assessments", [])
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.warning(f"API not available: {e}")
            return None
    
    def get_recommendations_direct(self, query: str) -> Optional[List[Dict]]:
        """Get recommendations directly from RAG engine"""
        try:
            if not self.initialize_rag_engine():
                st.error("Failed to initialize RAG engine")
                return None
            
            recommendations = self.rag_engine.recommend(query)
            
            # Convert to dict format
            result = []
            for rec in recommendations:
                result.append({
                    "name": rec.name,
                    "url": rec.url,
                    "description": rec.description,
                    "duration": rec.duration,
                    "adaptive_support": rec.adaptive_support,
                    "remote_support": rec.remote_support,
                    "test_type": rec.test_type
                })
            
            return result
            
        except Exception as e:
            st.error(f"Direct RAG error: {e}")
            return None
    
    def render_assessment_card(self, assessment: Dict, index: int):
        """Render an assessment card"""
        with st.container():
            st.markdown(f"""
            <div class="assessment-card">
                <div class="assessment-title">{index}. {assessment['name']}</div>
                <div class="assessment-meta">🕒 Duration: {assessment['duration']} minutes</div>
                <div class="assessment-meta">🔄 Adaptive: {assessment['adaptive_support']} | 🌐 Remote: {assessment['remote_support']}</div>
                <div style="margin: 0.5rem 0;">
                    {''.join([f'<span class="test-type-badge">{t}</span>' for t in assessment['test_type']])}
                </div>
                <p style="margin: 0.5rem 0; color: #34495E;">{assessment['description'][:200]}...</p>
                <a href="{assessment['url']}" target="_blank" style="color: #2E86C1; text-decoration: none;">🔗 View Assessment</a>
            </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """Main application"""
        # Header
        st.markdown('<h1 class="main-header">🎯 SHL GenAI Recommendation Engine</h1>', unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.header("🔧 Configuration")
            
            # API vs Direct mode
            use_api = st.checkbox("Use FastAPI Backend", value=True, help="Uncheck to use direct RAG engine")
            
            if use_api:
                st.info("Using FastAPI backend for recommendations")
                # Test API connection
                try:
                    response = requests.get(f"{self.api_base_url}/health", timeout=5)
                    if response.status_code == 200:
                        st.success("✅ API Connected")
                    else:
                        st.error("❌ API Error")
                except:
                    st.error("❌ API Not Available")
            else:
                st.info("Using direct RAG engine")
            
            st.header("📊 Sample Queries")
            sample_queries = [
                "Software developer with Java and Python skills",
                "Leadership assessment for managers",
                "Customer service communication skills",
                "Data analyst with technical and analytical skills", 
                "Sales professional with interpersonal skills",
                "Project manager with leadership and technical skills",
                "Financial analyst with numerical reasoning",
                "HR professional with personality assessment needs",
                "Technical architect with programming expertise",
                "Team lead with both technical and soft skills"
            ]
            
            selected_sample = st.selectbox("Choose a sample query:", [""] + sample_queries)
        
        # Main content
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.header("💬 Query Input")
            
            # Query input
            query = st.text_area(
                "Enter your assessment requirements:",
                value=selected_sample,
                height=100,
                placeholder="e.g., I need assessments for software developers with strong programming skills and leadership potential"
            )
            
            # Submit button
            if st.button("🔍 Get Recommendations", type="primary", use_container_width=True):
                if not query.strip():
                    st.error("Please enter a query")
                else:
                    with st.spinner("Getting recommendations..."):
                        # Get recommendations
                        if use_api:
                            recommendations = self.get_recommendations_api(query)
                        else:
                            recommendations = self.get_recommendations_direct(query)
                        
                        # Store in session state
                        st.session_state.recommendations = recommendations
                        st.session_state.current_query = query
            
            # Query analysis
            if query.strip():
                st.markdown('<div class="query-box">', unsafe_allow_html=True)
                st.subheader("🎯 Query Analysis")
                
                # Simple keyword analysis
                technical_keywords = ['programming', 'java', 'python', 'technical', 'coding', 'software', 'development']
                soft_keywords = ['leadership', 'communication', 'management', 'personality', 'teamwork', 'interpersonal']
                
                query_lower = query.lower()
                has_technical = any(keyword in query_lower for keyword in technical_keywords)
                has_soft = any(keyword in query_lower for keyword in soft_keywords)
                
                if has_technical and has_soft:
                    st.info("🎯 **Balance Detection**: Query contains both technical and soft skills. The system will apply balance logic to recommend both 'Knowledge & Skills' and 'Personality & Behavior' assessments.")
                elif has_technical:
                    st.info("💻 **Technical Focus**: Query focuses on technical skills. Recommendations will emphasize 'Knowledge & Skills' assessments.")
                elif has_soft:
                    st.info("🤝 **Soft Skills Focus**: Query focuses on soft skills. Recommendations will emphasize 'Personality & Behavior' assessments.")
                else:
                    st.info("🔍 **General Query**: System will provide balanced recommendations based on semantic similarity.")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.header("📋 Recommendations")
            
            # Display recommendations
            if hasattr(st.session_state, 'recommendations') and st.session_state.recommendations:
                recommendations = st.session_state.recommendations
                
                if recommendations:
                    st.success(f"Found {len(recommendations)} recommendations for: *{st.session_state.current_query}*")
                    
                    # Display each recommendation
                    for i, assessment in enumerate(recommendations, 1):
                        self.render_assessment_card(assessment, i)
                    
                    # Download option
                    if st.button("📥 Download Results as CSV"):
                        df = pd.DataFrame(recommendations)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name="shl_recommendations.csv",
                            mime="text/csv"
                        )
                else:
                    st.warning("No recommendations found for your query. Please try a different search.")
            
            elif hasattr(st.session_state, 'recommendations'):
                st.error("Failed to get recommendations. Please try again.")
            
            else:
                st.info("Enter a query and click 'Get Recommendations' to see results.")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #7B68EE; font-size: 0.9rem;'>
            <p>🎯 SHL GenAI Recommendation Engine | Powered by Google Gemini & ChromaDB</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main function"""
    setup_logging()
    
    app = StreamlitApp()
    app.run()

if __name__ == "__main__":
    main()