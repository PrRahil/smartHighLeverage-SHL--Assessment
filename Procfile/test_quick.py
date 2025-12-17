#!/usr/bin/env python3

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("🧪 Quick System Test...")

# Test fallback logic directly
from src.rag_engine import SHLRAGEngine

print("1. Creating engine...")
engine = SHLRAGEngine()

print("2. Initializing...")
if engine.initialize():
    print("✅ Engine initialized")
    
    print("3. Testing recommendation...")
    recommendations = engine.recommend("Java programming skills")
    print(f"   Generated {len(recommendations)} recommendations")
    
    if recommendations:
        print(f"   Top recommendation: {recommendations[0].name}")
        print("✅ System working!")
    else:
        print("❌ No recommendations generated")
else:
    print("❌ Failed to initialize")
