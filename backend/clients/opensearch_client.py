"""OpenSearch client for managing OpenSearch operations"""
import requests
from typing import Dict, List, Tuple


class OpenSearchClient:
    """Client for OpenSearch operations"""

    def __init__(self, endpoint: str, username: str, password: str):
        self.endpoint = endpoint.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.timeout = 30

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to OpenSearch"""
        try:
            response = self.session.get(f"{self.endpoint}/", timeout=10)
            if response.status_code == 200:
                version = response.json().get('version', {}).get('number', 'unknown')
                return True, f"✅ Connected to OpenSearch v{version}"
            return False, f"❌ HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"❌ Connection failed: {str(e)}"

    def get_indices(self) -> List[Dict]:
        """Get all indices"""
        try:
            response = self.session.get(
                f"{self.endpoint}/_cat/indices?format=json&h=index,health,status,docs.count,store.size,pri,rep",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get indices: {str(e)}")

    def get_index_data(self, index_name: str) -> Dict:
        """Get sample data from index - fixed to remove sorting issues"""
        try:
            # Get mapping first
            mapping_response = self.session.get(
                f"{self.endpoint}/{index_name}/_mapping",
                timeout=self.timeout
            )

            # Simple query without sorting to avoid field issues
            search_body = {
                "size": 10000,  # Fixed small sample size
                "query": {"match_all": {}}
            }

            search_response = self.session.post(
                f"{self.endpoint}/{index_name}/_search",
                json=search_body,
                timeout=self.timeout
            )
            search_response.raise_for_status()

            data = search_response.json()
            hits = data.get('hits', {}).get('hits', [])

            return {
                "mapping": mapping_response.json() if mapping_response.ok else {},
                "documents": data,
                "sample_size": len(hits),
                "total_hits": data.get('hits', {}).get('total', {}).get('value', 0),
                "took_ms": data.get('took', 0),
                "success": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
