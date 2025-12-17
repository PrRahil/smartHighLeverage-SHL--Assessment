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

    def load_data(self, csv_file: str = "shl_test_table.csv") -> bool:
        """Load comprehensive test catalog data into ChromaDB"""
        try:
            csv_path = config.DATA_DIR / csv_file

            if not csv_path.exists():
                logger.error(f"Data file not found: {csv_path}")
                # Fallback to old data if new catalog not available
                fallback_path = config.DATA_DIR / "shl_data_detailed.csv"
                if fallback_path.exists():
                    logger.info("Using fallback data: shl_data_detailed.csv")
                    return self._load_legacy_data(fallback_path)
                return False

            # Load CSV data
            logger.info(f"Loading comprehensive test catalog from {csv_path}")
            df = pd.read_csv(csv_path)

            # Check if data already exists in collection
            existing_count = self.collection.count()
            if existing_count > 0:
                logger.info(f"Collection already contains {existing_count} assessments")
                # Check if we need to update with new data
                if len(df) > existing_count:
                    logger.info("New data available, refreshing collection...")
                    self.chroma_client.delete_collection(name="shl_assessments")
                    self.collection = self.chroma_client.create_collection(
                        name="shl_assessments",
                        metadata={"hnsw:space": "cosine"}
                    )
                else:
                    self.data_loaded = True
                    return True

            # Prepare comprehensive test data for embedding
            logger.info(f"Processing {len(df)} SHL tests from catalog...")
            documents = []
            metadatas = []
            ids = []

            # Define test type categories for better understanding
            test_type_mapping = {
                'K': 'Knowledge Test - Technical Skills',
                'KS': 'Knowledge & Skills Test - Practical Application',
                'P': 'Personality Assessment - Behavioral Traits',
                'BP': 'Behavioral & Personality - Job-Focused',
                'A': 'Ability Test - Cognitive Skills',
                'S': 'Skills Assessment - Job-Specific',
                'C': 'Competency Assessment - Leadership & Management',
                'CPAB': 'Comprehensive Assessment - Multiple Dimensions',
                'ABPS': 'Ability, Behavioral, Personality & Skills Package',
                'PSK': 'Personality, Skills & Knowledge Assessment',
                'ABP': 'Ability, Behavioral & Personality Assessment',
                'AKP': 'Ability, Knowledge & Personality Assessment',
                'ABKP': 'Comprehensive Multi-Domain Assessment',
                'BPSA': 'Behavioral, Personality, Skills & Ability Assessment',
                'BAP': 'Behavioral, Ability & Personality Assessment',
                'PSKBA': 'Complete Professional Assessment Battery',
                'AEBCDP': 'Advanced Executive & Business Capability Assessment'
            }

            for idx, row in df.iterrows():
                # Skip header row if it exists in data
                if row['name'] == 'Pre-packaged Job Solutions' and row['test_type'] == 'Test Type':
                    continue

                # Get test type description
                test_type_code = str(row['test_type']).strip() if pd.notna(row['test_type']) else 'Unknown'
                test_type_desc = test_type_mapping.get(test_type_code, f'Assessment Type: {test_type_code}')

                # Extract domain from test name for better categorization
                name = str(row['name']).strip()
                domain = self._extract_domain(name)

                # Create comprehensive searchable document text
                document_text = f"""
                Assessment: {name}
                Domain: {domain}
                Type: {test_type_desc}
                Test Code: {test_type_code}
                URL: {row['url']}
                Remote Testing: {row['remote_testing'] if pd.notna(row['remote_testing']) and row['remote_testing'] else 'Not specified'}
                Adaptive/IRT: {row['adaptive_irt'] if pd.notna(row['adaptive_irt']) and row['adaptive_irt'] else 'Not specified'}
                Page Number: {row['page_number']}

                Assessment Details:
                This is a {test_type_desc.lower()} focusing on {domain.lower()} skills and capabilities.
                """.strip()

                # Metadata for filtering and retrieval
                metadata = {
                    "name": name,
                    "url": str(row['url']) if pd.notna(row['url']) else "",
                    "test_type": test_type_code,
                    "test_type_desc": test_type_desc[:200],  # Truncate for metadata
                    "domain": domain,
                    "remote_testing": str(row['remote_testing']) if pd.notna(row['remote_testing']) else "",
                    "adaptive_irt": str(row['adaptive_irt']) if pd.notna(row['adaptive_irt']) else "",
                    "page_number": int(row['page_number']) if pd.notna(row['page_number']) else 0,
                    "is_technical": 1 if any(keyword in name.lower() for keyword in
                                           ['programming', 'java', 'python', 'sql', 'javascript', 'development',
                                            'engineering', 'software', 'coding', 'technical', 'data', 'cloud']) else 0,
                    "is_behavioral": 1 if test_type_code in ['P', 'BP', 'OPQ'] else 0,
                    "is_skills": 1 if test_type_code in ['K', 'KS', 'S'] else 0
                }

                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(f"shl_test_{idx}")

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
            logger.info(f"✅ Successfully loaded {len(documents)} SHL tests into ChromaDB")
            logger.info(f"📊 Data includes: Technical({sum(m['is_technical'] for m in metadatas)}), "
                       f"Behavioral({sum(m['is_behavioral'] for m in metadatas)}), "
                       f"Skills({sum(m['is_skills'] for m in metadatas)}) assessments")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load test catalog data: {e}")
            return False

    def _extract_domain(self, test_name: str) -> str:
        """Extract domain/category from test name"""
        name_lower = test_name.lower()

        # Technical domains
        if any(word in name_lower for word in ['java', 'python', 'javascript', 'sql', 'programming', 'coding']):
            return 'Programming & Development'
        elif any(word in name_lower for word in ['engineering', 'mechanical', 'electrical', 'chemical']):
            return 'Engineering'
        elif any(word in name_lower for word in ['data', 'analytics', 'statistics', 'science']):
            return 'Data & Analytics'
        elif any(word in name_lower for word in ['microsoft', 'excel', 'word', 'powerpoint', 'office']):
            return 'Microsoft Office & Productivity'
        elif any(word in name_lower for word in ['cloud', 'aws', 'azure', 'devops']):
            return 'Cloud & Infrastructure'
        elif any(word in name_lower for word in ['sales', 'customer', 'service', 'marketing']):
            return 'Sales & Customer Service'
        elif any(word in name_lower for word in ['management', 'leadership', 'manager', 'executive']):
            return 'Leadership & Management'
        elif any(word in name_lower for word in ['personality', 'behavioral', 'motivation', 'opq']):
            return 'Personality & Behavior'
        elif any(word in name_lower for word in ['numerical', 'verbal', 'reasoning', 'ability', 'cognitive']):
            return 'Cognitive Abilities'
        elif any(word in name_lower for word in ['medical', 'healthcare', 'nursing', 'pharmaceutical']):
            return 'Healthcare & Medical'
        elif any(word in name_lower for word in ['finance', 'accounting', 'banking', 'financial']):
            return 'Finance & Accounting'
        else:
            return 'General Assessment'

    def _load_legacy_data(self, csv_path: Path) -> bool:
        """Load legacy data format as fallback"""
        try:
            logger.info(f"Loading legacy data from {csv_path}")
            df = pd.read_csv(csv_path)

            documents = []
            metadatas = []
            ids = []

            for idx, row in df.iterrows():
                test_types = row['test_type'].split('|') if pd.notna(row['test_type']) else []

                document_text = f"""
                Assessment: {row['name']}
                Description: {row['description']}
                Test Types: {', '.join(test_types)}
                Duration: {row['duration']} minutes
                Adaptive Support: {row['adaptive_support']}
                Remote Support: {row['remote_support']}
                """.strip()

                metadata = {
                    "name": str(row['name']),
                    "url": str(row['url']),
                    "description": str(row['description'])[:500],
                    "duration": int(row['duration']),
                    "adaptive_support": str(row['adaptive_support']),
                    "remote_support": str(row['remote_support']),
                    "test_type_str": str(row['test_type']),
                    "test_type_count": len(test_types)
                }

                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(f"legacy_assessment_{idx}")

            # Add to ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            self.data_loaded = True
            logger.info(f"✅ Successfully loaded {len(documents)} legacy assessments")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load legacy data: {e}")
            return False

    def retrieve_assessments(self, query: str, k: int = None) -> List[Dict]:
        """Retrieve top-k assessments based on query from comprehensive test catalog"""
        if not self.data_loaded:
            raise RuntimeError("Data not loaded. Call load_data() first.")

        k = k or config.TOP_K_RETRIEVAL

        try:
            logger.debug(f"Retrieving top {k} assessments for query: '{query}'")

            # Query ChromaDB with comprehensive catalog data
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )

            # Format results for new test catalog structure
            assessments = []
            for i, metadata in enumerate(results['metadatas'][0]):
                # Handle both new catalog format and legacy format
                if "test_type_desc" in metadata:  # New catalog format
                    assessment = {
                        "name": metadata["name"],
                        "url": metadata["url"],
                        "description": metadata.get("test_type_desc", "SHL Assessment"),
                        "test_type": metadata.get("test_type", "Unknown"),
                        "domain": metadata.get("domain", "General"),
                        "remote_testing": metadata.get("remote_testing", "Not specified"),
                        "adaptive_irt": metadata.get("adaptive_irt", "Not specified"),
                        "page_number": metadata.get("page_number", 0),
                        "is_technical": bool(metadata.get("is_technical", 0)),
                        "is_behavioral": bool(metadata.get("is_behavioral", 0)),
                        "is_skills": bool(metadata.get("is_skills", 0)),
                        "similarity_score": 1 - results['distances'][0][i]
                    }
                else:  # Legacy format
                    test_types_str = metadata.get("test_type_str", "")
                    test_types = test_types_str.split('|') if test_types_str else []

                    assessment = {
                        "name": metadata["name"],
                        "url": metadata["url"],
                        "description": metadata.get("description", ""),
                        "duration": metadata.get("duration", 0),
                        "adaptive_support": metadata.get("adaptive_support", ""),
                        "remote_support": metadata.get("remote_support", ""),
                        "test_type": test_types,
                        "similarity_score": 1 - results['distances'][0][i]
                    }

                assessments.append(assessment)

            logger.debug(f"Retrieved {len(assessments)} assessments from catalog")
            return assessments

        except Exception as e:
            logger.error(f"Error retrieving assessments: {e}")
            return []

    def refine_with_llm(self, query: str, candidate_assessments: List[Dict]) -> List[Assessment]:
        """Use Google Gemini to refine and select final recommendations"""
        try:
            logger.debug(f"Refining {len(candidate_assessments)} candidates with LLM")

            # Prepare context for LLM - handle both catalog and legacy formats
            assessments_context = []
            for i, assessment in enumerate(candidate_assessments):
                # Handle new catalog format
                if "domain" in assessment:
                    context_item = {
                        "id": i + 1,
                        "name": assessment["name"],
                        "description": assessment.get("description", "SHL Assessment"),
                        "domain": assessment.get("domain", "General"),
                        "test_type": assessment.get("test_type", "Unknown"),
                        "is_technical": assessment.get("is_technical", False),
                        "is_behavioral": assessment.get("is_behavioral", False),
                        "is_skills": assessment.get("is_skills", False),
                        "remote_testing": assessment.get("remote_testing", "Not specified"),
                        "adaptive_irt": assessment.get("adaptive_irt", "Not specified"),
                        "similarity_score": round(assessment.get("similarity_score", 0), 3)
                    }
                else:
                    # Handle legacy format
                    context_item = {
                        "id": i + 1,
                        "name": assessment["name"],
                        "description": assessment["description"][:200] + "..." if len(assessment.get("description", "")) > 200 else assessment.get("description", ""),
                        "test_type": assessment.get("test_type", []),
                        "duration": assessment.get("duration", 0),
                        "adaptive_support": assessment.get("adaptive_support", ""),
                        "remote_support": assessment.get("remote_support", ""),
                        "similarity_score": round(assessment.get("similarity_score", 0), 3)
                    }
                assessments_context.append(context_item)

            # Create enhanced system prompt for comprehensive catalog
            system_prompt = f"""You are an SHL Assessment Expert analyzing a comprehensive catalog of 389+ SHL tests. The user query is: '{query}'.

STRICT SELECTION REQUIREMENTS:
1. MANDATORY: Select EXACTLY between 5 and 10 assessments - NO MORE, NO LESS
2. STRICTLY ENFORCE: Your response MUST contain minimum 5 assessments and maximum 10 assessments
3. BALANCE RULE: For mixed queries (technical + soft skills), select:
   - Technical tests (test_type: K, KS) for programming, software, engineering skills
   - Behavioral tests (test_type: P, BP, OPQ) for personality, leadership, communication
   - Skills tests (test_type: S, CPAB) for job-specific competencies
4. Prioritize by similarity_score and domain relevance
5. Consider remote_testing and adaptive_irt capabilities if mentioned in query
6. CRITICAL: Return ONLY a JSON array of assessment IDs with 5-10 items ONLY

TEST TYPE GUIDE:
- K: Knowledge Tests (technical skills, programming, software)
- KS: Knowledge & Skills (practical application)
- P: Personality Assessment (behavioral traits, motivation)
- BP: Behavioral & Personality (job-focused behavior)
- S: Skills Assessment (job-specific skills)
- C: Competency Assessment (leadership, management)
- Multi-letter codes: Comprehensive packages

AVAILABLE ASSESSMENTS:
{json.dumps(assessments_context, indent=2)}

MANDATORY RESPONSE FORMAT: 
- Return exactly 5-10 assessment IDs in JSON array format
- Example for 7 recommendations: [1, 3, 5, 7, 9, 11, 13]
- Example for 5 recommendations: [2, 4, 6, 8, 10]
- NEVER return less than 5 or more than 10 IDs"""

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
                # Fallback: select top 7 assessments (within 5-10 range)
                selected_ids = list(range(1, min(8, len(candidate_assessments) + 1)))

            # STRICT VALIDATION: Ensure 5-10 recommendations
            if len(selected_ids) < 5:
                logger.warning(f"LLM returned only {len(selected_ids)} recommendations, expanding to minimum 5")
                # Add more assessments to reach minimum 5
                additional_needed = 5 - len(selected_ids)
                available_ids = [i for i in range(1, len(candidate_assessments) + 1) if i not in selected_ids]
                selected_ids.extend(available_ids[:additional_needed])
            elif len(selected_ids) > 10:
                logger.warning(f"LLM returned {len(selected_ids)} recommendations, limiting to maximum 10")
                # Limit to first 10 assessments
                selected_ids = selected_ids[:10]
            
            logger.info(f"Final selection: {len(selected_ids)} recommendations (enforced 5-10 range)")

            # Build final recommendations - handle both catalog and legacy formats
            final_assessments = []
            for selected_id in selected_ids:
                if 1 <= selected_id <= len(candidate_assessments):
                    assessment_data = candidate_assessments[selected_id - 1]

                    # Handle new catalog format
                    if "domain" in assessment_data:
                        assessment = Assessment(
                            url=assessment_data["url"],
                            name=assessment_data["name"],
                            adaptive_support=assessment_data.get("adaptive_irt", "Not specified"),
                            description=f"{assessment_data.get('domain', 'General')} - {assessment_data.get('description', 'SHL Assessment')}",
                            duration=60,  # Default duration for catalog items
                            remote_support=assessment_data.get("remote_testing", "Not specified"),
                            test_type=[assessment_data.get("test_type", "Unknown")] if isinstance(assessment_data.get("test_type", "Unknown"), str) else assessment_data.get("test_type", ["Unknown"]),
                            similarity_score=assessment_data.get("similarity_score", 0)
                        )
                    else:
                        # Handle legacy format
                        assessment = Assessment(
                            url=assessment_data["url"],
                            name=assessment_data["name"],
                            adaptive_support=assessment_data.get("adaptive_support", ""),
                            description=assessment_data.get("description", ""),
                            duration=assessment_data.get("duration", 0),
                            remote_support=assessment_data.get("remote_support", ""),
                            test_type=assessment_data.get("test_type", []),
                            similarity_score=assessment_data.get("similarity_score", 0)
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

            # Step 2: LLM refinement with balance logic (with fallback)
            try:
                recommendations = self.refine_with_llm(query, candidates)
            except Exception as llm_error:
                logger.warning(f"LLM refinement failed: {llm_error}, using fallback")
                recommendations = self.fallback_recommendations(candidates, query)

            logger.info(f"✅ Generated {len(recommendations)} recommendations")
            return recommendations

        except Exception as e:
            logger.error(f"❌ Recommendation failed: {e}")
            return []
    
    def fallback_recommendations(self, candidates, query):
        """Fallback recommendation method when LLM is unavailable"""
        from src.models import Assessment
        
        logger.info("Using fallback recommendation logic")
        
        # Simple rule-based selection
        recommendations = []
        query_lower = query.lower()
        
        # Categorize query
        is_technical = any(word in query_lower for word in 
                          ['java', 'python', 'programming', 'software', 'technical', 'code', 'development'])
        is_behavioral = any(word in query_lower for word in 
                           ['leadership', 'management', 'communication', 'personality', 'behavior'])
        
        # Select top candidates with balance
        selected = []
        technical_count = 0
        behavioral_count = 0
        
        for candidate in candidates[:15]:  # Consider top 15 candidates
            # Handle both catalog and legacy format
            if "domain" in candidate:
                # New catalog format
                is_tech_test = candidate.get("is_technical", False)
                is_behav_test = candidate.get("is_behavioral", False)
                
                # Balance selection
                if is_technical and is_behavioral:
                    if (is_tech_test and technical_count < 4) or (is_behav_test and behavioral_count < 4):
                        selected.append(candidate)
                        if is_tech_test:
                            technical_count += 1
                        if is_behav_test:
                            behavioral_count += 1
                elif is_technical and is_tech_test:
                    selected.append(candidate)
                    technical_count += 1
                elif is_behavioral and is_behav_test:
                    selected.append(candidate)
                    behavioral_count += 1
                else:
                    # General case - take top candidates
                    selected.append(candidate)
                
                if len(selected) >= 10:  # Maximum limit
                    break
            else:
                # Legacy format - just take top candidates
                selected.append(candidate)
                if len(selected) >= 10:  # Maximum limit
                    break
        
        # Convert to Assessment objects
        for candidate in selected:
            if "domain" in candidate:
                # New catalog format
                assessment = Assessment(
                    url=candidate["url"],
                    name=candidate["name"],
                    adaptive_support=candidate.get("adaptive_irt", "Not specified"),
                    description=f"{candidate.get('domain', 'General')} - {candidate.get('description', 'SHL Assessment')}",
                    duration=60,
                    remote_support=candidate.get("remote_testing", "Not specified"),
                    test_type=[candidate.get("test_type", "Unknown")] if isinstance(candidate.get("test_type", "Unknown"), str) else candidate.get("test_type", ["Unknown"]),
                    similarity_score=candidate.get("similarity_score", 0)
                )
            else:
                # Legacy format
                assessment = Assessment(
                    url=candidate["url"],
                    name=candidate["name"],
                    adaptive_support=candidate.get("adaptive_support", ""),
                    description=candidate.get("description", ""),
                    duration=candidate.get("duration", 0),
                    remote_support=candidate.get("remote_support", ""),
                    test_type=candidate.get("test_type", []),
                    similarity_score=candidate.get("similarity_score", 0)
                )
            recommendations.append(assessment)
        
        # STRICT VALIDATION: Ensure 5-10 recommendations for fallback too
        if len(recommendations) < 5:
            logger.warning(f"Fallback generated only {len(recommendations)} recommendations, need minimum 5")
            # Add more assessments from remaining candidates to reach minimum 5
            additional_needed = 5 - len(recommendations)
            remaining_candidates = candidates[len(selected):len(selected)+additional_needed]
            
            for candidate in remaining_candidates:
                if "domain" in candidate:
                    assessment = Assessment(
                        url=candidate["url"],
                        name=candidate["name"],
                        adaptive_support=candidate.get("adaptive_irt", "Not specified"),
                        description=f"{candidate.get('domain', 'General')} - {candidate.get('description', 'SHL Assessment')}",
                        duration=60,
                        remote_support=candidate.get("remote_testing", "Not specified"),
                        test_type=[candidate.get("test_type", "Unknown")] if isinstance(candidate.get("test_type", "Unknown"), str) else candidate.get("test_type", ["Unknown"]),
                        similarity_score=candidate.get("similarity_score", 0)
                    )
                else:
                    assessment = Assessment(
                        url=candidate["url"],
                        name=candidate["name"],
                        adaptive_support=candidate.get("adaptive_support", ""),
                        description=candidate.get("description", ""),
                        duration=candidate.get("duration", 0),
                        remote_support=candidate.get("remote_support", ""),
                        test_type=candidate.get("test_type", []),
                        similarity_score=candidate.get("similarity_score", 0)
                    )
                recommendations.append(assessment)
        elif len(recommendations) > 10:
            logger.warning(f"Fallback generated {len(recommendations)} recommendations, limiting to maximum 10")
            recommendations = recommendations[:10]
        
        logger.info(f"Fallback generated {len(recommendations)} recommendations (enforced 5-10 range)")
        return recommendations

# Global RAG engine instance
rag_engine = SHLRAGEngine()

def initialize_rag_engine() -> bool:
    """Initialize the global RAG engine instance"""
    return rag_engine.initialize()

def get_recommendations(query: str) -> List[Assessment]:
    """Get assessment recommendations for a query"""
    return rag_engine.recommend(query)
