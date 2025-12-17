"""
RAG (Retrieval Augmented Generation) Engine for SHL Assessment Recommendations
Uses ChromaDB for vector storage and Google Gemini for LLM refinement
"""

import pandas as pd
from typing import List, Dict, Optional
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from src.config import config
from src.models import Assessment, ScrapedAssessment
from loguru import logger

class SHLRAGEngine:
    """RAG Engine for SHL Assessment Recommendations"""
    
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.llm_model = None
        self.data_loaded = False
        
    def initialize(self) -> bool:
        """Initialize all components of the RAG engine"""
        try:
            # Initialize embedding model
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            
            # Initialize ChromaDB
            logger.info("Initializing ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(
                path=str(config.CHROMA_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(name="shl_assessments")
                logger.info("Using existing collection")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="shl_assessments",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Created new collection")
            
            # Initialize Google Gemini
            logger.info("Initializing Google Gemini...")
            if not config.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not configured")
                
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.llm_model = genai.GenerativeModel(config.LLM_MODEL)
            
            logger.info("✅ RAG engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG engine: {e}")
            return False
    
    def load_data(self, csv_file: str = "shl_data_detailed.csv") -> bool:
        """Load assessment data into ChromaDB"""
        try:
            csv_path = config.DATA_DIR / csv_file
            
            if not csv_path.exists():
                logger.error(f"Data file not found: {csv_path}")
                return False
            
            # Load CSV data
            logger.info(f"Loading data from {csv_path}")
            df = pd.read_csv(csv_path)
            
            # Check if data already exists in collection
            existing_count = self.collection.count()
            if existing_count > 0:
                logger.info(f"Collection already contains {existing_count} assessments")
                self.data_loaded = True
                return True
            
            # Prepare data for embedding
            logger.info(f"Processing {len(df)} assessments...")
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Create searchable document text
                test_types = row['test_type'].split('|') if pd.notna(row['test_type']) else []
                
                document_text = f"""
                Assessment: {row['name']}
                Description: {row['description']}
                Test Types: {', '.join(test_types)}
                Duration: {row['duration']} minutes
                Adaptive Support: {row['adaptive_support']}
                Remote Support: {row['remote_support']}
                """.strip()
                
                # Metadata for filtering and retrieval (ChromaDB only accepts scalar values)
                metadata = {
                    "name": str(row['name']),
                    "url": str(row['url']),
                    "description": str(row['description'])[:500],  # Truncate for metadata
                    "duration": int(row['duration']),
                    "adaptive_support": str(row['adaptive_support']),
                    "remote_support": str(row['remote_support']),
                    "test_type_str": str(row['test_type']),  # Store as string
                    "test_type_count": len(test_types)  # Number of test types
                }
                
                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(f"assessment_{idx}")
            
            # Add to ChromaDB in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_meta = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_meta,
                    ids=batch_ids
                )
                
                logger.debug(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            self.data_loaded = True
            logger.info(f"✅ Successfully loaded {len(documents)} assessments into ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return False
    
    def retrieve_assessments(self, query: str, k: int = None) -> List[Dict]:
        """Retrieve top-k assessments based on query"""
        if not self.data_loaded:
            raise RuntimeError("Data not loaded. Call load_data() first.")
        
        k = k or config.TOP_K_RETRIEVAL
        
        try:
            logger.debug(f"Retrieving top {k} assessments for query: '{query}'")
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            assessments = []
            for i, metadata in enumerate(results['metadatas'][0]):
                # Parse test types from stored string
                test_types_str = metadata.get("test_type_str", "")
                test_types = test_types_str.split('|') if test_types_str else []
                
                assessment = {
                    "name": metadata["name"],
                    "url": metadata["url"],
                    "description": metadata["description"],
                    "duration": metadata["duration"],
                    "adaptive_support": metadata["adaptive_support"],
                    "remote_support": metadata["remote_support"],
                    "test_type": test_types,
                    "similarity_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                assessments.append(assessment)
            
            logger.debug(f"Retrieved {len(assessments)} assessments")
            return assessments
            
        except Exception as e:
            logger.error(f"Error retrieving assessments: {e}")
            return []
    
    def refine_with_llm(self, query: str, candidate_assessments: List[Dict]) -> List[Assessment]:
        """Use Google Gemini to refine and select final recommendations"""
        try:
            logger.debug(f"Refining {len(candidate_assessments)} candidates with LLM")
            
            # Prepare context for LLM
            assessments_context = []
            for i, assessment in enumerate(candidate_assessments):
                context_item = {
                    "id": i + 1,
                    "name": assessment["name"],
                    "description": assessment["description"][:200] + "..." if len(assessment["description"]) > 200 else assessment["description"],
                    "test_type": assessment["test_type"],
                    "duration": assessment["duration"],
                    "adaptive_support": assessment["adaptive_support"],
                    "remote_support": assessment["remote_support"]
                }
                assessments_context.append(context_item)
            
            # Create system prompt with balance logic
            system_prompt = f"""You are an SHL Assessment Expert. The user query is: '{query}'.

INSTRUCTIONS:
1. Select exactly 5 to 10 assessments from the provided context that best match the user query.
2. BALANCE RULE: If the query mentions both technical skills (e.g., Java, Python, programming, technical) AND soft skills (e.g., communication, leadership, personality, teamwork), you MUST select a mix of:
   - 'Knowledge & Skills' tests (for technical skills)
   - 'Personality & Behavior' tests (for soft skills)
3. Consider relevance, test types, duration, and support features.
4. Return ONLY a JSON array of assessment IDs (numbers) that you select.
5. Do not include any explanations, just the JSON array.

AVAILABLE ASSESSMENTS:
{json.dumps(assessments_context, indent=2)}

Return format: [1, 3, 5, 7, 9]"""
            
            # Call Gemini
            response = self.llm_model.generate_content(system_prompt)
            
            # Parse response
            response_text = response.text.strip()
            logger.debug(f"LLM response: {response_text}")
            
            # Extract JSON array
            try:
                # Try to find JSON array in response
                start_bracket = response_text.find('[')
                end_bracket = response_text.rfind(']') + 1
                
                if start_bracket != -1 and end_bracket != -1:
                    json_str = response_text[start_bracket:end_bracket]
                    selected_ids = json.loads(json_str)
                else:
                    raise ValueError("No JSON array found in response")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Could not parse LLM response as JSON: {e}")
                # Fallback: select top assessments
                selected_ids = list(range(1, min(9, len(candidate_assessments) + 1)))
            
            # Build final recommendations
            final_assessments = []
            for selected_id in selected_ids:
                if 1 <= selected_id <= len(candidate_assessments):
                    assessment_data = candidate_assessments[selected_id - 1]
                    
                    assessment = Assessment(
                        url=assessment_data["url"],
                        name=assessment_data["name"],
                        adaptive_support=assessment_data["adaptive_support"],
                        description=assessment_data["description"],
                        duration=assessment_data["duration"],
                        remote_support=assessment_data["remote_support"],
                        test_type=assessment_data["test_type"]
                    )
                    final_assessments.append(assessment)
            
            logger.info(f"✅ LLM refined to {len(final_assessments)} final recommendations")
            return final_assessments
            
        except Exception as e:
            logger.error(f"Error in LLM refinement: {e}")
            # Fallback: return top assessments
            fallback_assessments = []
            for assessment_data in candidate_assessments[:config.FINAL_RECOMMENDATIONS]:
                assessment = Assessment(
                    url=assessment_data["url"],
                    name=assessment_data["name"],
                    adaptive_support=assessment_data["adaptive_support"],
                    description=assessment_data["description"],
                    duration=assessment_data["duration"],
                    remote_support=assessment_data["remote_support"],
                    test_type=assessment_data["test_type"]
                )
                fallback_assessments.append(assessment)
            
            return fallback_assessments
    
    def recommend(self, query: str) -> List[Assessment]:
        """Main recommendation function"""
        try:
            logger.info(f"Getting recommendations for: '{query}'")
            
            if not self.data_loaded:
                logger.warning("Data not loaded, attempting to load...")
                if not self.load_data():
                    raise RuntimeError("Failed to load assessment data")
            
            # Step 1: Retrieve top candidates
            candidates = self.retrieve_assessments(query, config.TOP_K_RETRIEVAL)
            
            if not candidates:
                logger.warning("No candidates retrieved")
                return []
            
            # Step 2: LLM refinement with balance logic
            recommendations = self.refine_with_llm(query, candidates)
            
            logger.info(f"✅ Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Recommendation failed: {e}")
            return []

# Global RAG engine instance
rag_engine = SHLRAGEngine()

def initialize_rag_engine() -> bool:
    """Initialize the global RAG engine instance"""
    return rag_engine.initialize()

def get_recommendations(query: str) -> List[Assessment]:
    """Get assessment recommendations for a query"""
    return rag_engine.recommend(query)