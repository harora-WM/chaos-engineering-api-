"""FastAPI application for Chaos Engineering Plan Generator"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import AsyncIterator
import logging

from .config import settings
from .models import (
    TestConnectionRequest,
    TestConnectionResponse,
    GetIndicesRequest,
    GetIndicesResponse,
    FetchIndexDataRequest,
    FetchIndexDataResponse,
    GeneratePlanRequest,
    GeneratePlanResponse,
    HealthResponse,
    IndexInfo
)
from .clients import OpenSearchClient, LLMClient, ChaosPlanGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        message="Chaos Engineering Plan Generator API is running"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="API is operational"
    )


@app.post("/api/opensearch/test-connection", response_model=TestConnectionResponse)
async def test_opensearch_connection(request: TestConnectionRequest):
    """Test OpenSearch connection"""
    try:
        client = OpenSearchClient(
            endpoint=request.endpoint,
            username=request.username,
            password=request.password
        )
        success, message = client.test_connection()
        return TestConnectionResponse(success=success, message=message)
    except Exception as e:
        logger.error(f"Error testing OpenSearch connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/opensearch/indices", response_model=GetIndicesResponse)
async def get_opensearch_indices(request: GetIndicesRequest):
    """Get all OpenSearch indices"""
    try:
        client = OpenSearchClient(
            endpoint=request.endpoint,
            username=request.username,
            password=request.password
        )
        indices_data = client.get_indices()

        # Convert to IndexInfo models
        indices = [IndexInfo(**index) for index in indices_data]

        return GetIndicesResponse(success=True, indices=indices)
    except Exception as e:
        logger.error(f"Error getting indices: {str(e)}")
        return GetIndicesResponse(success=False, error=str(e))


@app.post("/api/opensearch/fetch-data", response_model=FetchIndexDataResponse)
async def fetch_index_data(request: FetchIndexDataRequest):
    """Fetch data from a specific index"""
    try:
        client = OpenSearchClient(
            endpoint=request.endpoint,
            username=request.username,
            password=request.password
        )
        index_data = client.get_index_data(request.index_name)

        if index_data.get("success"):
            return FetchIndexDataResponse(
                success=True,
                mapping=index_data.get("mapping"),
                documents=index_data.get("documents"),
                sample_size=index_data.get("sample_size"),
                total_hits=index_data.get("total_hits"),
                took_ms=index_data.get("took_ms")
            )
        else:
            return FetchIndexDataResponse(
                success=False,
                error=index_data.get("error", "Unknown error")
            )
    except Exception as e:
        logger.error(f"Error fetching index data: {str(e)}")
        return FetchIndexDataResponse(success=False, error=str(e))


@app.post("/api/bedrock/test-connection", response_model=TestConnectionResponse)
async def test_bedrock_connection(aws_config: dict):
    """Test AWS Bedrock connection"""
    try:
        model = aws_config.get("model", settings.BEDROCK_MODEL_ID)
        region = aws_config.get("region", settings.AWS_REGION)

        client = LLMClient(model=model, region=region)
        success, message = client.test_connection()
        return TestConnectionResponse(success=success, message=message)
    except Exception as e:
        logger.error(f"Error testing Bedrock connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chaos/generate", response_model=GeneratePlanResponse)
async def generate_chaos_plan(request: GeneratePlanRequest):
    """Generate chaos engineering plan (non-streaming)"""
    try:
        # Create clients
        os_client = OpenSearchClient(
            endpoint=request.opensearch_config.endpoint,
            username=request.opensearch_config.username,
            password=request.opensearch_config.password
        )

        llm_client = LLMClient(
            model=request.aws_config.model,
            region=request.aws_config.region
        )

        # Fetch index data
        index_data = os_client.get_index_data(request.index_name)

        if not index_data.get("success"):
            return GeneratePlanResponse(
                success=False,
                error=f"Failed to fetch index data: {index_data.get('error')}"
            )

        # Generate chaos plan
        generator = ChaosPlanGenerator(os_client, llm_client)
        plan, metrics = generator.generate_plan(
            index_name=request.index_name,
            index_data=index_data,
            analysis_options=request.analysis_options.model_dump()
        )

        if metrics.get("success"):
            return GeneratePlanResponse(
                success=True,
                plan=plan,
                metrics=metrics
            )
        else:
            return GeneratePlanResponse(
                success=False,
                error=metrics.get("error", "Unknown error during generation")
            )

    except Exception as e:
        logger.error(f"Error generating chaos plan: {str(e)}")
        return GeneratePlanResponse(success=False, error=str(e))


async def plan_generator_stream(request: GeneratePlanRequest) -> AsyncIterator[str]:
    """Async generator for streaming chaos plan"""
    try:
        # Create clients
        os_client = OpenSearchClient(
            endpoint=request.opensearch_config.endpoint,
            username=request.opensearch_config.username,
            password=request.opensearch_config.password
        )

        llm_client = LLMClient(
            model=request.aws_config.model,
            region=request.aws_config.region
        )

        # Fetch index data
        index_data = os_client.get_index_data(request.index_name)

        if not index_data.get("success"):
            yield f"data: {{\"error\": \"Failed to fetch index data: {index_data.get('error')}\"}}\n\n"
            return

        # Generate chaos plan with streaming
        generator = ChaosPlanGenerator(os_client, llm_client)

        for chunk in generator.generate_plan_streaming(
            index_name=request.index_name,
            index_data=index_data,
            analysis_options=request.analysis_options.model_dump()
        ):
            # Send as Server-Sent Events format
            yield f"data: {chunk}\n\n"

    except Exception as e:
        logger.error(f"Error in streaming chaos plan: {str(e)}")
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"


@app.post("/api/chaos/generate-stream")
async def generate_chaos_plan_stream(request: GeneratePlanRequest):
    """Generate chaos engineering plan with streaming response"""
    return StreamingResponse(
        plan_generator_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
