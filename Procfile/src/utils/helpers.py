"""
Utility functions for the SHL project
"""

import subprocess
import sys
import os
from pathlib import Path
from loguru import logger

def install_chromedriver():
    """Install ChromeDriver using webdriver-manager"""
    try:
        # Install webdriver-manager if not already installed
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
        
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        # Download and install ChromeDriver
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver installed at: {driver_path}")
        
        # Test the installation
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()
        
        logger.info("✅ ChromeDriver installation verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to install ChromeDriver: {e}")
        return False

def setup_logging():
    """Setup logging configuration"""
    from src.config import config
    
    # Create logs directory if it doesn't exist
    config.LOGS_DIR.mkdir(exist_ok=True)
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL
    )
    
    # Add file logger
    logger.add(
        config.LOGS_DIR / "shl_app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days"
    )

def check_dependencies():
    """Check if all required dependencies are installed"""
    critical_packages = [
        'selenium', 'bs4', 'requests', 'fastapi', 'uvicorn',
        'streamlit', 'chromadb', 'langchain', 'pandas', 'loguru'
    ]
    
    missing_packages = []
    
    for package in critical_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing critical packages: {missing_packages}")
        logger.info("Run: pip install -r requirements.txt")
        return False
    
    # Test sentence-transformers separately due to tensorflow issues
    try:
        import sentence_transformers
        logger.debug("✅ sentence-transformers available")
    except ImportError:
        logger.warning("⚠️ sentence-transformers not available - will need for RAG engine")
    
    logger.info("✅ All critical dependencies are available")
    return True