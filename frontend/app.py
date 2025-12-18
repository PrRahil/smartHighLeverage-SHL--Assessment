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

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.config import config
    from src.rag_engine import SHLRAGEngine
    from src.utils.helpers import setup_logging
    DIRECT_RAG_AVAILABLE = True
except ImportError:
    DIRECT_RAG_AVAILABLE = False

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
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: 2px solid #2E86C1;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(46, 134, 193, 0.1);
    }
    .assessment-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1B4F72;
        margin-bottom: 1rem;
    }
    .assessment-link {
        font-size: 1rem;
        color: #2E86C1;
        text-decoration: none;
        font-weight: 500;
        padding: 0.75rem 1rem;
        background-color: #FFFFFF;
        border: 1px solid #2E86C1;
        border-radius: 0.5rem;
        display: inline-block;
        transition: all 0.3s ease;
    }
    .assessment-link:hover {
        background-color: #2E86C1;
        color: #FFFFFF;
        text-decoration: none;
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
        if DIRECT_RAG_AVAILABLE:
            # Use localhost instead of 0.0.0.0 for frontend connections
            self.api_base_url = f"http://localhost:{config.PORT}"
        else:
            self.api_base_url = "http://localhost:8000"  # Default to standard port
        self.rag_engine = None

    def initialize_rag_engine(self):
        """Initialize RAG engine for direct access"""
        if not DIRECT_RAG_AVAILABLE:
            return False

        if self.rag_engine is None:
            self.rag_engine = SHLRAGEngine()
            if self.rag_engine.initialize():
                self.rag_engine.load_data()
                return True
        return self.rag_engine is not None and self.rag_engine.data_loaded

    def get_recommendations_api(self, query: str) -> Optional[List[Dict]]:
        """Get recommendations via FastAPI with auto-retry"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    st.info(f"🔗 Connecting to API: {self.api_base_url}")
                else:
                    st.info(f"🔄 Retry attempt {attempt}/{max_retries-1} - Waiting for backend to initialize...")
                
                response = requests.post(
                    f"{self.api_base_url}/recommend",
                    json={"query": query},
                    timeout=30,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommended_assessments", [])
                    st.success(f"✅ API Connected! Got {len(recommendations)} recommendations")
                    return recommendations
                else:
                    st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    return None

            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    import time
                    st.warning(f"⏳ Backend starting up... Retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay += 1  # Increase delay with each attempt
                else:
                    st.error(f"❌ API Not Available\n\nFailed to connect after {max_retries} attempts. Backend may not be running.")
                    # Try direct mode as fallback
                    st.warning("🔄 Attempting direct mode as fallback...")
                    return self.get_recommendations_direct(query)
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    st.warning(f"⏱️ Request timeout. Retrying... (attempt {attempt + 1}/{max_retries})")
                else:
                    st.error("⏱️ API request timed out after multiple attempts. Please check if backend is running.")
                return None
                
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {e}")
                return None
        
        return None

    def check_backend_health(self) -> bool:
        """Check if backend API is healthy and ready"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_backend(self, max_wait_time: int = 30):
        """Wait for backend to be ready with progress indicator"""
        placeholder = st.empty()
        
        for i in range(max_wait_time):
            if self.check_backend_health():
                placeholder.success("✅ Backend is ready!")
                return True
            
            remaining = max_wait_time - i
            placeholder.info(f"⏳ Waiting for backend to initialize... ({remaining}s remaining)")
            
            import time
            time.sleep(1)
        
        placeholder.error("❌ Backend failed to start within expected time")
        return False

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

    def get_demo_recommendations(self, query: str) -> List[Dict]:
        """Get demo recommendations when no backend/direct mode available"""
        # Simple demo recommendations based on query content
        query_lower = query.lower()
        
        recommendations = []
        
        # Technical skills assessments
        if any(word in query_lower for word in ['programming', 'coding', 'developer', 'technical', 'software', 'java', 'python']):
            recommendations.extend([
                {
                    "name": "Programming Skills Assessment",
                    "url": "https://www.shl.com/en/assessments/technical-skills/",
                    "description": "Evaluate programming and technical abilities",
                    "test_type": "Technical Skills",
                    "duration": "60 minutes"
                },
                {
                    "name": "Cognitive Ability - Technical Reasoning",
                    "url": "https://www.shl.com/en/assessments/cognitive-ability/",
                    "description": "Assess logical and analytical thinking for technical roles",
                    "test_type": "Cognitive",
                    "duration": "45 minutes"
                }
            ])
        
        # Leadership and management assessments
        if any(word in query_lower for word in ['leadership', 'manager', 'management', 'lead', 'supervisor']):
            recommendations.extend([
                {
                    "name": "Leadership Assessment",
                    "url": "https://www.shl.com/en/assessments/leadership/",
                    "description": "Evaluate leadership potential and management skills",
                    "test_type": "Leadership",
                    "duration": "50 minutes"
                },
                {
                    "name": "Situational Judgment Test - Management",
                    "url": "https://www.shl.com/en/assessments/situational-judgment/",
                    "description": "Assess decision-making in management scenarios",
                    "test_type": "Situational Judgment",
                    "duration": "40 minutes"
                }
            ])
        
        # Communication and soft skills
        if any(word in query_lower for word in ['communication', 'customer', 'service', 'interpersonal', 'teamwork']):
            recommendations.extend([
                {
                    "name": "Communication Skills Assessment",
                    "url": "https://www.shl.com/en/assessments/communication/",
                    "description": "Evaluate verbal and written communication abilities",
                    "test_type": "Communication",
                    "duration": "35 minutes"
                },
                {
                    "name": "Personality Assessment - Teamwork",
                    "url": "https://www.shl.com/en/assessments/personality/",
                    "description": "Assess personality traits for team collaboration",
                    "test_type": "Personality",
                    "duration": "30 minutes"
                }
            ])
        
        # Default recommendations if no specific keywords found
        if not recommendations:
            recommendations = [
                {
                    "name": "General Cognitive Ability Assessment",
                    "url": "https://www.shl.com/en/assessments/cognitive-ability/",
                    "description": "Comprehensive assessment of reasoning abilities",
                    "test_type": "Cognitive",
                    "duration": "45 minutes"
                },
                {
                    "name": "Workplace Personality Assessment",
                    "url": "https://www.shl.com/en/assessments/personality/",
                    "description": "Evaluate personality traits for workplace success",
                    "test_type": "Personality",
                    "duration": "30 minutes"
                },
                {
                    "name": "Situational Judgment Test",
                    "url": "https://www.shl.com/en/assessments/situational-judgment/",
                    "description": "Assess decision-making in workplace scenarios",
                    "test_type": "Situational Judgment",
                    "duration": "40 minutes"
                }
            ]
        
        return recommendations[:5]  # Limit to 5 recommendations

    def render_assessment_card(self, assessment: Dict, index: int):
        """Render a simplified assessment card with only SHL direct link"""
        # Get the assessment name and URL
        assessment_name = assessment.get('name', f'Assessment {index}')
        assessment_url = assessment.get('url', '')
        
        # Use the actual SHL URL from the scraped data
        if assessment_url and 'shl.com' in assessment_url:
            shl_url = assessment_url
        else:
            # Fallback URL construction if URL is missing
            shl_url = f"https://www.shl.com/products/product-catalog/view/{assessment_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '')}/"
        
        with st.container():
            st.markdown(f"""
            <div class="assessment-card">
                <div class="assessment-title">{index}. {assessment_name}</div>
                <a href="{shl_url}" target="_blank" class="assessment-link">
                    🔗 {shl_url}
                </a>
            </div>
            """, unsafe_allow_html=True)

    def render_search_results(self, results):
        """Render search results with direct links"""
        if results:
            # Display success message with count and links
            st.success(f"Found {len(results)} recommendations for: {st.session_state.get('last_search_query', 'your search')}")
            
            # Create expandable section with direct links
            with st.expander("🔗 Direct Links to Results", expanded=True):
                for i, result in enumerate(results, 1):
                    # Create clickable link for each result
                    link_text = result.get('title', f'Result {i}')
                    if 'url' in result:
                        st.markdown(f"**{i}.** [{link_text}]({result['url']})")
                    elif 'id' in result:
                        # If no direct URL, create a reference link
                        st.markdown(f"**{i}.** {link_text} (ID: {result['id']})")
                    else:
                        st.markdown(f"**{i}.** {link_text}")
            
            # Render individual result cards
            for i, result in enumerate(results):
                self.render_result_card(result, i)
        else:
            st.warning("No recommendations found for your search query.")

    def render_result_card(self, result, index):
        """Render individual result card with proper error handling"""
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Title with optional link
                title = result.get('title', f'Result {index + 1}')
                if 'url' in result:
                    st.markdown(f"### [{title}]({result['url']})")
                else:
                    st.markdown(f"### {title}")
                
                # Description
                if 'description' in result:
                    st.write(result['description'])
                
                # Tags or categories
                if 'tags' in result:
                    st.markdown(" ".join([f"`{tag}`" for tag in result['tags']]))
            
            with col2:
                # Action button with link
                if 'url' in result:
                    st.markdown(f"[📋 View Details]({result['url']})")
                elif 'id' in result:
                    if st.button(f"View {result['id']}", key=f"view_{index}"):
                        st.info(f"Opening result: {result['id']}")

    def render_assessment_card(self, assessment, index):
        """Render assessment card with proper error handling for missing fields"""
        with st.container():
            st.markdown(f"""
            <div class="assessment-card">
                <div class="assessment-header">
                    <h3>{assessment.get('title', 'Assessment')}</h3>
                </div>
                <div class="assessment-content">
                    <p>{assessment.get('description', 'No description available')}</p>
                    <div class="assessment-meta">
                        🎯 Skills: {', '.join(assessment.get('skills', ['Not specified']))}
                    </div>
                    <div class="assessment-meta">
                        📊 Difficulty: {assessment.get('difficulty', 'Not specified')}
                    </div>
                    <div class="assessment-meta">
                        🕒 Duration: {assessment.get('duration', 'Not specified')} {'minutes' if assessment.get('duration') else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Take Assessment", key=f"take_{index}"):
                    st.session_state.selected_assessment = assessment
                    st.session_state.current_page = 'assessment_detail'
                    st.rerun()
            
            with col2:
                # Add direct link if available
                if 'url' in assessment:
                    st.markdown(f"[🔗 Direct Link]({assessment['url']})")

    def perform_search(self, query):
        """Enhanced search function with link generation"""
        try:
            # Store the search query for later reference
            st.session_state.last_search_query = query
            
            # Simulate API call or database search
            # Replace this with your actual search logic
            results = self.mock_search_results(query)
            
            # Ensure each result has necessary fields
            for result in results:
                if 'url' not in result and 'id' in result:
                    # Generate URL based on result type and ID
                    result['url'] = self.generate_result_url(result)
            
            return results
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            return []

    def generate_result_url(self, result):
        """Generate appropriate URL for result based on type"""
        result_type = result.get('type', 'general')
        result_id = result.get('id', '')
        
        # Generate URLs based on your application structure
        url_mapping = {
            'assessment': f"/assessment/{result_id}",
            'course': f"/course/{result_id}",
            'job': f"/job/{result_id}",
            'profile': f"/profile/{result_id}",
            'general': f"/item/{result_id}"
        }
        
        return url_mapping.get(result_type, f"/item/{result_id}")

    def mock_search_results(self, query):
        """Mock search results with proper structure including URLs"""
        return [
            {
                'id': 'java_dev_001',
                'title': 'Senior Java Developer - Remote',
                'description': 'Looking for experienced Java developer with strong collaboration skills',
                'type': 'job',
                'url': 'https://example.com/jobs/java_dev_001',
                'tags': ['Java', 'Remote', 'Collaboration'],
                'duration': 45,
                'difficulty': 'Senior'
            },
            {
                'id': 'java_assessment_001',
                'title': 'Java Collaboration Assessment',
                'description': 'Assessment focusing on Java skills and team collaboration',
                'type': 'assessment',
                'url': 'https://example.com/assessments/java_assessment_001',
                'tags': ['Java', 'Teamwork'],
                'duration': 60,
                'difficulty': 'Intermediate',
                'skills': ['Java', 'Communication', 'Team Collaboration']
            },
            # Add more mock results...
        ]

    def run(self):
        """Main application"""
        # Header
        st.markdown('<h1 class="main-header">🎯 SHL GenAI Recommendation Engine</h1>', unsafe_allow_html=True)

        # Sidebar
        with st.sidebar:
            st.header("🔧 Configuration")

            # API vs Direct mode
            use_api = st.checkbox("Use FastAPI Backend", value=True, help="Uncheck to use direct RAG engine")

            # Auto-detect API availability
            api_available = False
            if use_api:
                try:
                    response = requests.get(f"{self.api_base_url}/health", timeout=5)
                    if response.status_code == 200:
                        api_available = True
                        st.success("✅ API Connected")
                        health_data = response.json()
                        st.caption(f"Status: {health_data.get('status', 'unknown')}")
                    else:
                        st.error(f"❌ API Error: {response.status_code}")
                except:
                    # API not available, auto-switch to direct mode
                    st.warning("⚠️ API not available - Switching to direct mode")
                    use_api = False
            
            if not use_api:
                if DIRECT_RAG_AVAILABLE:
                    st.info("✅ Using direct RAG engine")
                else:
                    st.warning("⚠️ Direct mode not available - Using demo mode")
                    st.caption("Some dependencies might be missing for full functionality")

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
                        # Get recommendations with fallback hierarchy
                        if use_api and api_available:
                            recommendations = self.get_recommendations_api(query)
                        elif DIRECT_RAG_AVAILABLE:
                            recommendations = self.get_recommendations_direct(query)
                        else:
                            # Demo mode fallback
                            recommendations = self.get_demo_recommendations(query)

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

                    # Display direct links list only
                    st.subheader("🔗 Direct SHL Assessment Links:")
                    
                    # Display as clickable links, not code block
                    for i, assessment in enumerate(recommendations, 1):
                        assessment_url = assessment.get('url', '')
                        assessment_name = assessment.get('name', f'Assessment {i}')
                        if assessment_url:
                            st.markdown(f"**{i}.** [{assessment_url}]({assessment_url})")
                        else:
                            st.markdown(f"**{i}.** {assessment_name} (URL not available)")

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
    if DIRECT_RAG_AVAILABLE:
        setup_logging()

    app = StreamlitApp()
    
    # Initialize system - gracefully handle backend availability
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = True
        
        with st.spinner("🚀 Initializing SHL Recommendation System..."):
            # Try backend first, fallback to direct mode
            backend_available = app.check_backend_health()
            if backend_available:
                st.success("✅ System ready! Full functionality with backend API.")
            elif DIRECT_RAG_AVAILABLE:
                st.success("✅ System ready! Running in direct mode.")
            else:
                st.info("ℹ️ Running in demo mode. Some features may be limited.")
    
    app.run()

if __name__ == "__main__":
    main()
