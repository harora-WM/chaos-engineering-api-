# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Chaos Engineering Plan Generator** - Analyzes application logs from OpenSearch and uses AWS Bedrock (Claude AI) to generate comprehensive chaos engineering test plans.

**Two deployment modes:**
1. **FastAPI REST API** (`backend/`) - Production API (currently deployed on Render)
2. **Streamlit Web UI** (`chaos_code.py`) - Original interactive interface for manual testing

## Architecture

```
chaos_deploy/
├── backend/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── models.py            # Pydantic request/response models
│   ├── config.py            # Configuration and environment variables
│   └── clients/             # Core business logic (extracted from monolithic Streamlit)
│       ├── opensearch_client.py    # OpenSearch operations
│       ├── llm_client.py           # AWS Bedrock/LLM operations
│       └── chaos_generator.py      # Chaos plan generation logic
├── chaos_code.py            # Streamlit UI (legacy)
├── requirements-api.txt     # Backend-only dependencies (minimal)
├── requirements.txt         # Full dependencies (includes Streamlit + ML libs)
└── Dockerfile              # Production container
```

### Core Components (backend/clients/)

**OpenSearchClient** - Fetches up to 10,000 documents per query using basic auth
**LLMClient** - AWS Bedrock integration with 3-retry logic and streaming support
**ChaosPlanGenerator** - Orchestrates plan generation with comprehensive prompt (400+ lines) containing failure reference tables for VMs, K8s, AWS, Azure, GCP

## Development Commands

### Run Backend Locally (Recommended)
```bash
# Setup
python3 -m venv venv-api
source venv-api/bin/activate
pip install -r requirements-api.txt

# Run with auto-reload
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Access at http://localhost:8000/docs
```

### Run Streamlit UI (Legacy/Testing)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run chaos_code.py  # http://localhost:8501
```

### Testing
```bash
# Comprehensive API tests
python3 test_api.py

# Quick curl-based tests
./test_endpoints.sh
```

### Docker
```bash
docker build -t chaos-api .
docker run -p 8000:8000 --env-file .env chaos-api
```

## API Endpoints

All endpoints documented at `/docs` (Swagger UI)

**Health:** `GET /health`, `GET /`
**OpenSearch:** `POST /api/opensearch/test-connection`, `/indices`, `/fetch-data`
**Bedrock:** `POST /api/bedrock/test-connection`
**Chaos Generation:** `POST /api/chaos/generate`, `/generate-stream` (SSE streaming)

## Environment Configuration

Required `.env` file:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
CORS_ORIGINS=*  # Optional
```

## Deployment

### Production (Render - Currently Active)

**Live API:** https://chaos-engineering-api.onrender.com/docs

**Auto-deploy from `main` branch:**
- Build: `pip install -r requirements-api.txt`
- Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Deploy time: 3-5 minutes after push
- **Important:** Free tier has cold start (50-60s) after 15 min inactivity

```bash
git push origin main  # Auto-deploys to Render
```

## Important Implementation Details

### Chaos Plan Generation Workflow
1. **Log Analysis** - Parse logs to identify service dependencies, IPs, ports, FQDNs
2. **Entity Classification** - Identify infrastructure type (K8s/AWS/Azure/GCP/VMs)
3. **Failure Mapping** - Cross-reference entities with failure scenario reference tables
4. **Plan Output** - Generate 4 scenarios: component failures, stress, network, dependencies

### The Prompt (`backend/clients/chaos_generator.py:_create_prompt()`)
- 400+ line comprehensive prompt with failure reference tables
- Covers VMs, Kubernetes, AWS (EC2/EKS/RDS/Lambda/etc), Azure, GCP
- Token budget: 16,384 max_tokens
- **When modifying:** Preserve structured output format and reference tables

### Streaming Implementation
- **FastAPI**: `StreamingResponse` with Server-Sent Events (SSE)
- **Streamlit**: `st.write_stream()` with generator
- Provides better UX for 30-120 second LLM generations

### Performance Notes
- OpenSearch: Fetches up to 10,000 documents per query
- LLM: 3-retry logic with exponential backoff
- API is stateless (no session management)
- Consider caching for frequently accessed indices

### Frontend Integration Resources
- `Chaos_API.postman_collection.json` - Postman collection
- `chaos-api.types.ts` - TypeScript types + API client class
- `API_EXAMPLES.md` - Complete request/response examples
- `/docs` - Interactive Swagger UI

## Dependencies

**requirements-api.txt** (production): fastapi, uvicorn, pydantic, requests, boto3, python-dotenv
**requirements.txt** (legacy): Includes above + Streamlit, TensorFlow, PyTorch (mostly unnecessary)
