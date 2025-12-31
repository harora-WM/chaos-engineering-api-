# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Chaos Engineering Plan Generator** that analyzes application logs from OpenSearch and uses AWS Bedrock (Claude) to generate comprehensive chaos engineering test plans.

The application is now available in **two modes**:
1. **Streamlit Web UI** (`chaos_code.py`) - Interactive web interface
2. **FastAPI REST API** (`backend/`) - API for integration with other platforms

## Architecture

### New FastAPI Backend Structure

```
chaos_deploy/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with all endpoints
│   ├── models.py            # Pydantic request/response models
│   ├── config.py            # Configuration and environment variables
│   └── clients/
│       ├── __init__.py
│       ├── opensearch_client.py    # OpenSearch operations
│       ├── llm_client.py           # AWS Bedrock/LLM operations
│       └── chaos_generator.py      # Chaos plan generation logic
├── chaos_code.py            # Original Streamlit UI
├── requirements-api.txt     # Backend dependencies (minimal)
├── requirements.txt         # Full dependencies (includes Streamlit)
├── Dockerfile              # Container for FastAPI backend
└── .env                    # Environment variables
```

### Core Components

All three core classes have been extracted into separate modules in `backend/clients/`:

1. **OpenSearchClient** (`backend/clients/opensearch_client.py`)
   - Handles all OpenSearch operations (connection testing, index listing, data retrieval)
   - Uses requests library with basic auth
   - Fetches up to 10,000 documents per query for analysis
   - Methods: `test_connection()`, `get_indices()`, `get_index_data()`

2. **LLMClient** (`backend/clients/llm_client.py`)
   - Manages AWS Bedrock API interactions
   - Supports both standard and streaming responses
   - Default model: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`
   - Implements retry logic (3 attempts with exponential backoff)
   - Methods: `test_connection()`, `analyze_with_bedrock()`, `analyze_with_bedrock_streaming()`

3. **ChaosPlanGenerator** (`backend/clients/chaos_generator.py`)
   - Orchestrates the chaos plan generation workflow
   - Creates detailed prompts with log samples and failure scenario references
   - Generates 4 chaos scenarios covering: component failures, stress conditions, network conditions, and dependencies
   - Methods: `generate_plan()`, `generate_plan_streaming()`, `_create_prompt()`

## Running the Application

### Option 1: Streamlit UI (Original)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run chaos_code.py

# Available at http://localhost:8501
```

### Option 2: FastAPI Backend

```bash
# Install minimal dependencies
pip install -r requirements-api.txt

# Run the FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Option 3: Docker Container

```bash
# Build the Docker image
docker build -t chaos-api .

# Run the container
docker run -p 8000:8000 --env-file .env chaos-api

# API available at http://localhost:8000
```

## FastAPI Endpoints

### Health & Status
- `GET /` - Root endpoint with API info
- `GET /health` - Health check

### OpenSearch Operations
- `POST /api/opensearch/test-connection` - Test OpenSearch connection
- `POST /api/opensearch/indices` - Get all indices
- `POST /api/opensearch/fetch-data` - Fetch data from specific index

### AWS Bedrock Operations
- `POST /api/bedrock/test-connection` - Test AWS Bedrock connection

### Chaos Plan Generation
- `POST /api/chaos/generate` - Generate chaos plan (non-streaming)
- `POST /api/chaos/generate-stream` - Generate chaos plan with Server-Sent Events streaming

### Example API Request

```bash
curl -X POST "http://localhost:8000/api/chaos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "logs-2024",
    "opensearch_config": {
      "endpoint": "http://your-opensearch:9200",
      "username": "admin",
      "password": "your-password"
    },
    "aws_config": {
      "model": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
      "region": "ap-south-1"
    },
    "analysis_options": {
      "focus": "All",
      "security": true,
      "include_external": true
    }
  }'
```

## Environment Configuration

Create a `.env` file in the project root:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# CORS Settings (optional)
CORS_ORIGINS=*

# Default OpenSearch (optional)
DEFAULT_OPENSEARCH_ENDPOINT=
DEFAULT_OPENSEARCH_USERNAME=
DEFAULT_OPENSEARCH_PASSWORD=
```

## Deployment

### Deploy to Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/chaos-api

