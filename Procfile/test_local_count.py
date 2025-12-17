#!/usr/bin/env python3
"""
Simple test to verify the recommendation system locally without API calls
"""

import sys
sys.path.append('.')

from src.enhanced_rag_engine import initialize_enhanced_rag_engine, get_enhanced_recommendations
from src.rag_engine import initialize_rag_engine, get_recommendations

def test_recommendation_counts():
    """Test recommendation counts locally"""
    
    print("🧪 Testing Recommendation Count Enforcement Locally...")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "I want to hire new graduates for a sales role",
        "Java developers with collaboration skills", 
        "Leadership assessment for managers"
    ]
    
    # Try enhanced RAG first
    print("\n1. Testing Enhanced RAG Engine:")
    if initialize_enhanced_rag_engine():
        print("   ✅ Enhanced RAG initialized")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Test {i}: '{query[:40]}...'")
            try:
                recommendations = get_enhanced_recommendations(query)
                count = len(recommendations)
                
                if 5 <= count <= 10:
                    print(f"      ✅ PASS: {count} recommendations (within 5-10 range)")
                else:
                    print(f"      ❌ FAIL: {count} recommendations (outside 5-10 range)")
                    
                # Show URLs
                for j, rec in enumerate(recommendations[:3], 1):
                    print(f"        {j}. {rec.name}")
                if count > 3:
                    print(f"        ... and {count-3} more")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
    else:
        print("   ⚠️  Enhanced RAG failed to initialize")
    
    # Test standard RAG as fallback
    print("\n2. Testing Standard RAG Engine:")
    if initialize_rag_engine():
        print("   ✅ Standard RAG initialized")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Test {i}: '{query[:40]}...'")
            try:
                recommendations = get_recommendations(query)
                count = len(recommendations)
                
                if 5 <= count <= 10:
                    print(f"      ✅ PASS: {count} recommendations (within 5-10 range)")
                else:
                    print(f"      ❌ FAIL: {count} recommendations (outside 5-10 range)")
                    
                # Show URLs
                for j, rec in enumerate(recommendations[:3], 1):
                    print(f"        {j}. {rec.name}")
                if count > 3:
                    print(f"        ... and {count-3} more")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
    else:
        print("   ❌ Standard RAG failed to initialize")

    print("\n" + "=" * 60)
    print("✅ Local testing completed!")

if __name__ == "__main__":
    test_recommendation_counts()