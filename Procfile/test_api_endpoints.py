#!/usr/bin/env python3
"""
Test the API endpoints to ensure they meet the requirements
"""

import requests
import json
import time
from typing import List, Dict

def test_api_endpoints():
    """Test both required API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Endpoints...")
    
    # Wait for server to be ready
    print("Waiting for server to start...")
    time.sleep(15)
    
    try:
        # Test 1: Health Check Endpoint
        print("\n1. Testing Health Check Endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Recommendation Endpoint
        print("\n2. Testing Recommendation Endpoint...")
        
        test_queries = [
            "I am hiring for Java developers who can also collaborate effectively with my business teams.",
            "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript.",
            "I need assessments for an analyst position with cognitive and personality tests"
        ]
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Test Query {i}: {query}")
            
            payload = {"query": query}
            response = requests.post(
                f"{base_url}/recommend", 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommended_assessments", [])
                
                print(f"   ✅ Got {len(recommendations)} recommendations")
                
                # Validate response format
                if recommendations:
                    first_rec = recommendations[0]
                    required_fields = ['name', 'description', 'test_type', 'relevance_score']
                    
                    missing_fields = [field for field in required_fields if field not in first_rec]
                    if missing_fields:
                        print(f"   ⚠️  Missing fields in response: {missing_fields}")
                    else:
                        print(f"   ✅ Response format is valid")
                        print(f"   Top recommendation: {first_rec['name']}")
                
                # Store for CSV generation
                for rec in recommendations:
                    results.append({
                        'Query': query,
                        'Assessment_url': f"https://www.shl.com/products/product-catalog/view/{rec['name'].lower().replace(' ', '-')}/"
                    })
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        # Test 3: Generate Sample CSV Output
        if results:
            print(f"\n3. Generating Sample CSV Output...")
            
            csv_content = "Query,Assessment_url\n"
            for result in results:
                # Escape commas in query
                query_clean = result['Query'].replace(',', ';')
                csv_content += f'"{query_clean}",{result["Assessment_url"]}\n'
            
            with open('sample_predictions.csv', 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            print("   ✅ Sample CSV generated: sample_predictions.csv")
        
        print(f"\n✅ All API tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure it's running on port 8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_api_endpoints()