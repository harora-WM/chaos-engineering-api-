# Chaos Engineering Plan Generator - FastAPI Backend

REST API for generating chaos engineering plans from OpenSearch logs using AWS Bedrock.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-api.txt
```

### 2. Configure Environment

Create `.env` file:

```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### 3. Run the API

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access Documentation

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Generate Chaos Plan

**POST** `/api/chaos/generate`

```json
{
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
}
```

### Streaming Generation

**POST** `/api/chaos/generate-stream`

Returns Server-Sent Events stream.

## Docker Deployment

### Build

```bash
docker build -t chaos-api .
```

### Run

```bash
docker run -p 8000:8000 --env-file .env chaos-api
```

## Cloud Deployment

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/chaos-api
gcloud run deploy chaos-api --image gcr.io/PROJECT_ID/chaos-api
```

### Render

1. Connect GitHub repo
2. Build: `pip install -r requirements-api.txt`
3. Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## Integration Example

### JavaScript/TypeScript

```typescript
const response = await fetch('https://your-api.com/api/chaos/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    index_name: "logs-2024",
    opensearch_config: { /* ... */ },
    aws_config: { /* ... */ }
  })
});

const { plan, metrics } = await response.json();
```

### Python

```python
import requests

response = requests.post('https://your-api.com/api/chaos/generate', json={
    'index_name': 'logs-2024',
    'opensearch_config': { ... },
    'aws_config': { ... }
})

result = response.json()
print(result['plan'])
```

## Architecture

```
Frontend App → FastAPI Backend → OpenSearch + AWS Bedrock
                    ↓
              Chaos Plan Output
```

See `CLAUDE.md` for complete documentation.
