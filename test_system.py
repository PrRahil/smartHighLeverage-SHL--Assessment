"""
Quick test script to verify the SHL RAG system works
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.rag_engine import SHLRAGEngine
from src.utils.helpers import setup_logging
from loguru import logger

def test_rag_system():
    """Test the RAG system with sample queries"""
    print("🧪 Testing SHL RAG System...")
    
    # Setup logging
    setup_logging()
    
    # Initialize RAG engine
    rag_engine = SHLRAGEngine()
    
    print("📦 Initializing RAG engine...")
    if not rag_engine.initialize():
        print("❌ Failed to initialize RAG engine")
        return False
    
    print("📊 Loading assessment data...")
    if not rag_engine.load_data():
        print("❌ Failed to load data")
        return False
    
    # Test queries
    test_queries = [
        "Software developer with Java programming skills",
        "Leadership assessment for managers", 
        "Data analyst with Python and SQL skills",
        "Customer service representative with communication skills"
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} sample queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        
        try:
            recommendations = rag_engine.recommend(query)
            
            if recommendations:
                print(f"✅ Got {len(recommendations)} recommendations:")
                for j, rec in enumerate(recommendations[:3], 1):  # Show top 3
                    print(f"  {j}. {rec.name}")
                    print(f"     Duration: {rec.duration}min, Types: {rec.test_type}")
            else:
                print("⚠️ No recommendations returned")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ RAG system test completed!")
    return True

if __name__ == "__main__":
    success = test_rag_system()
    if not success:
        sys.exit(1)