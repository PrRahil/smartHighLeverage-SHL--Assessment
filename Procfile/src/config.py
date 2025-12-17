"""
Configuration settings for the SHL GenAI Recommendation Engine
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Database Configuration
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Scraping Configuration
    SCRAPING_DELAY = int(os.getenv("SCRAPING_DELAY", 2))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

    # Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-8b")

    # RAG Configuration
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 25))
    FINAL_RECOMMENDATIONS = int(os.getenv("FINAL_RECOMMENDATIONS", 8))

    # File Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    CHROMA_DIR = BASE_DIR / "chroma_db"

    # SHL Scraping Configuration
    SHL_CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
    TARGET_COUNT = 377  # Minimum expected products

    # Selenium Configuration
    WEBDRIVER_TIMEOUT = 30
    PAGE_LOAD_TIMEOUT = 60
    IMPLICIT_WAIT = 10

    @classmethod
    def validate_config(cls):
        """Validate essential configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required but not set")

        # Create directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.CHROMA_DIR.mkdir(exist_ok=True)

        return True

# Global config instance
config = Config()
