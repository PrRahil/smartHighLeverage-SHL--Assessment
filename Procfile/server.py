"""
Production-ready FastAPI server for deployment
"""

import os
import uvicorn
from src.config import config

if __name__ == "__main__":
    # Use environment PORT for deployment platforms
    port = int(os.environ.get("PORT", config.PORT))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        access_log=True
    )