# Deploy to Cloud Run
gcloud run deploy chaos-api \
  --image gcr.io/PROJECT_ID/chaos-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AWS_ACCESS_KEY_ID=xxx,AWS_SECRET_ACCESS_KEY=xxx
```

### Deploy to Render

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements-api.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env` file

### Deploy to AWS ECS/Fargate

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ECR_URI
docker tag chaos-api:latest ECR_URI/chaos-api:latest
docker push ECR_URI/chaos-api:latest

# Deploy to ECS (configure task definition and service)
```

## Key Features

### Chaos Plan Generation Process

The chaos plan follows a structured 4-step analysis:

1. **Log & Topology Analysis** - Parse logs to identify service dependencies, IPs, ports, FQDNs, and communication patterns
2. **Entity Identification** - Classify infrastructure as Kubernetes pods, VMs, AWS resources, Azure resources, or GCP resources
3. **Cross-Reference Failure Modes** - Map entities to applicable failure scenarios from comprehensive reference tables
4. **Generate Chaos Plan** - Create 4 detailed scenarios with hypothesis, metrics, injection methods, propagation paths, and rollback criteria

### Failure Scenario Coverage

The prompt includes comprehensive failure reference tables for:
- **VMs** (Linux/Windows): Component failures, stress conditions, network conditions, user-related, internal failures, batch-related
- **Kubernetes/OpenShift**: Pod failures, service endpoints, node operations, scaling scenarios, network policies
- **AWS**: EC2, EKS, RDS, Lambda, ASG, S3, DynamoDB, ECS, ElastiCache, ELB, EMR, IAM
- **Azure**: VM, VMSS, WebApp, AKS
- **GCP**: Compute Engine, Cloud Storage, Cloud SQL, GKE

## Integration with Frontend Platforms

The FastAPI backend enables seamless integration:

### From React/Vue/Angular Frontend

```javascript
const response = await fetch('https://your-api.com/api/chaos/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    index_name: "logs-2024",
    opensearch_config: { /* ... */ },
    aws_config: { /* ... */ },
    analysis_options: { /* ... */ }
  })
});

const result = await response.json();
console.log(result.plan);
```

### From Mobile Apps (iOS/Android)

Use standard HTTP client libraries to call the same endpoints.

### From CLI Tools

```bash
# Using curl or any HTTP client
curl -X POST https://your-api.com/api/chaos/generate -d @request.json
```

## Important Implementation Details

### Streaming Support

Both Streamlit and FastAPI support streaming responses:
- **Streamlit**: Uses `st.write_stream()` with generator from `generate_plan_streaming()`
- **FastAPI**: Uses `StreamingResponse` with Server-Sent Events format

### Error Handling

- OpenSearch client: Basic exception handling with user-facing error messages
- LLM client: 3-retry logic with exponential backoff
- FastAPI: Returns structured error responses with appropriate HTTP status codes

### CORS Configuration

CORS is enabled in FastAPI to allow cross-origin requests. Configure allowed origins via `CORS_ORIGINS` environment variable.

## Modifying the Prompt

The chaos plan prompt is in `backend/clients/chaos_generator.py` in the `_create_prompt()` method. This is a comprehensive 400+ line prompt that defines:
- Output format and structure
- Analysis methodology
- Failure scenario reference tables
- Specific requirements for SRE deliverable

When modifying the prompt:
- Keep token budget under 16,384 (max_tokens setting)
- Maintain the structured output format
- Preserve the failure reference tables for consistent scenario generation

## Performance Considerations

- Fetching 10,000 documents can be slow for large indices
- LLM generation can take 30-120 seconds depending on log complexity
- Streaming mode provides better UX for long generations
- FastAPI is stateless - no session management needed
- Consider implementing caching for frequently accessed indices

## AWS Bedrock Model Configuration

Supported models:
- Uses inference profile IDs with regional prefixes (`global.`, `us.`, `eu.`)
- Default model: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Ensure model access is enabled in AWS Bedrock console

## Dependencies

### Backend Only (requirements-api.txt)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `requests` - HTTP client
- `boto3` - AWS SDK
- `python-dotenv` - Environment variables

### Full Stack (requirements.txt)
Includes all backend dependencies plus Streamlit, TensorFlow, PyTorch, and other ML libraries (most are unnecessary for the core functionality).
