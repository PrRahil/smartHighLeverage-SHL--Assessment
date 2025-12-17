#!/usr/bin/env python3
"""
Test the enhanced RAG system with training data
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.enhanced_rag_engine import initialize_enhanced_rag_engine, get_enhanced_recommendations

def test_enhanced_system():
    """Test the enhanced recommendation system"""
    print("🧪 Testing Enhanced SHL Recommendation System...")
    
    # Initialize enhanced system
    print("1. Initializing Enhanced RAG engine...")
    if not initialize_enhanced_rag_engine():
        print("❌ Failed to initialize enhanced RAG engine")
        return False
    
    print("✅ Enhanced RAG engine initialized")
    
    # Test sales query from your example
    test_query = "I want to hire new graduates for a sales role in my company, the budget is for about an hour for each test. Give me some options"
    
    print(f"\n2. Testing query: '{test_query}'")
    recommendations = get_enhanced_recommendations(test_query)
    
    if recommendations:
        print(f"✅ Got {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.name}")
            print(f"   URL: {rec.url}")
            if hasattr(rec, 'similarity_score'):
                print(f"   Score: {rec.similarity_score}")
            print()
    else:
        print("❌ No recommendations returned")
    
    # Test Java query 
    java_query = "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."
    
    print(f"\n3. Testing Java query: '{java_query}'")
    java_recommendations = get_enhanced_recommendations(java_query)
    
    if java_recommendations:
        print(f"✅ Got {len(java_recommendations)} recommendations:")
        for i, rec in enumerate(java_recommendations, 1):
            print(f"{i}. {rec.name}")
            print(f"   URL: {rec.url}")
            print()
    else:
        print("❌ No Java recommendations returned")
    
    return True

if __name__ == "__main__":
    test_enhanced_system()