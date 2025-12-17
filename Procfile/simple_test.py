import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing SHL API Endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health Check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return
    
    # Test recommendation endpoint
    try:
        payload = {"query": "Java programming skills for collaboration"}
        response = requests.post(f"{base_url}/recommend", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get("recommended_assessments", [])
            print(f"\nRecommendations: {len(recommendations)} assessments")
            
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"{i}. {rec['name']} (Type: {rec['test_type']}, Score: {rec['relevance_score']:.2f})")
        else:
            print(f"Recommendation Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Recommendation Test Failed: {e}")

if __name__ == "__main__":
    test_api()