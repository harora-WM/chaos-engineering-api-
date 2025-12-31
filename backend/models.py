"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class OpenSearchConfig(BaseModel):
    """OpenSearch connection configuration"""
    endpoint: str = Field(..., description="OpenSearch endpoint URL")
    username: str = Field(..., description="OpenSearch username")
    password: str = Field(..., description="OpenSearch password")


class AWSBedrockConfig(BaseModel):
    """AWS Bedrock configuration"""
    model: str = Field(
        default="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        description="Bedrock model ID"
    )
    region: str = Field(default="ap-south-1", description="AWS region")


class AnalysisOptions(BaseModel):
    """Options for chaos plan analysis"""
    focus: str = Field(default="All", description="Focus area for analysis")
    security: bool = Field(default=True, description="Include security analysis")
    include_external: bool = Field(default=True, description="Include external dependencies")


class TestConnectionRequest(BaseModel):
    """Request model for testing OpenSearch connection"""
    endpoint: str
    username: str
    password: str


class TestConnectionResponse(BaseModel):
    """Response model for connection test"""
    success: bool
    message: str


class GetIndicesRequest(BaseModel):
    """Request model for getting indices"""
    endpoint: str
    username: str
    password: str


class IndexInfo(BaseModel):
    """Information about an OpenSearch index"""
    index: str
    health: str
    status: str
    docs_count: Optional[str] = Field(None, alias="docs.count")
    store_size: Optional[str] = Field(None, alias="store.size")
    pri: Optional[str] = None
    rep: Optional[str] = None


class GetIndicesResponse(BaseModel):
    """Response model for getting indices"""
    success: bool
    indices: List[IndexInfo] = []
    error: Optional[str] = None


class FetchIndexDataRequest(BaseModel):
    """Request model for fetching index data"""
    endpoint: str
    username: str
    password: str
    index_name: str


class FetchIndexDataResponse(BaseModel):
    """Response model for fetching index data"""
    success: bool
    mapping: Optional[Dict[str, Any]] = None
    documents: Optional[Dict[str, Any]] = None
    sample_size: Optional[int] = None
    total_hits: Optional[int] = None
    took_ms: Optional[int] = None
    error: Optional[str] = None


class GeneratePlanRequest(BaseModel):
    """Request model for generating chaos plan"""
    index_name: str
    opensearch_config: OpenSearchConfig
    aws_config: AWSBedrockConfig
    analysis_options: Optional[AnalysisOptions] = AnalysisOptions()


class GeneratePlanResponse(BaseModel):
    """Response model for chaos plan generation"""
    success: bool
    plan: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
