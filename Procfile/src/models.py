"""
Pydantic models for the SHL GenAI Recommendation Engine
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Assessment(BaseModel):
    """Assessment data model for internal processing"""
    name: str = Field(..., description="Name of the assessment")
    url: str = Field(..., description="URL of the assessment")
    description: str = Field(..., description="Description of the assessment")
    duration: Union[str, int] = Field(..., description="Duration of the assessment")
    adaptive_support: Union[bool, str] = Field(..., description="Adaptive support availability")
    remote_support: Union[bool, str] = Field(..., description="Remote support availability")
    test_type: List[str] = Field(..., description="List of test types")
    similarity_score: Optional[float] = Field(None, description="Similarity score")


class ScrapedAssessment(BaseModel):
    """Model for scraped assessment data"""
    name: str = Field(..., description="Name of the assessment")
    url: str = Field(..., description="URL of the assessment")
    description: str = Field(..., description="Description of the assessment")
    duration: str = Field(..., description="Duration of the assessment")
    adaptive_support: Union[bool, str] = Field(..., description="Adaptive support availability")
    remote_support: Union[bool, str] = Field(..., description="Remote support availability")
    test_type: Union[List[str], str] = Field(..., description="Test types")


class RecommendationRequest(BaseModel):
    """Request model for assessment recommendations"""
    query: str = Field(..., description="The user query for assessment recommendations")


class AssessmentRecommendation(BaseModel):
    """Individual assessment recommendation"""
    name: str = Field(..., description="Name of the assessment")
    description: str = Field(..., description="Description of the assessment")
    test_type: str = Field(..., description="Type of test (technical/soft skills)")
    relevance_score: float = Field(..., description="Relevance score from 0.0 to 1.0")
    url: str = Field(..., description="Direct SHL URL to the assessment")


class RecommendationResponse(BaseModel):
    """Response model for assessment recommendations"""
    recommended_assessments: List[AssessmentRecommendation] = Field(
        default_factory=list,
        description="List of recommended assessments"
    )
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata about the recommendation process"
    )


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="ISO formatted timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    database_status: Optional[str] = Field(None, description="Database status")
    api_status: Optional[str] = Field(None, description="API status")
