"""
SHL Assessment Catalog Scraper
Deep scrapes the SHL product catalog to extract Individual Test Solutions
"""

import csv
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import requests

from src.config import config
from loguru import logger

@dataclass
class AssessmentData:
    """Data class for assessment information"""
    name: str
    url: str
    description: str
    duration: int
    adaptive_support: str
    remote_support: str
    test_type: List[str]

class SHLScraper:
    """Deep scraper for SHL assessment catalog"""
    
    def __init__(self):
        self.driver = None
        self.scraped_assessments: List[AssessmentData] = []
        self.base_url = config.SHL_CATALOG_URL
        
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            driver.implicitly_wait(config.IMPLICIT_WAIT)
            logger.info("Chrome WebDriver initialized successfully")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def load_all_products(self) -> List[str]:
        """Load the catalog page and click 'Load More' until all products are visible"""
        logger.info(f"Loading catalog page: {self.base_url}")
        
        try:
            self.driver.get(self.base_url)
            time.sleep(config.SCRAPING_DELAY)
            
            # Wait for page to load
            WebDriverWait(self.driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='product-card'], .product-card, .assessment-card"))
            )
            
            # Click "Load More" button repeatedly until all products are loaded
            load_more_attempts = 0
            max_attempts = 50  # Prevent infinite loop
            
            while load_more_attempts < max_attempts:
                try:
                    # Look for various possible "Load More" button selectors
                    load_more_selectors = [
                        "button[data-testid='load-more']",
                        "button.load-more",
                        "button:contains('Load More')",
                        "a[data-testid='load-more']",
                        ".load-more-button",
                        "[data-action='load-more']"
                    ]
                    
                    load_more_button = None
                    for selector in load_more_selectors:
                        try:
                            load_more_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if load_more_button.is_displayed() and load_more_button.is_enabled():
                                break
                        except NoSuchElementException:
                            continue
                    
                    if load_more_button:
                        logger.info(f"Clicking 'Load More' button (attempt {load_more_attempts + 1})")
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                        time.sleep(config.SCRAPING_DELAY)
                        load_more_attempts += 1
                    else:
                        logger.info("No more 'Load More' button found - all products loaded")
                        break
                        
                except Exception as e:
                    logger.warning(f"Error clicking 'Load More' button: {e}")
                    break
            
            # Extract product URLs
            product_urls = self.extract_product_urls()
            logger.info(f"Found {len(product_urls)} product URLs")
            return product_urls
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            return []
    
    def extract_product_urls(self) -> List[str]:
        """Extract all product URLs from the current page"""
        urls = []
        
        try:
            # Multiple selectors for product cards/links
            product_selectors = [
                "a[data-testid='product-card']",
                "a.product-card",
                "a[href*='/assessment/']",
                "a[href*='/product/']",
                "a[href*='/test/']",
                ".product-card a",
                "[data-testid='product-card'] a",
                ".assessment-card a"
            ]
            
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and self.is_valid_product_url(href):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in urls:
                                urls.append(full_url)
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
            
            # Filter for Individual Test Solutions (exclude pre-packaged job solutions)
            filtered_urls = []
            for url in urls:
                if self.is_individual_test_solution(url):
                    filtered_urls.append(url)
            
            logger.info(f"Filtered to {len(filtered_urls)} Individual Test Solution URLs")
            return filtered_urls
            
        except Exception as e:
            logger.error(f"Error extracting product URLs: {e}")
            return []
    
    def is_valid_product_url(self, url: str) -> bool:
        """Check if URL appears to be a valid product URL"""
        if not url:
            return False
        
        # Must be from SHL domain
        if 'shl.com' not in url:
            return False
            
        # Should contain product/assessment/test indicators
        url_lower = url.lower()
        valid_indicators = ['assessment', 'test', 'product', 'solution']
        
        return any(indicator in url_lower for indicator in valid_indicators)
    
    def is_individual_test_solution(self, url: str) -> bool:
        """
        Determine if this URL represents an Individual Test Solution
        (not a Pre-packaged Job Solution)
        """
        url_lower = url.lower()
        
        # Exclude pre-packaged job solutions
        exclude_keywords = [
            'job-solution', 'job-pack', 'package', 'bundle',
            'suite', 'collection', 'pre-packaged'
        ]
        
        if any(keyword in url_lower for keyword in exclude_keywords):
            return False
        
        # Include individual assessments/tests
        include_keywords = [
            'assessment', 'test', 'individual', 'single'
        ]
        
        return any(keyword in url_lower for keyword in include_keywords)
    
    def scrape_assessment_details(self, url: str) -> Optional[AssessmentData]:
        """Scrape detailed information from an individual assessment page"""
        logger.debug(f"Scraping details from: {url}")
        
        try:
            # Try with Selenium first
            self.driver.get(url)
            time.sleep(config.SCRAPING_DELAY)
            
            # Wait for page content
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"Timeout loading page: {url}")
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract assessment details
            assessment_data = self.parse_assessment_page(soup, url)
            
            if assessment_data:
                logger.debug(f"Successfully scraped: {assessment_data.name}")
                return assessment_data
            else:
                logger.warning(f"Could not extract assessment data from: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def parse_assessment_page(self, soup: BeautifulSoup, url: str) -> Optional[AssessmentData]:
        """Parse assessment details from BeautifulSoup object"""
        try:
            # Extract name
            name = self.extract_name(soup)
            if not name:
                return None
            
            # Extract description
            description = self.extract_description(soup)
            
            # Extract duration
            duration = self.extract_duration(soup)
            
            # Extract adaptive support
            adaptive_support = self.extract_adaptive_support(soup)
            
            # Extract remote support
            remote_support = self.extract_remote_support(soup)
            
            # Extract test types
            test_type = self.extract_test_types(soup)
            
            return AssessmentData(
                name=name,
                url=url,
                description=description,
                duration=duration,
                adaptive_support=adaptive_support,
                remote_support=remote_support,
                test_type=test_type
            )
            
        except Exception as e:
            logger.error(f"Error parsing assessment page: {e}")
            return None
    
    def extract_name(self, soup: BeautifulSoup) -> str:
        """Extract assessment name from the page"""
        selectors = [
            'h1', 'h1.title', '.product-title', '.assessment-title',
            '[data-testid="product-name"]', '.page-title', '.hero-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return "Unknown Assessment"
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract assessment description"""
        selectors = [
            '.description', '.product-description', '.assessment-description',
            '.overview', '.summary', '[data-testid="description"]',
            '.content p', '.hero-description', '.intro'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                text = element.get_text(strip=True)
                if len(text) > 50:  # Ensure it's substantial
                    return text
        
        # Fallback to first substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 100:
                return text
        
        return "No description available"
    
    def extract_duration(self, soup: BeautifulSoup) -> int:
        """Extract duration in minutes"""
        text = soup.get_text()
        
        # Look for duration patterns
        duration_patterns = [
            r'(\d+)\s*(?:min|minute|minutes)',
            r'Duration[:\s]+(\d+)',
            r'Time[:\s]+(\d+)',
            r'(\d+)\s*min'
        ]
        
        for pattern in duration_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except ValueError:
                    continue
        
        return 30  # Default duration
    
    def extract_adaptive_support(self, soup: BeautifulSoup) -> str:
        """Extract adaptive support information"""
        text = soup.get_text().lower()
        
        adaptive_keywords = ['adaptive', 'adapts', 'personalized', 'tailored']
        
        if any(keyword in text for keyword in adaptive_keywords):
            return "Yes"
        
        return "No"
    
    def extract_remote_support(self, soup: BeautifulSoup) -> str:
        """Extract remote support information"""
        text = soup.get_text().lower()
        
        remote_keywords = ['remote', 'online', 'virtual', 'web-based', 'digital']
        
        if any(keyword in text for keyword in remote_keywords):
            return "Yes"
        
        return "No"
    
    def extract_test_types(self, soup: BeautifulSoup) -> List[str]:
        """Extract test types from the page"""
        text = soup.get_text().lower()
        
        # Common test type categories
        type_mapping = {
            'knowledge': 'Knowledge & Skills',
            'skill': 'Knowledge & Skills',
            'cognitive': 'Ability & Aptitude',
            'ability': 'Ability & Aptitude',
            'aptitude': 'Ability & Aptitude',
            'personality': 'Personality & Behavior',
            'behavioral': 'Personality & Behavior',
            'behavior': 'Personality & Behavior',
            'psychometric': 'Ability & Aptitude',
            'numerical': 'Ability & Aptitude',
            'verbal': 'Ability & Aptitude',
            'logical': 'Ability & Aptitude'
        }
        
        detected_types = []
        for keyword, test_type in type_mapping.items():
            if keyword in text and test_type not in detected_types:
                detected_types.append(test_type)
        
        return detected_types if detected_types else ['General Assessment']
    
    def save_to_csv(self, filename: str = "shl_data_detailed.csv"):
        """Save scraped data to CSV file"""
        filepath = config.DATA_DIR / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'url', 'description', 'duration', 'adaptive_support', 'remote_support', 'test_type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for assessment in self.scraped_assessments:
                    writer.writerow({
                        'name': assessment.name,
                        'url': assessment.url,
                        'description': assessment.description,
                        'duration': assessment.duration,
                        'adaptive_support': assessment.adaptive_support,
                        'remote_support': assessment.remote_support,
                        'test_type': '|'.join(assessment.test_type)  # Join list with pipe separator
                    })
            
            logger.info(f"Saved {len(self.scraped_assessments)} assessments to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            raise
    
    def run_scraper(self) -> int:
        """Main scraper execution"""
        logger.info("Starting SHL catalog scraping...")
        
        try:
            # Setup WebDriver
            self.driver = self.setup_driver()
            
            # Load all product URLs
            product_urls = self.load_all_products()
            logger.info(f"Found {len(product_urls)} product URLs to scrape")
            
            if len(product_urls) < config.TARGET_COUNT:
                logger.warning(f"Only found {len(product_urls)} products, expected at least {config.TARGET_COUNT}")
            
            # Scrape each product
            for i, url in enumerate(product_urls, 1):
                logger.info(f"Scraping {i}/{len(product_urls)}: {url}")
                
                assessment_data = self.scrape_assessment_details(url)
                if assessment_data:
                    self.scraped_assessments.append(assessment_data)
                
                # Add delay between requests
                time.sleep(config.SCRAPING_DELAY)
                
                # Save progress every 50 items
                if i % 50 == 0:
                    logger.info(f"Progress: {i}/{len(product_urls)} - Saving checkpoint...")
                    self.save_to_csv(f"shl_data_checkpoint_{i}.csv")
            
            # Final save
            self.save_to_csv()
            
            logger.info(f"Scraping completed! Total assessments: {len(self.scraped_assessments)}")
            return len(self.scraped_assessments)
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return 0
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")

def main():
    """Main function to run the scraper"""
    scraper = SHLScraper()
    
    try:
        count = scraper.run_scraper()
        if count >= config.TARGET_COUNT:
            logger.info(f"✅ Success! Scraped {count} assessments (target: {config.TARGET_COUNT})")
        else:
            logger.warning(f"⚠️ Only scraped {count} assessments (target: {config.TARGET_COUNT})")
        
        return count
        
    except Exception as e:
        logger.error(f"❌ Scraper failed: {e}")
        return 0

if __name__ == "__main__":
    main()