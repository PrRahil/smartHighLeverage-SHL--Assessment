"""
Quick Start Guide for SHL GenAI Recommendation Engine
Run this to get started immediately!
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🎯 SHL GenAI Recommendation Engine - Quick Start")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this from the SHL project directory!")
        return False
    
    print("📋 Available Options:")
    print("1. 🔧 Setup Environment (install ChromeDriver, etc.)")
    print("2. 🚀 Start FastAPI Backend")  
    print("3. 🌐 Start Streamlit Frontend")
    print("4. 🕷️  Run Scraper (requires API key)")
    print("5. 📊 Generate Submission CSV")
    print("6. 📄 View System Documentation")
    print("7. 🧪 Test System (basic test)")
    
    choice = input("\nEnter your choice (1-7): ").strip()
    
    if choice == "1":
        print("\n🔧 Setting up environment...")
        os.system(f"{sys.executable} setup.py")
        
    elif choice == "2":
        print("\n🚀 Starting FastAPI backend...")
        print("API will be available at: http://localhost:8000")
        print("API Docs at: http://localhost:8000/docs")
        os.system(f"{sys.executable} main.py")
        
    elif choice == "3":
        print("\n🌐 Starting Streamlit frontend...")
        print("Web interface will be available at: http://localhost:8501")
        os.system(f"{sys.executable} -m streamlit run frontend/app.py")
        
    elif choice == "4":
        print("\n🕷️ Running SHL catalog scraper...")
        print("⚠️  Make sure you have set GOOGLE_API_KEY in .env file!")
        proceed = input("Continue? (y/n): ").lower().startswith('y')
        if proceed:
            os.system(f"{sys.executable} run_scraper.py")
        
    elif choice == "5":
        print("\n📊 Generating submission CSV...")
        os.system(f"{sys.executable} evaluate.py")
        
    elif choice == "6":
        print("\n📄 System Documentation:")
        print("-" * 40)
        if Path("README_NEW.md").exists():
            with open("README_NEW.md", 'r', encoding='utf-8') as f:
                content = f.read()[:2000]  # First 2000 chars
                print(content)
                print("\n... (see README_NEW.md for full documentation)")
        else:
            print("Documentation not found. Check README_NEW.md")
            
    elif choice == "7":
        print("\n🧪 Testing system...")
        print("Note: This requires GOOGLE_API_KEY to be set in .env")
        proceed = input("Continue with test? (y/n): ").lower().startswith('y')
        if proceed:
            os.system(f"{sys.executable} test_system.py")
        
    else:
        print("❌ Invalid choice!")
        return False
    
    print(f"\n✅ Action completed!")
    return True

if __name__ == "__main__":
    main()
    
    print("\n" + "=" * 60)
    print("🎉 SHL GenAI Recommendation Engine Ready!")
    print("💡 Remember to set GOOGLE_API_KEY in .env file")
    print("📚 Check README_NEW.md for detailed documentation")
    print("🚀 Run this script again anytime for quick actions!")
    print("=" * 60)