"""
Evaluation script for generating submission CSV in stacked format
Reads test queries and generates recommendations using the RAG engine
"""

import pandas as pd
import csv
from pathlib import Path
import sys
from typing import List, Dict

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import config
from src.rag_engine import SHLRAGEngine
from src.utils.helpers import setup_logging
from loguru import logger

class SubmissionGenerator:
    """Generate submission CSV from test dataset"""
    
    def __init__(self):
        self.rag_engine = SHLRAGEngine()
        self.test_queries: List[str] = []
        self.submission_data: List[Dict[str, str]] = []
    
    def load_test_dataset(self, filename: str = "Gen_AI Dataset (2).xlsx") -> bool:
        """Load test queries from Excel file"""
        try:
            # Try different possible locations and names
            possible_paths = [
                config.DATA_DIR / filename,
                config.DATA_DIR / "Gen_AI_Dataset.xlsx",
                config.DATA_DIR / "test_queries.xlsx",
                config.DATA_DIR / "Test-Set.csv",
                config.BASE_DIR / filename,
                Path(filename)
            ]
            
            test_file = None
            for path in possible_paths:
                if path.exists():
                    test_file = path
                    break
            
            if not test_file:
                logger.warning(f"Test file not found. Creating sample queries...")
                # Create sample queries for demonstration
                self.test_queries = [
                    "I need assessments for software developers with strong programming skills",
                    "Find tests for leadership and management positions",
                    "Assessments for customer service representatives with communication skills",
                    "Technical tests for data analysts and Python programmers",
                    "Personality assessments for team collaboration and leadership",
                    "Cognitive ability tests for problem-solving roles",
                    "Skills assessment for Java developers and technical architects",
                    "Behavioral tests for sales and marketing professionals",
                    "Numerical reasoning tests for financial analysts",
                    "Communication and interpersonal skills assessments"
                ]
                logger.info(f"Created {len(self.test_queries)} sample queries")
                return True
            
            logger.info(f"Loading test queries from: {test_file}")
            
            # Load based on file extension
            if test_file.suffix.lower() == '.xlsx':
                df = pd.read_excel(test_file)
            elif test_file.suffix.lower() == '.csv':
                df = pd.read_csv(test_file)
            else:
                raise ValueError(f"Unsupported file format: {test_file.suffix}")
            
            # Extract queries - look for common column names
            query_columns = ['query', 'Query', 'question', 'Question', 'text', 'Text']
            query_column = None
            
            for col in query_columns:
                if col in df.columns:
                    query_column = col
                    break
            
            if query_column:
                self.test_queries = df[query_column].dropna().astype(str).tolist()
            else:
                # If no standard column found, use first column
                logger.warning("No standard query column found, using first column")
                self.test_queries = df.iloc[:, 0].dropna().astype(str).tolist()
            
            logger.info(f"Loaded {len(self.test_queries)} test queries")
            return True
            
        except Exception as e:
            logger.error(f"Error loading test dataset: {e}")
            return False
    
    def generate_recommendations(self) -> bool:
        """Generate recommendations for all test queries"""
        try:
            logger.info("Initializing RAG engine...")
            if not self.rag_engine.initialize():
                logger.error("Failed to initialize RAG engine")
                return False
            
            logger.info("Loading assessment data...")
            if not self.rag_engine.load_data():
                logger.error("Failed to load assessment data")
                return False
            
            logger.info(f"Generating recommendations for {len(self.test_queries)} queries...")
            
            for i, query in enumerate(self.test_queries, 1):
                logger.info(f"Processing query {i}/{len(self.test_queries)}: {query[:100]}...")
                
                try:
                    # Get recommendations
                    recommendations = self.rag_engine.recommend(query)
                    
                    # Convert to stacked format
                    for recommendation in recommendations:
                        self.submission_data.append({
                            "Query": query,
                            "Assessment_url": recommendation.url
                        })
                    
                    logger.debug(f"Added {len(recommendations)} recommendations for query {i}")
                    
                except Exception as e:
                    logger.error(f"Error processing query {i}: {e}")
                    continue
            
            logger.info(f"✅ Generated {len(self.submission_data)} total recommendations")
            return True
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return False
    
    def save_submission(self, filename: str = "submission.csv") -> bool:
        """Save submission data in stacked format"""
        try:
            output_path = config.DATA_DIR / filename
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Query', 'Assessment_url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(self.submission_data)
            
            logger.info(f"✅ Submission saved to: {output_path}")
            logger.info(f"Total entries: {len(self.submission_data)}")
            
            # Show sample of the data
            if self.submission_data:
                logger.info("Sample entries:")
                for i, entry in enumerate(self.submission_data[:3]):
                    logger.info(f"  {i+1}. Query: {entry['Query'][:50]}...")
                    logger.info(f"      URL: {entry['Assessment_url']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving submission: {e}")
            return False
    
    def run_evaluation(self, test_file: str = None) -> bool:
        """Main evaluation function"""
        logger.info("🔍 Starting evaluation and submission generation...")
        
        # Load test dataset
        if not self.load_test_dataset(test_file or "Gen_AI Dataset (2).xlsx"):
            logger.error("Failed to load test dataset")
            return False
        
        # Generate recommendations
        if not self.generate_recommendations():
            logger.error("Failed to generate recommendations")
            return False
        
        # Save submission
        if not self.save_submission():
            logger.error("Failed to save submission")
            return False
        
        logger.info("✅ Evaluation completed successfully!")
        return True

def main():
    """Main function"""
    # Setup logging
    setup_logging()
    
    # Create and run submission generator
    generator = SubmissionGenerator()
    
    # Check command line arguments for test file
    test_file = None
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        logger.info(f"Using test file: {test_file}")
    
    success = generator.run_evaluation(test_file)
    
    if success:
        print("\n" + "="*60)
        print("✅ Submission generation completed!")
        print(f"📄 Output file: {config.DATA_DIR}/submission.csv")
        print("📊 Format: Stacked CSV with Query,Assessment_url columns")
        print("="*60)
        return 0
    else:
        print("\n❌ Submission generation failed!")
        return 1

if __name__ == "__main__":
    exit(main())