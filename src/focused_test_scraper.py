"""
Focused SHL Test Scraper
Extracts only test/assessment related information from SHL product catalog
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
from typing import List, Dict
from dataclasses import dataclass, asdict
from pathlib import Path
import re

@dataclass
class TestInfo:
    """Test information structure matching the table format"""
    name: str
    url: str
    remote_testing: str = ""
    adaptive_irt: str = ""
    test_type: str = ""
    page_number: int = 0

class FocusedTestScraper:
    """Scraper focused only on test/assessment products"""

    def __init__(self):
        self.base_url = "https://www.shl.com/products/product-catalog/"
        self.tests = []
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Setup session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })

    def is_test_related(self, name: str, url: str, description: str) -> bool:
        """Check if the item is actually a test/assessment"""
        test_keywords = [
            'test', 'assessment', 'evaluation', 'measure', 'aptitude',
            'reasoning', 'cognitive', 'personality', 'skills', 'ability',
            'opq', 'spi', 'verification', 'situational', 'judgment',
            'numerical', 'verbal', 'logical', 'mechanical', 'spatial',
            'programming', 'technical', 'leadership', 'sales', 'customer'
        ]

        # Exclude navigation and general pages
        exclude_keywords = [
            'careers', 'contact', 'support', 'search', 'categories',
            'login', 'register', 'about', 'company', 'news', 'blog',
            'privacy', 'terms', 'cookies', 'legal', 'sitemap'
        ]

        text_to_check = f"{name} {url} {description}".lower()

        # Check if it contains exclude keywords
        for exclude in exclude_keywords:
            if exclude in text_to_check:
                return False

        # Check if it contains test keywords
        for keyword in test_keywords:
            if keyword in text_to_check:
                return True

        # Additional checks for assessment products
        if any(pattern in url.lower() for pattern in ['/assessments/', '/products/', '/solutions/']):
            if any(test_word in text_to_check for test_word in ['test', 'assessment', 'measure']):
                return True

        return False

    def extract_test_from_table_row(self, row, page_number: int) -> TestInfo:
        """Extract test information from a table row"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 4:
                return None

            # First column: Test name and URL
            name_cell = cells[0]
            name_link = name_cell.find('a')

            if name_link:
                name = name_link.get_text(strip=True)
                url = name_link.get('href', '')
                if url.startswith('/'):
                    url = f"https://www.shl.com{url}"
            else:
                name = name_cell.get_text(strip=True)
                url = ""

            # Skip if name is empty or looks like a header
            if not name or name.lower() in ['individual test solutions', 'test name', 'name']:
                return None

            # Second column: Remote Testing (usually a green dot or text)
            remote_cell = cells[1]
            remote_testing = "Yes" if remote_cell.find('span', class_='green') or "●" in remote_cell.get_text() else remote_cell.get_text(strip=True)

            # Third column: Adaptive/IRT
            adaptive_cell = cells[2]
            adaptive_irt = adaptive_cell.get_text(strip=True) if adaptive_cell else ""

            # Fourth column: Test Type (might be an icon or text)
            type_cell = cells[3]
            test_type = type_cell.get_text(strip=True) if type_cell else ""

            return TestInfo(
                name=name,
                url=url,
                remote_testing=remote_testing,
                adaptive_irt=adaptive_irt,
                test_type=test_type,
                page_number=page_number
            )

        except Exception as e:
            print(f"Error extracting test from table row: {e}")
            return None

    def scrape_page(self, start_value: int, page_number: int) -> List[TestInfo]:
        """Scrape a single page for tests from the table structure"""
        url = f"{self.base_url}?start={start_value}&type=1"
        page_tests = []

        try:
            print(f"Scraping page {page_number} (start={start_value})")
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for the main table containing test results
                tables = soup.find_all('table')

                for table in tables:
                    # Find all rows in the table
                    rows = table.find_all('tr')

                    for row in rows:
                        test_info = self.extract_test_from_table_row(row, page_number)
                        if test_info and test_info.name:
                            # Additional validation to ensure it's a real test
                            if len(test_info.name) > 3 and not test_info.name.lower().startswith(('search', 'filter', 'sort')):
                                page_tests.append(test_info)
                                print(f"  Found: {test_info.name}")

                # If no table found, try alternative selectors for the catalog items
                if not page_tests:
                    # Look for catalog entries with different selectors
                    selectors = [
                        '.search-result-item',
                        '.product-item',
                        '.catalog-item',
                        'div[class*="result"]',
                        'div[class*="item"]'
                    ]

                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            print(f"  Found {len(items)} items with selector: {selector}")
                            for item in items:
                                # Try to extract as if it's a simple item
                                name_elem = item.find('a') or item.find('h3') or item.find('h4')
                                if name_elem:
                                    name = name_elem.get_text(strip=True)
                                    url = name_elem.get('href', '')
                                    if url.startswith('/'):
                                        url = f"https://www.shl.com{url}"

                                    if name and len(name) > 3:
                                        test_info = TestInfo(
                                            name=name,
                                            url=url,
                                            remote_testing="",
                                            adaptive_irt="",
                                            test_type="",
                                            page_number=page_number
                                        )
                                        page_tests.append(test_info)
                                        print(f"  Found: {name}")
                            break

                print(f"  Extracted {len(page_tests)} tests from page {page_number}")

            else:
                print(f"  Failed to load page {page_number}: {response.status_code}")

            # Add delay between requests
            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"  Error scraping page {page_number}: {e}")

        return page_tests

    def scrape_all_tests(self) -> int:
        """Scrape all pages for tests only"""
        print("🔬 Starting focused test extraction from SHL product catalog...")

        # Scrape pages 1-32 (start values 0-372 in increments of 12)
        for page_num in range(1, 33):  # Pages 1-32
            start_value = (page_num - 1) * 12

            page_tests = self.scrape_page(start_value, page_num)
            self.tests.extend(page_tests)

            print(f"Page {page_num}: Found {len(page_tests)} tests (Total: {len(self.tests)})")

            # Save progress every 5 pages
            if page_num % 5 == 0:
                self.save_tests()
                print(f"💾 Progress saved at page {page_num}")

        # Final save
        self.save_tests()

        print(f"\n✅ Scraping complete!")
        print(f"📊 Total tests extracted: {len(self.tests)}")

        return len(self.tests)

    def save_tests(self):
        """Save tests to CSV and JSON files"""
        if not self.tests:
            return

        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Save to CSV with table format
        csv_file = data_dir / "shl_test_table.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.tests:
                fieldnames = ['name', 'url', 'remote_testing', 'adaptive_irt', 'test_type', 'page_number']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for test in self.tests:
                    writer.writerow({
                        'name': test.name,
                        'url': test.url,
                        'remote_testing': test.remote_testing,
                        'adaptive_irt': test.adaptive_irt,
                        'test_type': test.test_type,
                        'page_number': test.page_number
                    })

        # Save to JSON
        json_file = data_dir / "shl_test_table.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(test) for test in self.tests], f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(self.tests)} tests to {csv_file} and {json_file}")

def main():
    """Main function"""
    scraper = FocusedTestScraper()
    count = scraper.scrape_all_tests()

    print(f"\n🎯 TEST TABLE EXTRACTION COMPLETE")
    print(f"📋 Total Tests Found: {count}")
    print(f"📁 Files saved:")
    print(f"   • data/shl_test_table.csv")
    print(f"   • data/shl_test_table.json")

    return count > 0

if __name__ == "__main__":
    main()
