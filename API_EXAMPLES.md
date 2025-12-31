# Chaos Engineering API - Request/Response Examples

Base URL: `https://chaos-engineering-api.onrender.com`

---

## 1. Health Check

### Request
```http
GET /health
```

### Response (200 OK)
```json
{
  "status": "healthy",
  "message": "API is operational"
}
```

---

## 2. Test OpenSearch Connection

### Request
```http
POST /api/opensearch/test-connection
Content-Type: application/json
```
```json
{
  "endpoint": "http://your-opensearch:9200",
  "username": "admin",
  "password": "your-password"
}
```

### Response - Success (200 OK)
```json
{
  "success": true,
  "message": "✅ Connected to OpenSearch v3.3.1"
}
```

### Response - Failure (200 OK)
```json
{
  "success": false,
  "message": "❌ Connection failed: Connection refused"
}
```

---

## 3. Get OpenSearch Indices

### Request
```http
POST /api/opensearch/indices
Content-Type: application/json
```
```json
{
  "endpoint": "http://your-opensearch:9200",
  "username": "admin",
  "password": "your-password"
}
```

### Response - Success (200 OK)
```json
{
  "success": true,
  "indices": [
    {
      "index": "logs-2024-01",
      "health": "green",
      "status": "open",
      "docs.count": "15234",
      "store.size": "12.3mb",
      "pri": "1",
      "rep": "1"
    },
    {
      "index": "logs-2024-02",
      "health": "green",
      "status": "open",
      "docs.count": "23456",
      "store.size": "18.7mb",
      "pri": "1",
      "rep": "1"
    }
  ]
}
```

### Response - Failure (200 OK)
```json
{
  "success": false,
  "indices": [],
  "error": "Failed to get indices: Connection timeout"
}
```

---

## 4. Fetch Index Data

### Request
```http
POST /api/opensearch/fetch-data
Content-Type: application/json
```
```json
{
  "endpoint": "http://your-opensearch:9200",
  "username": "admin",
  "password": "your-password",
  "index_name": "logs-2024-01"
}
```

### Response - Success (200 OK)
```json
{
  "success": true,
  "sample_size": 568,
  "total_hits": 15234,
  "took_ms": 45,
  "mapping": {
    "logs-2024-01": {
      "mappings": {
        "properties": {
          "timestamp": { "type": "date" },
          "message": { "type": "text" },
          "level": { "type": "keyword" }
        }
      }
    }
  },
  "documents": {
    "hits": {
      "total": { "value": 15234 },
      "hits": [
        {
          "_source": {
            "timestamp": "2024-01-15T10:30:00Z",
            "message": "Application started",
            "level": "INFO"
          }
        }
      ]
    }
  }
}
```

### Response - Failure (200 OK)
```json
{
  "success": false,
  "error": "Index not found: logs-2024-01"
}
```

---

## 5. Test AWS Bedrock Connection

### Request
```http
POST /api/bedrock/test-connection
Content-Type: application/json
```
```json
{
  "model": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "region": "ap-south-1"
}
```

### Response - Success (200 OK)
```json
{
  "success": true,
  "message": "✅ Connected to AWS Bedrock with model 'global.anthropic.claude-sonnet-4-5-20250929-v1:0'"
}
```

### Response - Failure (200 OK)
```json
{
  "success": false,
  "message": "❌ Access denied. Enable model access at https://console.aws.amazon.com/bedrock/home?#/modelaccess"
}
```

---

## 6. Generate Chaos Plan (Non-Streaming)

