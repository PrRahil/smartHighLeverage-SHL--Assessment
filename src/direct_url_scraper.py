"""
Direct URL SHL Catalog Scraper
Uses direct URLs with start parameter to efficiently scrape all 377 entries
"""
import time
import json
import csv
import requests
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger
import os
import random
from urllib.parse import urljoin

@dataclass
class AssessmentEntry:
    """Data structure for SHL assessment entries"""
    name: str = ""
    categories: List[str] = None
    url: str = ""
    page_number: int = 0
    start_value: int = 0
    description: str = ""

    def __post_init__(self):
        if self.categories is None:
            self.categories = []

class DirectURLScraper:
    """Direct URL scraper using start parameter pattern"""

    def __init__(self, output_dir: str = "data"):
        self.base_url = "https://www.shl.com/products/product-catalog/"
        self.output_dir = output_dir
        self.progress_file = os.path.join(output_dir, "direct_scraping_progress.json")
        self.results_file = os.path.join(output_dir, "shl_direct_catalog.json")
        self.csv_file = os.path.join(output_dir, "shl_direct_catalog.csv")

        # Setup session with proper headers
        self.session = requests.Session()
        self.setup_session()

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # All entries collected
        self.all_entries = []

    def setup_session(self):
        """Setup requests session with proper headers"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]

        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_page_url(self, start_value: int) -> str:
        """Generate URL for specific page using start parameter"""
        return f"{self.base_url}?start={start_value}&type=1"

    def scrape_page(self, start_value: int, page_num: int) -> List[AssessmentEntry]:
        """Scrape a single page using direct URL"""
        url = self.get_page_url(start_value)
        entries = []

        try:
            logger.info(f"🔍 Scraping page {page_num} (start={start_value}): {url}")

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for assessment entries - adapting to actual page structure
                product_items = soup.find_all(['div', 'li', 'article'], class_=lambda x: x and any(
                    keyword in x.lower() for keyword in ['product', 'item', 'card', 'entry', 'assessment', 'result']))

                if not product_items:
                    # Fallback: look for any elements with links to assessment pages
                    product_items = soup.find_all('a', href=lambda x: x and '/en/assessments/' in x)

                if not product_items:
                    # Another fallback: look for structured content
                    product_items = soup.find_all(['div', 'section'], class_=lambda x: x and 'grid' in x.lower())
                    if product_items:
                        # Look inside grid containers
                        nested_items = []
                        for container in product_items:
                            nested_items.extend(container.find_all(['div', 'a'], href=True))
                        product_items = nested_items

                logger.info(f"   Found {len(product_items)} potential product items")

                for i, item in enumerate(product_items):
                    try:
                        entry = self.extract_entry_data(item, page_num, start_value)
                        if entry and entry.name:  # Only add if we got meaningful data
                            entries.append(entry)
                            logger.debug(f"   ✅ Entry {i+1}: {entry.name[:50]}...")
                    except Exception as e:
                        logger.debug(f"   ⚠️ Error extracting entry {i+1}: {e}")
                        continue

                # If we didn't find structured items, try extracting all links
                if len(entries) == 0:
                    logger.info("   No structured items found, trying to extract all assessment links...")
                    all_links = soup.find_all('a', href=True)
                    assessment_links = [link for link in all_links
                                      if link.get('href') and '/assessments/' in link.get('href', '')]

                    for link in assessment_links:
                        try:
                            entry = self.extract_entry_from_link(link, page_num, start_value)
                            if entry and entry.name:
                                entries.append(entry)
                        except Exception as e:
                            logger.debug(f"   Error extracting from link: {e}")
                            continue

                logger.info(f"   ✅ Successfully extracted {len(entries)} entries from page {page_num}")

            else:
                logger.warning(f"   ❌ HTTP {response.status_code} for page {page_num}")

        except Exception as e:
            logger.error(f"   ❌ Error scraping page {page_num}: {e}")

        return entries

    def extract_entry_data(self, item, page_num: int, start_value: int) -> Optional[AssessmentEntry]:
        """Extract data from a product item element"""
        try:
            name = ""
            url = ""
            categories = []
            description = ""

            # Extract name - try multiple selectors
            name_selectors = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '.title', '.name', '.product-title', '.assessment-title',
                '[data-title]', '.card-title'
            ]

            for selector in name_selectors:
                name_elem = item.select_one(selector)
                if name_elem:
                    name = name_elem.get_text().strip()
                    if name:
                        break

            # Extract URL
            if item.name == 'a' and item.get('href'):
                url = item.get('href')
            else:
                link_elem = item.find('a', href=True)
                if link_elem:
                    url = link_elem.get('href')

            # Make URL absolute
            if url and not url.startswith('http'):
                url = urljoin("https://www.shl.com", url)

            # Extract categories
            category_selectors = [
                '.category', '.tag', '.label', '.type', '.product-type'
            ]

            for selector in category_selectors:
                category_elems = item.select(selector)
                for elem in category_elems:
                    cat_text = elem.get_text().strip()
                    if cat_text and cat_text not in categories:
                        categories.append(cat_text)

            # Extract description
            desc_selectors = [
                '.description', '.summary', '.excerpt', 'p'
            ]

            for selector in desc_selectors:
                desc_elem = item.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text().strip()
                    if description:
                        break

            # If no name found, try to get it from the URL or any text
            if not name and url:
                # Extract name from URL
                url_parts = url.strip('/').split('/')
                if url_parts:
                    name = url_parts[-1].replace('-', ' ').title()

            if not name:
                # Get any text content as fallback
                name = item.get_text().strip()[:100]  # Limit length

            if name and len(name) > 3:  # Minimum name length
                return AssessmentEntry(
                    name=name,
                    categories=categories,
                    url=url,
                    page_number=page_num,
                    start_value=start_value,
                    description=description
                )

        except Exception as e:
            logger.debug(f"Error extracting entry data: {e}")

        return None

    def extract_entry_from_link(self, link, page_num: int, start_value: int) -> Optional[AssessmentEntry]:
        """Extract entry data from a link element"""
        try:
            name = link.get_text().strip()
            url = link.get('href')

            if url and not url.startswith('http'):
                url = urljoin("https://www.shl.com", url)

            if name and len(name) > 3:
                return AssessmentEntry(
                    name=name,
                    categories=[],
                    url=url,
                    page_number=page_num,
                    start_value=start_value,
                    description=""
                )
        except Exception as e:
            logger.debug(f"Error extracting from link: {e}")

        return None

    def save_progress(self, current_page: int, total_entries: int):
        """Save current progress"""
        progress = {
            'last_page': current_page,
            'total_entries': total_entries,
            'timestamp': time.time()
        }

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)

    def save_results(self, entries: List[AssessmentEntry]):
        """Save results to both JSON and CSV"""
        # Save to JSON
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(entry) for entry in entries], f, indent=2, ensure_ascii=False)

        # Save to CSV
        if entries:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'categories', 'url', 'page_number', 'start_value', 'description'])
                writer.writeheader()

                for entry in entries:
                    row = asdict(entry)
                    # Convert list to string for CSV
                    if isinstance(row['categories'], list):
                        row['categories'] = '; '.join(row['categories'])
                    writer.writerow(row)

        logger.info(f"💾 Results saved to {self.results_file} and {self.csv_file}")

    def run_complete_scraping(self) -> int:
        """Scrape all pages from 0 to 372 (32 pages total)"""
        logger.info("🚀 Starting complete SHL catalog scraping using direct URLs")
        logger.info("   Pattern: ?start=X&type=1 where X goes from 0 to 372 in steps of 12")

        # Calculate all start values (0, 12, 24, ..., 372)
        start_values = list(range(0, 373, 12))  # 0 to 372 inclusive, step 12
        total_pages = len(start_values)

        logger.info(f"   Total pages to scrape: {total_pages}")
        logger.info(f"   Start values: {start_values[:5]}...{start_values[-5:]}")

        all_entries = []
        successful_pages = 0

        for i, start_value in enumerate(start_values):
            page_num = i + 1

            try:
                logger.info(f"\n📄 Processing page {page_num}/{total_pages} (start={start_value})")

                # Scrape the page
                entries = self.scrape_page(start_value, page_num)

                if entries:
                    all_entries.extend(entries)
                    successful_pages += 1
                    logger.info(f"   ✅ Page {page_num}: Added {len(entries)} entries (total: {len(all_entries)})")
                else:
                    logger.warning(f"   ⚠️ Page {page_num}: No entries found")

                # Save progress every 5 pages
                if page_num % 5 == 0:
                    self.save_progress(page_num, len(all_entries))
                    self.save_results(all_entries)
                    logger.info(f"   💾 Progress saved at page {page_num}")

                # Random delay between requests
                delay = random.uniform(1, 3)
                logger.debug(f"   ⏱️ Waiting {delay:.1f}s before next request...")
                time.sleep(delay)

            except Exception as e:
                logger.error(f"   ❌ Error on page {page_num}: {e}")
                continue

        # Final save
        self.save_results(all_entries)
        self.save_progress(total_pages, len(all_entries))

        # Summary
        logger.info(f"\n🎉 SCRAPING COMPLETE!")
        logger.info(f"   📊 Total entries collected: {len(all_entries)}")
        logger.info(f"   📄 Successful pages: {successful_pages}/{total_pages}")
        logger.info(f"   💾 Results saved to: {self.csv_file}")

        return len(all_entries)

def main():
    """Main function"""
    scraper = DirectURLScraper()
    total_entries = scraper.run_complete_scraping()
    return total_entries

if __name__ == "__main__":
    main()
