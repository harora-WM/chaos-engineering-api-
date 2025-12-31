# Chaos Engineering Plan Generator

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688)
![License](https://img.shields.io/badge/license-MIT-green)

A comprehensive chaos engineering plan generator that analyzes application logs from OpenSearch and uses AWS Bedrock (Claude AI) to create detailed chaos testing scenarios.

**Live API:** https://chaos-engineering-api.onrender.com
**Documentation:** https://chaos-engineering-api.onrender.com/docs

---

## 🌟 Features

- ✅ **OpenSearch Integration** - Fetch and analyze application logs from any OpenSearch cluster
- ✅ **AI-Powered Analysis** - Uses AWS Bedrock (Claude Sonnet 4.5) to generate intelligent chaos plans
- ✅ **Multi-Platform Support** - Covers Kubernetes, AWS, Azure, GCP, and VM infrastructure
- ✅ **Comprehensive Scenarios** - Generates 4 chaos scenarios covering component failures, stress conditions, network issues, and dependencies
- ✅ **Streaming Support** - Real-time chaos plan generation with Server-Sent Events
- ✅ **REST API** - Easy integration with any frontend framework
- ✅ **Interactive Docs** - Auto-generated Swagger UI for testing

---

## 🏗️ Architecture

### Two Deployment Modes

#### 1. Streamlit UI (Original)
Interactive web interface for manual chaos plan generation.

```bash
streamlit run chaos_code.py
```

#### 2. FastAPI Backend (Production)
RESTful API for frontend integration - **Currently Deployed**

```
chaos_deploy/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic request/response models
│   ├── config.py            # Configuration management
│   └── clients/
│       ├── opensearch_client.py    # OpenSearch operations
│       ├── llm_client.py           # AWS Bedrock integration
│       └── chaos_generator.py      # Chaos plan generation logic
├── requirements-api.txt     # Backend dependencies
├── Dockerfile              # Container configuration
└── .env                    # Environment variables (not in git)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenSearch cluster (with logs)
- AWS account with Bedrock access
- AWS credentials with Claude model enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/harora-WM/chaos-engineering-api-.git
   cd chaos-engineering-api-
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-api.txt
   ```

4. **Configure environment variables**

   Create `.env` file:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=ap-south-1
   BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
   ```

5. **Run the API**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs

---

## 📡 API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /` - API information

### OpenSearch Operations
- `POST /api/opensearch/test-connection` - Test OpenSearch connection
- `POST /api/opensearch/indices` - Get all indices
- `POST /api/opensearch/fetch-data` - Fetch data from specific index

### AWS Bedrock Operations
- `POST /api/bedrock/test-connection` - Test AWS Bedrock connection

### Chaos Plan Generation
- `POST /api/chaos/generate` - Generate chaos plan (non-streaming)
- `POST /api/chaos/generate-stream` - Generate chaos plan with streaming

---

## 💻 Usage Examples

### JavaScript/TypeScript

```javascript
const response = await fetch('https://chaos-engineering-api.onrender.com/api/chaos/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    index_name: "logs-2024",
    opensearch_config: {
      endpoint: "http://your-opensearch:9200",
      username: "admin",
      password: "password"
    },
    aws_config: {
      model: "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
      region: "ap-south-1"
    },
    analysis_options: {
      focus: "All",
      security: true,
      include_external: true
    }
  })
});

const result = await response.json();
console.log(result.plan);
```

### Python

```python
import requests

response = requests.post(
    'https://chaos-engineering-api.onrender.com/api/chaos/generate',
    json={
        'index_name': 'logs-2024',
        'opensearch_config': {
            'endpoint': 'http://your-opensearch:9200',
            'username': 'admin',
            'password': 'password'
        },
        'aws_config': {
            'model': 'global.anthropic.claude-sonnet-4-5-20250929-v1:0',
            'region': 'ap-south-1'
        }
    }
)

result = response.json()
print(result['plan'])
```

### Using TypeScript Client

```typescript
import { ChaosEngineeringAPI } from './chaos-api.types';

const api = new ChaosEngineeringAPI();

const response = await api.generateChaosPlan({
  index_name: "logs-2024",
  opensearch_config: { /* ... */ },
  aws_config: { /* ... */ }
});

if (response.success) {
  console.log(response.plan);
}
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t chaos-api .
```

### Run Container

```bash
docker run -p 8000:8000 --env-file .env chaos-api
```

---

## ☁️ Cloud Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect repository on [Render](https://render.com)
3. Configure:
   - **Build Command:** `pip install -r requirements-api.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env`
5. Deploy!

**Current deployment:** https://chaos-engineering-api.onrender.com

### Deploy to Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/chaos-api
gcloud run deploy chaos-api --image gcr.io/PROJECT_ID/chaos-api
```

---

## 🧪 Testing

### Automated Tests

```bash
python3 test_api.py
```

### Quick Shell Tests

```bash
./test_endpoints.sh
```

### Using Postman

Import `Chaos_API.postman_collection.json` into Postman for interactive testing.

---

## 📚 Frontend Integration Resources

### For Frontend Developers

1. **Postman Collection** - `Chaos_API.postman_collection.json`
2. **TypeScript Types** - `chaos-api.types.ts`
3. **Complete Examples** - `API_EXAMPLES.md`
4. **Interactive Docs** - https://chaos-engineering-api.onrender.com/docs

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `ap-south-1` |
| `BEDROCK_MODEL_ID` | Claude model ID | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` (all) |

### Analysis Options

- **focus**: `All`, `Network`, `Database`, `Storage`, `External APIs`, `Security`
- **security**: Include security analysis (boolean)
- **include_external**: Include external dependencies (boolean)

---

## 🎯 Chaos Plan Output

The generated chaos plan includes:

1. **Log & Topology Analysis**
   - Service topology diagram (textual)
   - Communication patterns
   - IP addresses, ports, FQDNs
   - Internal and external dependencies

2. **Entity Identification**
   - Kubernetes pods/services
   - Cloud resources (AWS/Azure/GCP)
   - Virtual machines

3. **Cross-Reference Failure Modes**
   - Applicable chaos scenarios per entity
   - Failure propagation mapping
   - Blast radius analysis

4. **4 Chaos Scenarios**
   - Component failures
   - Stress conditions
   - Network conditions
   - Dependency failures

Each scenario includes:
- Entity details
- Failure type
- Hypothesis
- Steady state metrics
- Injection method
- Propagation path
- Rollback criteria
- Observability hooks

---

## 🚨 Known Limitations

### Free Tier Constraints (Render)

- ⚠️ **Cold Start**: First request after 15 minutes of inactivity takes 50-60 seconds
- ⚠️ **No Persistent Storage**: API is stateless
- ⚠️ **Auto-Sleep**: Service spins down after inactivity

**Solution**: Upgrade to paid tier ($7/month) for always-on service.

### Rate Limits

Currently no rate limiting. Consider adding for production use.

---

## 🔒 Security Considerations

### Current Setup
- ✅ Environment variables for AWS credentials
- ✅ CORS enabled (configurable)
- ✅ HTTPS enabled (Render provides SSL)

### TODO for Production
- ⚠️ Add API key authentication
- ⚠️ Implement rate limiting
- ⚠️ Use secrets manager instead of request body credentials
- ⚠️ Add request validation and sanitization
- ⚠️ Implement audit logging

---

## 🛠️ Development

### Project Structure

```
chaos_deploy/
├── backend/                 # FastAPI backend
│   ├── main.py             # API routes
│   ├── models.py           # Pydantic models
│   ├── config.py           # Configuration
│   └── clients/            # Business logic
├── chaos_code.py           # Streamlit UI (original)
├── requirements-api.txt    # Backend dependencies
├── requirements.txt        # Full dependencies
├── Dockerfile              # Container config
├── test_api.py            # Automated tests
└── test_endpoints.sh      # Shell tests
```

### Running Locally

```bash
# Backend only
uvicorn backend.main:app --reload

# Streamlit UI
streamlit run chaos_code.py
```

### Running Tests

```bash
# All tests
python3 test_api.py

# Quick tests
./test_endpoints.sh

# Test specific endpoint
curl https://chaos-engineering-api.onrender.com/health
```

---

## 📖 Documentation

- **API Docs**: https://chaos-engineering-api.onrender.com/docs
- **ReDoc**: https://chaos-engineering-api.onrender.com/redoc
- **Examples**: See `API_EXAMPLES.md`
- **Architecture**: See `CLAUDE.md`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙋 Support

- **Issues**: https://github.com/harora-WM/chaos-engineering-api-/issues
- **Documentation**: https://chaos-engineering-api.onrender.com/docs

---

## 🎯 Roadmap

- [ ] Add API key authentication
- [ ] Implement rate limiting
- [ ] Add caching for frequently accessed indices
- [ ] Support for multiple LLM providers
- [ ] Export chaos plans to PDF/Word
- [ ] Integration with chaos testing tools (Chaos Mesh, LitmusChaos)
- [ ] Historical plan storage and versioning

---

## 👥 Authors

- **Hardik Arora** - Initial work - [@harora-WM](https://github.com/harora-WM)

---

## 🙏 Acknowledgments

- AWS Bedrock for Claude AI models
- OpenSearch for log analysis capabilities
- FastAPI framework for excellent developer experience
- Render for simple cloud deployment

---

**Built with ❤️ for SRE teams practicing Chaos Engineering**
