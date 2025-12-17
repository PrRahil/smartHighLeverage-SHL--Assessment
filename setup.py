"""
Setup script for the SHL GenAI Recommendation Engine
Run this first to set up the environment and test scraping
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.helpers import install_chromedriver, setup_logging, check_dependencies
from src.config import config
from loguru import logger

def main():
    """Main setup function"""
    print("🚀 Setting up SHL GenAI Recommendation Engine...")
    
    # Setup logging
    setup_logging()
    
    # Validate configuration
    try:
        config.validate_config()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.info("Please update your .env file with the required API keys")
        return False
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Missing dependencies - please run: pip install -r requirements.txt")
        return False
    
    # Install ChromeDriver
    logger.info("Installing ChromeDriver...")
    if not install_chromedriver():
        logger.error("❌ ChromeDriver installation failed")
        return False
    
    logger.info("✅ Setup completed successfully!")
    logger.info(f"📁 Data directory: {config.DATA_DIR}")
    logger.info(f"📁 Logs directory: {config.LOGS_DIR}")
    logger.info(f"📁 ChromaDB directory: {config.CHROMA_DIR}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 Setup complete! You can now run:")
    print("  python run_scraper.py  - To scrape SHL assessments")
    print("  python main.py         - To start the FastAPI server")  
    print("  streamlit run frontend/app.py - To start the web interface")
    print("="*60)