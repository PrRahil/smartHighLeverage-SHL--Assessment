#!/usr/bin/env python3
"""
Test the API to ensure it returns exactly 5-10 recommendations
"""

import requests
import json

def test_recommendation_count():
    """Test that API returns 5-10 recommendations"""
    
    # Test queries
    test_queries = [
        "I want to hire new graduates for a sales role",
        "Java developers who can collaborate effectively",
        "Leadership assessment for managers",
        "Technical assessment for software engineers",
        "Communication skills test"
    ]
    
    api_url = "http://localhost:8000/recommend"
    
    print("🧪 Testing Recommendation Count Enforcement...")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        try:
            print(f"\n{i}. Testing query: '{query[:50]}...'")
            
            # Make API request
            response = requests.post(
                api_url,
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", [])
                count = len(recommendations)
                
                # Check count
                if 5 <= count <= 10:
                    print(f"   ✅ PASS: Got {count} recommendations (within 5-10 range)")
                else:
                    print(f"   ❌ FAIL: Got {count} recommendations (outside 5-10 range)")
                
                # Show first few URLs for verification
                for j, rec in enumerate(recommendations[:3], 1):
                    url = rec.get("url", "No URL")
                    print(f"     {j}. {url}")
                
                if count > 3:
                    print(f"     ... and {count-3} more")
                    
            else:
                print(f"   ❌ API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_recommendation_count()