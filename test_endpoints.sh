#!/bin/bash
# Quick manual endpoint testing with curl

API_URL="http://localhost:8000"

echo "=========================================="
echo "TESTING CHAOS ENGINEERING API ENDPOINTS"
echo "=========================================="
echo ""

echo "1️⃣  Testing Health Endpoint..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

echo "2️⃣  Testing Root Endpoint..."
curl -s "$API_URL/" | python3 -m json.tool
echo ""

echo "3️⃣  Testing OpenSearch Connection..."
curl -s -X POST "$API_URL/api/opensearch/test-connection" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "http://a535cb3b72b21477894f7c62dda6d607-1503392638.ap-south-1.elb.amazonaws.com:9200/",
    "username": "admin",
    "password": "b#Z2xTpR$9MvYkHq"
  }' | python3 -m json.tool
echo ""

echo "4️⃣  Testing Get Indices (first 2 shown)..."
curl -s -X POST "$API_URL/api/opensearch/indices" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "http://a535cb3b72b21477894f7c62dda6d607-1503392638.ap-south-1.elb.amazonaws.com:9200/",
    "username": "admin",
    "password": "b#Z2xTpR$9MvYkHq"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Success: {data['success']}, Indices: {len(data['indices'])}\")"
echo ""

echo "5️⃣  Testing AWS Bedrock Connection..."
curl -s -X POST "$API_URL/api/bedrock/test-connection" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "region": "ap-south-1"
  }' | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ Basic endpoint tests complete!"
echo "View full API docs at: $API_URL/docs"
echo "=========================================="
