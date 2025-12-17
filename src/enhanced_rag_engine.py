"""
Enhanced RAG Engine with Training Data Integration for Better Accuracy
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from pathlib import Path

from src.config import config
from src.rag_engine import SHLRAGEngine
from loguru import logger

class EnhancedSHLRAGEngine(SHLRAGEngine):
    """Enhanced RAG Engine with training data for improved accuracy"""
    
    def __init__(self):
        super().__init__()
        self.training_data = None
        self.training_vectorizer = None
        self.training_vectors = None
        self.query_patterns = {}
        
    def load_training_data(self, training_file: str = "training_data.xlsx") -> bool:
        """Load and process training data for improved recommendations"""
        try:
            training_path = config.BASE_DIR / training_file
            if not training_path.exists():
                logger.warning(f"Training file not found: {training_path}")
                return False
            
            # Load training data
            self.training_data = pd.read_excel(training_path)
            logger.info(f"Loaded {len(self.training_data)} training examples")
            
            # Create query patterns for better matching
            self._create_query_patterns()
            
            # Create TF-IDF vectors for training queries
            self._create_training_vectors()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
            return False
    
    def _create_query_patterns(self):
        """Create patterns from training queries for better matching"""
        if self.training_data is None:
            return
            
        # Group URLs by similar queries
        query_url_map = {}
        for _, row in self.training_data.iterrows():
            query = row['Query'].lower().strip()
            url = row['Assessment_url']
            
            if query not in query_url_map:
                query_url_map[query] = []
            query_url_map[query].append(url)
        
        # Extract keywords and patterns
        for query, urls in query_url_map.items():
            # Extract key terms
            key_terms = self._extract_key_terms(query)
            self.query_patterns[query] = {
                'keywords': key_terms,
                'urls': urls,
                'query_text': query
            }
        
        logger.info(f"Created {len(self.query_patterns)} query patterns")
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from a query"""
        # Define important patterns
        role_patterns = [
            r'java\s+develop', r'sales\s+role', r'entry.level', r'new\s+graduate',
            r'manager', r'analyst', r'engineer', r'developer', r'representative'
        ]
        
        skill_patterns = [
            r'collaborat', r'communicat', r'technical', r'leadership', r'programming',
            r'interpersonal', r'business', r'analytical', r'problem.solving'
        ]
        
        assessment_patterns = [
            r'personality', r'cognitive', r'behavioral', r'technical', r'soft.skill',
            r'hard.skill', r'aptitude', r'competency'
        ]
        
        time_patterns = [
            r'\d+\s*minutes?', r'\d+\s*hours?', r'quick', r'short', r'brief', r'long'
        ]
        
        key_terms = []
        
        # Extract matches from all patterns
        all_patterns = role_patterns + skill_patterns + assessment_patterns + time_patterns
        for pattern in all_patterns:
            matches = re.findall(pattern, query.lower())
            key_terms.extend(matches)
        
        # Add individual important words
        important_words = [
            'java', 'python', 'sales', 'marketing', 'leadership', 'communication',
            'collaboration', 'technical', 'graduates', 'entry', 'senior', 'manager'
        ]
        
        words = query.lower().split()
        for word in words:
            if word in important_words:
                key_terms.append(word)
        
        return list(set(key_terms))  # Remove duplicates
    
    def _create_training_vectors(self):
        """Create TF-IDF vectors for training queries"""
        if self.training_data is None:
            return
            
        try:
            queries = self.training_data['Query'].tolist()
            
            # Create TF-IDF vectorizer with custom parameters
            self.training_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 3),  # Include bigrams and trigrams
                min_df=1,
                max_df=0.9
            )
            
            # Fit and transform training queries
            self.training_vectors = self.training_vectorizer.fit_transform(queries)
            logger.info("Created TF-IDF vectors for training queries")
            
        except Exception as e:
            logger.error(f"Failed to create training vectors: {e}")
    
    def enhanced_recommend(self, query: str, k: int = 10) -> List:
        """Enhanced recommendation using training data and original RAG"""
        
        # First, try to find exact or similar matches in training data
        training_matches = self._find_training_matches(query)
        
        if training_matches:
            logger.info(f"Found {len(training_matches)} matches in training data")
            
            # Get assessments for training URLs
            enhanced_recommendations = []
            for url in training_matches[:k]:
                # Find assessment in our data that matches this URL
                assessment = self._find_assessment_by_url(url)
                if assessment:
                    enhanced_recommendations.append(assessment)
            
            if enhanced_recommendations:
                # STRICT VALIDATION: Ensure 5-10 recommendations
                if len(enhanced_recommendations) < 5:
                    logger.info(f"Training matches only provided {len(enhanced_recommendations)}, getting additional from RAG")
                    # Get additional recommendations from original RAG
                    additional_recs = super().recommend(query)
                    # Add recommendations until we have at least 5
                    for rec in additional_recs:
                        if len(enhanced_recommendations) >= 10:  # Don't exceed maximum
                            break
                        # Avoid duplicates
                        if not any(existing.url == rec.url for existing in enhanced_recommendations):
                            enhanced_recommendations.append(rec)
                        if len(enhanced_recommendations) >= 5:  # We have minimum now
                            break
                elif len(enhanced_recommendations) > 10:
                    logger.info(f"Training matches provided {len(enhanced_recommendations)}, limiting to 10")
                    enhanced_recommendations = enhanced_recommendations[:10]
                
                logger.info(f"Returning {len(enhanced_recommendations)} enhanced recommendations (enforced 5-10 range)")
                return enhanced_recommendations
        
        # Fallback to original RAG if no training matches
        logger.info("Using original RAG engine as fallback")
        fallback_recs = super().recommend(query)
        
        # STRICT VALIDATION: Ensure 5-10 recommendations even in fallback
        if len(fallback_recs) < 5:
            logger.warning(f"Original RAG returned only {len(fallback_recs)} recommendations, expanding")
            # This shouldn't happen as original RAG now enforces 5-10, but just in case
            additional_recs = super().recommend(query + " assessment test")  # Broader query
            for rec in additional_recs:
                if len(fallback_recs) >= 10:
                    break
                if not any(existing.url == rec.url for existing in fallback_recs):
                    fallback_recs.append(rec)
        elif len(fallback_recs) > 10:
            logger.warning(f"Original RAG returned {len(fallback_recs)} recommendations, limiting to 10")
            fallback_recs = fallback_recs[:10]
        
        logger.info(f"Returning {len(fallback_recs)} fallback recommendations (enforced 5-10 range)")
        return fallback_recs
    
    def _find_training_matches(self, query: str, threshold: float = 0.3) -> List[str]:
        """Find matching URLs from training data based on query similarity"""
        if self.training_data is None or self.training_vectorizer is None:
            return []
        
        try:
            # Transform the input query
            query_vector = self.training_vectorizer.transform([query])
            
            # Calculate similarities with training queries
            similarities = cosine_similarity(query_vector, self.training_vectors)[0]
            
            # Get top similar queries
            similar_indices = np.argsort(similarities)[::-1]
            
            matching_urls = []
            seen_urls = set()
            
            for idx in similar_indices:
                if similarities[idx] < threshold:
                    break
                    
                url = self.training_data.iloc[idx]['Assessment_url']
                if url not in seen_urls:
                    matching_urls.append(url)
                    seen_urls.add(url)
                    
                if len(matching_urls) >= 10:  # Limit results
                    break
            
            logger.debug(f"Found {len(matching_urls)} training matches with similarity > {threshold}")
            return matching_urls
            
        except Exception as e:
            logger.error(f"Error finding training matches: {e}")
            return []
    
    def _find_assessment_by_url(self, url: str):
        """Find assessment object by URL from loaded data"""
        try:
            # Load our assessment data
            csv_path = config.DATA_DIR / "shl_test_table.csv"
            if not csv_path.exists():
                return None
                
            df = pd.read_csv(csv_path)
            
            # Find matching assessment
            matching_rows = df[df['url'] == url]
            if len(matching_rows) == 0:
                # Try partial URL matching
                url_suffix = url.split('/')[-2] if '/' in url else url
                matching_rows = df[df['url'].str.contains(url_suffix, na=False)]
            
            if len(matching_rows) > 0:
                row = matching_rows.iloc[0]
                
                # Create assessment object (using your existing Assessment model)
                from src.models import Assessment
                
                # Handle NaN values properly
                def safe_get(value, default='Not specified'):
                    if pd.isna(value) or value == '' or str(value).lower() == 'nan':
                        return default
                    return str(value)

                assessment = Assessment(
                    name=safe_get(row['name'], f'Assessment {url.split("/")[-2] if "/" in url else "Unknown"}'),
                    url=row['url'],
                    description=f"{safe_get(row.get('test_type'), 'Assessment')} - {safe_get(row['name'])}",
                    duration=safe_get(row.get('duration')),
                    adaptive_support=safe_get(row.get('adaptive_irt')),
                    remote_support=safe_get(row.get('remote_testing')),
                    test_type=[safe_get(row.get('test_type'), 'General')],
                    similarity_score=0.9  # High score for training matches
                )
                
                return assessment
                
        except Exception as e:
            logger.error(f"Error finding assessment by URL {url}: {e}")
        
        return None

# Initialize enhanced engine
enhanced_rag_engine = None

def initialize_enhanced_rag_engine() -> bool:
    """Initialize the enhanced RAG engine with training data"""
    global enhanced_rag_engine
    
    try:
        enhanced_rag_engine = EnhancedSHLRAGEngine()
        
        # Initialize base RAG functionality
        if not enhanced_rag_engine.initialize():
            return False
        
        # Load assessment data
        if not enhanced_rag_engine.load_data():
            return False
        
        # Load training data for enhanced accuracy
        enhanced_rag_engine.load_training_data()
        
        logger.info("Enhanced RAG engine initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced RAG engine: {e}")
        return False

def get_enhanced_recommendations(query: str) -> List:
    """Get enhanced recommendations using training data"""
    global enhanced_rag_engine
    
    if enhanced_rag_engine is None:
        if not initialize_enhanced_rag_engine():
            return []
    
    return enhanced_rag_engine.enhanced_recommend(query)