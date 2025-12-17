#!/usr/bin/env python3
"""
Quick test to verify the recommendation system works
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.rag_engine import SHLRAGEngine

def test_system():
    """Test the recommendation system directly"""
    print("🧪 Testing SHL Recommendation System...")
    
    try:
        # Initialize RAG engine
        rag = SHLRAGEngine()
        
        print("1. Initializing RAG engine...")
        if not rag.initialize():
            print("❌ Failed to initialize RAG engine")
            return False
        
        print("2. Loading data...")
        if not rag.load_data():
            print("❌ Failed to load data")
            return False
        
        print("3. Testing retrieval...")
        candidates = rag.retrieve_assessments("Java programming test", k=5)
        print(f"   Retrieved {len(candidates)} candidates")
        
        if candidates:
            print("   Top candidate:", candidates[0]['name'])
        
        print("4. Testing full recommendation...")
        recommendations = rag.recommend("Java programming skills")
        print(f"   Generated {len(recommendations)} recommendations")
        
        if recommendations:
            print("\n📋 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"{i}. {rec.name}")
                print(f"   Type: {rec.test_type}")
                print(f"   Domain: {rec.description.split(' - ')[0] if ' - ' in rec.description else 'General'}")
                print()
        
        print("✅ System working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
