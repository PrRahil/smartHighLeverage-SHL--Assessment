"""
FastAPI Backend for SHL GenAI Recommendation Engine
Provides API endpoints for health check and assessment recommendations
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from src.config import config
from src.models import (
    RecommendationRequest,
    RecommendationResponse,
    AssessmentRecommendation,
    HealthResponse
)
from src.rag_engine import initialize_rag_engine, get_recommendations
from src.enhanced_rag_engine import initialize_enhanced_rag_engine, get_enhanced_recommendations
from src.utils.helpers import setup_logging
from loguru import logger

# Global initialization flag
RAG_INITIALIZED = False
ENHANCED_RAG_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global RAG_INITIALIZED, ENHANCED_RAG_AVAILABLE

    # Startup
    logger.info("🚀 Starting SHL GenAI Recommendation Engine...")

    # Try to initialize enhanced RAG engine first
    logger.info("Initializing Enhanced RAG engine with training data...")
    ENHANCED_RAG_AVAILABLE = initialize_enhanced_rag_engine()
    
    if ENHANCED_RAG_AVAILABLE:
        logger.info("✅ Enhanced RAG engine initialized successfully")
        RAG_INITIALIZED = True
    else:
        # Fallback to standard RAG engine
        logger.warning("⚠️  Enhanced RAG failed, falling back to standard RAG...")
        RAG_INITIALIZED = initialize_rag_engine()
        
        if RAG_INITIALIZED:
            logger.info("✅ Standard RAG engine initialized successfully")
        else:
            logger.error("❌ Failed to initialize any RAG engine")

    yield

    # Shutdown
    logger.info("🔄 Shutting down SHL GenAI Recommendation Engine...")

# Create FastAPI app with lifecycle
app = FastAPI(
    title="SHL GenAI Recommendation Engine",
    description="API for recommending SHL Individual Test Solutions using RAG and Google Gemini",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="SHL GenAI Recommendation Engine",
        version="1.0.0",
        database_status="enhanced" if ENHANCED_RAG_AVAILABLE else ("connected" if RAG_INITIALIZED else "disconnected"),
        api_status="active"
    )

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend_assessments(request: RecommendationRequest):
    """
    Recommend SHL assessments based on user query

    Returns 5-10 recommended assessments with balance logic:
    - If query mentions both technical and soft skills, returns mix of test types
    - Strict JSON schema compliance as per requirements
    """

    if not RAG_INITIALIZED:
        logger.error("RAG engine not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available. Please try again later."
        )

    try:
        logger.info(f"Recommendation request: '{request.query}'")

        # Get recommendations from RAG engine (enhanced if available)
        if ENHANCED_RAG_AVAILABLE:
            logger.info("Using Enhanced RAG engine for recommendations")
            recommendations = get_enhanced_recommendations(request.query)
        else:
            logger.info("Using standard RAG engine for recommendations")
            recommendations = get_recommendations(request.query)

        if not recommendations:
            logger.warning(f"No recommendations found for query: '{request.query}'")
            return RecommendationResponse(recommended_assessments=[])

        # Convert Assessment objects to AssessmentRecommendation objects
        assessment_recommendations = []
        for i, assessment in enumerate(recommendations):
            # Determine test type from the test_type list
            test_type = assessment.test_type[0] if assessment.test_type else "General"

            # Use similarity score if available, otherwise assign based on ranking
            relevance_score = assessment.similarity_score if assessment.similarity_score else (1.0 - (i * 0.1))

            recommendation = AssessmentRecommendation(
                name=assessment.name,
                description=assessment.description,
                test_type=test_type,
                relevance_score=min(max(relevance_score, 0.0), 1.0),  # Clamp between 0.0 and 1.0
                url=assessment.url
            )
            assessment_recommendations.append(recommendation)

        logger.info(f"Returning {len(assessment_recommendations)} recommendations")
        return RecommendationResponse(recommended_assessments=assessment_recommendations)

    except Exception as e:
        logger.error(f"Error processing recommendation request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing recommendation"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

def main():
    """Main function to run the FastAPI server"""
    # Setup logging
    setup_logging()

    # Validate configuration
    try:
        config.validate_config()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.info("Please update your .env file with the required API keys")
        return

    # Run the server
    logger.info(f"Starting FastAPI server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main()