### Request
```http
POST /api/chaos/generate
Content-Type: application/json
```
```json
{
  "index_name": "logs-2024-01",
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

### Response - Success (200 OK)
```json
{
  "success": true,
  "plan": "# CHAOS ENGINEERING PLAN\n\n## Step 1: Log & Topology Analysis\n\n### Textual Service Topology:\n\n1. Pod: api-service-xyz (IP: 10.0.1.5, Port: 8080)\n│\n├──→ Database: PostgreSQL (IP: 10.0.2.10, Port: 5432)\n│   └──→ Connection pool: 20 connections\n│\n├──→ Redis Cache (IP: 10.0.2.15, Port: 6379)\n│   └──→ Session storage\n│\n└──→ External API: payment-gateway.example.com\n    └──→ HTTPS/REST\n\n### Communication Patterns:\n- HTTP/REST: External API\n- TCP: PostgreSQL, Redis\n\n## Step 2: Entity Identification\n\n- api-service-xyz: Kubernetes Pod\n- PostgreSQL: Kubernetes Stateful Set\n- Redis: Kubernetes Pod\n- payment-gateway: External Service\n\n## Step 3: Cross-Reference Failure Modes\n\n| Entity | Type | Applicable Scenarios |\n|--------|------|---------------------|\n| api-service-xyz | K8s Pod | Loss of pods, High CPU, High Memory |\n| PostgreSQL | Stateful Set | Remove stateful set, Block Traffic |\n| Redis | K8s Pod | Loss of pods, Scale down |\n| payment-gateway | External | Loss of interfacing system, Network latency |\n\n## Step 4: Chaos Plan (4 Scenarios)\n\n### Scenario 1: Pod Failure\n**Entity:** api-service-xyz\n**Failure Type:** Loss of pods\n**Hypothesis:** System should handle pod failure with automatic restart\n**Steady State:** Response time < 200ms, Error rate < 0.1%\n**Injection Method:** kubectl delete pod api-service-xyz\n**Propagation:** User requests fail → Load balancer redirects → New pod starts\n**Blast Radius:** Single pod, limited to 1/3 of traffic\n**Rollback:** Kubernetes auto-restart (30s)\n**Observability:** Monitor pod restart count, response times\n**Goal:** Verify zero-downtime deployment\n\n### Scenario 2: Database Connection Loss\n**Entity:** PostgreSQL\n**Failure Type:** Block Traffic (Target) - Pod\n**Hypothesis:** Application should retry with backoff\n**Steady State:** Database queries < 100ms\n**Injection Method:** Network policy to block traffic\n**Propagation:** DB queries timeout → Circuit breaker opens → Fallback to cache\n**Blast Radius:** All write operations, cached reads continue\n**Rollback:** Remove network policy\n**Observability:** Circuit breaker state, cache hit rate\n**Goal:** Test graceful degradation\n\n### Scenario 3: High CPU on Pods\n**Entity:** api-service-xyz\n**Failure Type:** High CPU stress\n**Hypothesis:** Auto-scaling should trigger at 70% CPU\n**Steady State:** CPU < 50%, Response time < 200ms\n**Injection Method:** Stress test tool (Apache Bench)\n**Propagation:** CPU spike → HPA triggers → New pods launch\n**Blast Radius:** Temporary performance degradation\n**Rollback:** Stop stress test\n**Observability:** HPA metrics, pod count, CPU usage\n**Goal:** Validate auto-scaling configuration\n\n### Scenario 4: External API Latency\n**Entity:** payment-gateway.example.com\n**Failure Type:** Network latency\n**Hypothesis:** Timeout after 5s with proper error handling\n**Steady State:** Payment API response < 1s\n**Injection Method:** Proxy with artificial delay\n**Propagation:** Slow response → Request timeout → User error message\n**Blast Radius:** Payment functionality only\n**Rollback:** Remove proxy delay\n**Observability:** API timeout rate, error logs\n**Goal:** Test timeout and retry mechanisms\n\n---\n\n## Recommendations\n\n1. **Reliability:** Add circuit breaker for database connections\n2. **Scalability:** Configure HPA with CPU threshold at 60%\n3. **Security:** Implement mTLS for internal services\n4. **Monitoring:** Add distributed tracing for better observability\n\n---\n\nGenerated: 2024-12-31\nDuration: 45.2 seconds",
  "metrics": {
    "start_time": 1704029400,
    "end_time": 1704029445.2,
    "duration_seconds": 45.2,
    "plan_length": 3542,
    "success": true
  }
}
```

### Response - Failure (200 OK)
```json
{
  "success": false,
  "error": "Failed to fetch index data: Index not found",
  "metrics": {
    "start_time": 1704029400,
    "success": false,
    "error": "Failed to fetch index data: Index not found"
  }
}
```

---

## 7. Generate Chaos Plan (Streaming)

### Request
```http
POST /api/chaos/generate-stream
Content-Type: application/json
```
```json
{
  "index_name": "logs-2024-01",
  "opensearch_config": {
    "endpoint": "http://your-opensearch:9200",
    "username": "admin",
    "password": "your-password"
  },
  "aws_config": {
    "model": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "region": "ap-south-1"
  }
}
```

### Response - Streaming (200 OK)
**Content-Type:** `text/event-stream`

```
data: # CHAOS

data:  ENGINEERING PLAN

data:

## Step 1:

data:  Log & Topology Analysis

data:

### Textual Service

data:  Topology:

data:

1. Pod

data: : api-service-xyz

...

data: {"error": "Some error message"}
```

**Note:** The streaming response sends chunks prefixed with `data: `. Your frontend should parse these incrementally.

---

## Error Response Format

All endpoints return errors in this format:

### HTTP 500 - Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

### HTTP 422 - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "endpoint"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Common HTTP Status Codes

- **200 OK** - Request successful (even if business logic fails, check `success` field)
- **422 Unprocessable Entity** - Invalid request body (missing fields, wrong types)
- **500 Internal Server Error** - Server error

---

## Notes for Frontend Developers

1. **Always check `success` field** in response body, not just HTTP status
2. **Streaming endpoint** requires special handling (Server-Sent Events)
3. **First request after inactivity** may take 50-60 seconds (Render free tier cold start)
4. **CORS is enabled** - no special headers needed
5. **No authentication required** currently (may change in future)
6. **Timeout recommendations:**
   - Health/Test endpoints: 10 seconds
   - Get indices: 30 seconds
   - Generate plan: 180 seconds (3 minutes)
   - Streaming: No timeout (wait for completion)
