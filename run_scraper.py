"""
Script to run the SHL catalog scraper
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.scraper import main as run_scraper
from src.utils.helpers import setup_logging

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    print("🕷️ Starting SHL Assessment Scraper...")
    print("This will scrape the SHL catalog for Individual Test Solutions")
    print("Expected to find at least 377 assessments")
    print("-" * 60)
    
    # Run the scraper
    count = run_scraper()
    
    print("-" * 60)
    if count > 0:
        print(f"✅ Scraping completed! Found {count} assessments")
        print("📄 Data saved to: data/shl_data_detailed.csv")
    else:
        print("❌ Scraping failed - check logs for details")
        sys.exit(1)