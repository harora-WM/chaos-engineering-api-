import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import time
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(".env")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Chaos Engineering Plan Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Initialize session state variables
if 'os_client' not in st.session_state:
    st.session_state.os_client = None
if 'llm_client' not in st.session_state:
    st.session_state.llm_client = None
if 'indices' not in st.session_state:
    st.session_state.indices = []
if 'selected_index' not in st.session_state:
    st.session_state.selected_index = None
if 'index_data' not in st.session_state:
    st.session_state.index_data = None
if 'chaos_plan' not in st.session_state:
    st.session_state.chaos_plan = None
if 'connection_tested' not in st.session_state:
    st.session_state.connection_tested = False

# ============================================================================
# CUSTOM CSS
# ============================================================================

def load_custom_css():
    """Load custom CSS for the application"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        color: #718096;
        font-size: 0.9rem;
        text-transform: uppercase;
    }
    
    .status-success {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        color: #155724;
        margin-bottom: 1rem;
    }
    
    .status-error {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
        color: #721c24;
        margin-bottom: 1rem;
    }
    
    .status-warning {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        color: #856404;
        margin-bottom: 1rem;
    }
    
    .status-info {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        margin: 0.25rem;
    }
    
    .primary-button > button {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%) !important;
    }
    
    .danger-button > button {
        background: linear-gradient(135deg, #f44336 0%, #c62828 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# OPENSEARCH CLIENT
# ============================================================================

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
            st.error(f"Failed to get indices: {str(e)}")
            return []
    
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
            st.error(f"Failed to get index data: {str(e)}")
            return {"success": False, "error": str(e)}

# ============================================================================
# LLM CLIENT
# ============================================================================

class LLMClient:
    """Client for LLM operations using AWS Bedrock"""

    def __init__(self, model: str = "anthropic.claude-3-haiku-20240307-v1:0", region: str = "us-east-1"):
        self.model = model
        self.region = region
        self.max_retries = 3
        self.client = None

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to AWS Bedrock"""
        try:
            # Create Bedrock Runtime client
            self.client = boto3.client("bedrock-runtime", region_name=self.region)

            # Try a simple test call
            test_payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Hi"}],
                    }
                ],
            }

            response = self.client.invoke_model(
                modelId=self.model,
                body=json.dumps(test_payload)
            )

            return True, f"✅ Connected to AWS Bedrock with model '{self.model}'"

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                return False, f"❌ Model '{self.model}' not found. Check model ID and region."
            elif error_code == 'AccessDeniedException':
                return False, f"❌ Access denied. Enable model access at https://console.aws.amazon.com/bedrock/home?#/modelaccess"
            else:
                return False, f"❌ AWS Error: {error_code} - {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"❌ Failed to connect to AWS Bedrock: {str(e)}"

    def analyze_with_bedrock(self, prompt: str) -> str:
        """Generate analysis using AWS Bedrock with retries"""
        if not self.client:
            self.client = boto3.client("bedrock-runtime", region_name=self.region)

        for attempt in range(self.max_retries):
            try:
                # Format the request payload using Bedrock's native structure
                native_request = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 16384,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": prompt}],
                        }
                    ],
                }

                # Invoke the model
                response = self.client.invoke_model(
                    modelId=self.model,
                    body=json.dumps(native_request)
                )

                # Decode the response body
                model_response = json.loads(response["body"].read())

                # Extract and return the response text
                response_text = model_response["content"][0]["text"]
                return response_text

            except ClientError as e:
                error_msg = f"Bedrock error (attempt {attempt+1}): {e.response['Error']['Code']} - {e.response['Error']['Message']}"
                print(error_msg)
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))

            except Exception as e:
                error_msg = f"Bedrock connection failed (attempt {attempt+1}): {str(e)}"
                print(error_msg)
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))

        raise Exception(f"All {self.max_retries} attempts failed")

    def analyze_with_bedrock_streaming(self, prompt: str):
        """Generate analysis using AWS Bedrock with streaming response.

        Yields text chunks as they are generated by the model.
        """
        if not self.client:
            self.client = boto3.client("bedrock-runtime", region_name=self.region)

        # Format the request payload using Bedrock's native structure
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 16384,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }

        # Invoke the model with streaming response
        streaming_response = self.client.invoke_model_with_response_stream(
            modelId=self.model,
            body=json.dumps(native_request)
        )

        # Extract and yield the response text in real-time
        for event in streaming_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk["type"] == "content_block_delta":
                text = chunk["delta"].get("text", "")
                if text:
                    yield text
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are a Chaos Engineering SRE expert with 15 years of experience."""

# ============================================================================
# CHAOS PLAN GENERATOR
# ============================================================================

class ChaosPlanGenerator:
    """Main class for generating chaos plans"""
    
    def __init__(self, opensearch_client: OpenSearchClient, llm_client: LLMClient):
        self.os_client = opensearch_client
        self.llm_client = llm_client
        
    def generate_plan(self, index_name: str, index_data: Dict, analysis_options: Dict) -> Tuple[str, Dict]:
        """Generate chaos engineering plan"""

        metrics = {
            "start_time": time.time(),
            "success": False,
            "error": None
        }

        try:
            # Create prompt
            prompt = self._create_prompt(index_name, index_data, analysis_options)

            # Generate with LLM
            plan = self.llm_client.analyze_with_bedrock(prompt)

            if plan:
                metrics.update({
                    "success": True,
                    "end_time": time.time(),
                    "duration_seconds": time.time() - metrics["start_time"],
                    "plan_length": len(plan)
                })
                return plan, metrics
            else:
                metrics["error"] = "Empty response from LLM"
                return "", metrics

        except Exception as e:
            metrics["error"] = str(e)
            return "", metrics

    def generate_plan_streaming(self, index_name: str, index_data: Dict, analysis_options: Dict):
        """Generate chaos engineering plan with streaming output.

        Yields text chunks as they are generated by the LLM.
        Returns a generator that yields text chunks.
        """
        # Create prompt
        prompt = self._create_prompt(index_name, index_data, analysis_options)

        # Generate with LLM using streaming
        yield from self.llm_client.analyze_with_bedrock_streaming(prompt)
    
    def _create_prompt(self, index_name: str, index_data: Dict, analysis_options: Dict) -> str:
        """Create prompt for LLM"""
        
        # Extract sample documents
        hits = index_data.get("documents", {}).get("hits", {}).get("hits", [])
        sample_docs = []
        
        for i, hit in enumerate(hits[:1000]):  # Only use first 5 docs for LLM
            source = hit.get("_source", {})
            # Truncate long messages
            message = source.get("message") or source.get("log") or str(source)
            
            sample_docs.append({
                "doc": i + 1,
                "timestamp": source.get("@timestamp", source.get("timestamp", "N/A")),
                "message": message,
                "level": source.get("level", source.get("severity", "N/A")),
                "service": source.get("service", source.get("app", "N/A"))
            })
        
        # Build prompt
        prompt = f"""
# CHAOS ENGINEERING PLAN GENERATION

## INDEX INFORMATION:
- **Index Name:** {index_name}
- **Total Documents:** {index_data.get('total_hits', 0):,}
- **Query Time:** {index_data.get('took_ms', 0)} ms

## SAMPLE LOG DOCUMENTS (1000 out of {len(hits)} fetched):
```json
{json.dumps(sample_docs, indent=2)}

Focus Area: {analysis_options.get('focus', 'All')}

Include Security: {analysis_options.get('security', True)}

Include External Dependencies: {analysis_options.get('include_external', True)}
You are a Chaos Engineering SRE expert with 15 years of experience. Your task is to analyze the logs and provide all necessary output under 16384 tokens only:

Step 1 — Log & Topology Analysis

Analyze the provided kubernetes configuration file and determine weaknesses around reliability, scalability and security and provide remedial recommendations specific to the logs(pin point the issue exactly and tell technical remedies specefic to the pod configuration and show its each analysis)

Parse and analyze the given application logs.

From logs, generate a textual service topology that includes:

IP addresses, Port numbers, FQDNs, URLs and methods such as GET/PUT/POST/etc.

All internal service communications (pod ↔ pod, pod ↔ DataBases, service ↔ service, middleware interactions, storage interactions).

All external communications (to DNS, LDAP, MQ, APIs, 3rd-party services, interfacing systems).

Show dependencies and propagation paths (e.g., "Pod A → Service B → External DB").

Represent topology as a clear textual graph (priority). The output for this could be something along the lines of the following structure strictly (example):

Textual Service Topology:
text
1. Pod: wmuitestcontroller-7ddb4564f4-hhcxb (IP: Kubernetes-internal, Port: 9090)
│
├──→ Consul: wmconsul.default.svc.cluster.local (DNS: Kubernetes service)
│ └──→ Service discovery and configuration
│
├──→ Database: PostgreSQL (via SPRING_DATASOURCE_URL_UIT)
│ └──→ Database operations (Hibernate, Liquibase)
│
├──→ RabbitMQ: (via SPRING_RABBITMQ_HOST)
│ └──→ Message queueing for async tasks
│
├──→ OpenSearch: (via OPENSEARCH_URIS)
│ └──→ Logging and search operations
│
├──→ Minio/S3: (via STORAGE_ENDPOINT, STORAGE_REGION)
│ └──→ Storage for screenshots, videos, HAR files, APK/IPA, etc.
│ ├──→ Bucket: wm-ui-test-screenshots
│ ├──→ Bucket: wm-ui-test-videos
│ ├──→ Bucket: wm-ft-tmp
│ ├──→ Bucket: wm-ui-test-har
│ ├──→ Bucket: wm-ui-test-browser-logs
│ ├──→ Bucket: wm-ui-test-scripts
│ ├──→ Bucket: wm-ui-test-page-source
│ ├──→ Bucket: wm-ui-test-apk-ipa
│ ├──→ Bucket: wm-ui-test-resource
│ └──→ Bucket: wm-ui-test-scm-repository
│
├──→ Gateway: (via WM_GATEWAY_BASEURL)
│ └──→ API gateway for external communications
│
├──→ External: JIRA (DBSRootUAT.crt) - Certificate lookup failed
│
├──→ External: Device Farm (video sessions)
│ └──→ chrome-124-0-6367-118-6-* sessions
│
└──→ External: ALM (via wmMetaClient.getTicketCredentialDTOByCode)
└──→ Ticket credential lookup
Communication Patterns:
- HTTP/REST: Consul, Gateway, ALM, Device Farm
- JDBC: PostgreSQL
- AMQP: RabbitMQ
- S3 API: Minio/S3
- OpenSearch API: OpenSearch(As you can see from the example all the communication patterns are noted and clear )
Key Observations(All key observations from the observed pattterns and more fixes should be displayed)

Step 2 — Entity Identification

For each node in the topology, identify if it is a:

Kubernetes pod / service / stateful set

VM (Linux/Windows)

AWS Resource (EC2, EKS, RDS, Lambda, S3, etc.)

Azure Resource (VM, VMSS, WebApp, AKS, etc.)

GCP Resource (Compute Engine, Cloud Storage, Cloud SQL, GKE, etc.)

3. CROSS-REFERENCE FAILURE MODES
Use EXACT categories below. For each entity:

Select valid chaos scenarios from reference table only

Generate failure propagation mapping:

Root Failure (first break)

Propagation Impact (cascading failures)

Blast Radius (spread extent)

Recovery Path / Mitigation

4. GENERATE CHAOS PLAN (4 scenarios)
Template for each scenario:

Entity (VM, Pod, etc.) - with specific IPs/FQDNs/pod names

Failure Type (from reference only)

Hypothesis (expected breakage)

Steady State Metrics (latency, throughput, error rate baseline)

Failure Injection Method (how to induce chaos)

Propagation Path (downstream dependency failures)

Blast Radius Analysis (impact scope)

Rollback / Abort Criteria

Observability Hooks (metrics, logs, alerts to monitor)

Resiliency Goal (test validation purpose)

OUTPUT FORMAT (3 parts):

Textual topology view - all services + communication flows

Cross-reference table - entities → possible failure scenarios

Full chaos plan - 4 scenarios covering component failures, stress conditions, network conditions, internal/external dependencies

CRITICAL RULES:

Use only provided reference scenarios (no inventions)

Capture ALL internal & external communications

Identify reliability/security hotspots + recommendations

Show multi-level propagation (entity failure → cascading impact)

Treat as deliverable for SRE + Risk Review Board

Include configured replica counts and scale-down targets

Be specific: Include IPs, FQDNs, pod names where available

FAILURE REFERENCE TABLES (Use Only These):

Treat this as if delivering to an SRE + Risk Review Board.the cross referecne info is: #	Category	VM - Linux	VM - Windows
1	Component Failures	Loss of VM	Loss of VM
2		Loss of interfacing system	Loss of interfacing system
3		Loss of DNS	Loss of DNS
4		Loss of LDAP	Loss of LDAP
5		Application process terminated	Application process terminated
6		Application process hung	
7		Loss of DB connectivity	
8		Loss of MQ connectivity	
9		Loss of filesystem	
10		Filesystem corruption	
11		Kernel Panic	
12	Stress Conditions	CPU starvation	CPU starvation
13		Memory starvation	Memory starvation
14		High I/O	High I/O
15		Filesystem full	Drive full
16		Loss of filesystem	
17	Network Conditions	Network latency (ingress/egress)	
18		Packet loss	
19		Packet corruption	
20		Packet duplication	
21	User related	User id locked	User id locked
22		User id expired	Password change
23	Internal failures	Time drift	Time drift
24		Certificate expiry	
25	Batch related	Zero byte file	
26		File format changed	
27		File binary corrupt	
28		Duplicate job run (idempotency)	
29		File text removal (header/trailer)	  for PaaS: Category	Kubernetes / OpenShift
Component Failures	Loss of pods
	Remove service endpoint
	Cordon node
	Delete node
	Delete service
	Delete replicate set
	Remove stateful set
Stress Conditions	High CPU on pods
	High Memory on pods
	High I/O on pods
	Filesystem full on pods
	Scale down deployments/pods
	Scale down replica sets
	Scale down stateful sets
Network conditions	Block Traffic (ALL) - Namespace
	Block Traffic (Target) - Namespace
	Remove network policy
	Block Traffic (ALL) - Pod
	Block Traffic (Target) - Pod , for ews: Resource Type	Category	Scenarios
EC2	Component Failures	Detach random volume
EC2	Component Failures	Restart instances
EC2	Component Failures	Stop instance/instances
EC2	Component Failures	Terminate instance/instances
EC2	Component Failures	Component failures - loss of connectivity to interfacing system
EC2	Component Failures	Component failures - terminate application process
EC2	Component Failures	Component failures - hang application process
EC2	Stress Conditions	High CPU
EC2	Stress Conditions	High Memory
EC2	Stress Conditions	High IO
EC2	Stress Conditions	Disk full
EC2	Network Conditions	Latency (ingress/egress)
EC2	Network Conditions	Packet loss (ingress/egress)
EC2	Network Conditions	Packet corruption (ingress/egress)
EC2	Network Conditions	Packet duplication (ingress/egress)
EC2	Internal Failures	Lock user
EC2	Internal Failures	Expire user
EC2	Internal Failures	Time drift
EC2	Internal Failures	Certificate expiry
EKS	Component Failures	Delete cluster
RDS	Component Failures	Delete DB cluster
RDS	Component Failures	Delete DB cluster endpoint
RDS	Component Failures	Delete DB instance
RDS	Component Failures	Failover DB cluster
RDS	Component Failures	Reboot DB instance
RDS	Component Failures	Stop DB cluster
RDS	Component Failures	Stop DB instance
RDS	Stress Conditions	Block tables
Lambda	Component Failures	Delete event source mapping
Lambda	Component Failures	Delete function concurrency
Lambda	Stress Conditions	Change (put) function timeout
Lambda	Component Failures	Toggle event source mapping
Lambda	Stress Conditions	Change (put) function memory size
ASG	Network Conditions	Change subnets
ASG	Component Failures	Detach random volume
ASG	Component Failures	Detach random instances
ASG	Component Failures	Suspend processes
ASG	Component Failures	Terminate random instances
S3	Component Failures	Delete objects
S3	Component Failures	Toggle versions
Lambda	Component Failures	Memory Failure
DDB	Stress Conditions	Read Write Capacity
ECS	Component Failures	delete_cluster 
ECS	Component Failures	delete_service 
ECS	Component Failures	deregister_container_instance 
ECS	Component Failures	stop_random_tasks 
ECS	Component Failures	stop_task 
ECS	Component Failures	untag_resource 
ECS	Stress Conditions	Reduce number of tasks
Network	Component Failures	disassociate_vpc_from_zone
Elastic Cache	Component Failures	delete_cache_clusters
Elastic Cache	Component Failures	delete_replication_groups
Elastic Cache	Component Failures	reboot_cache_clusters
Elastic Cache	Component Failures	test_failover
ELBv2	Component Failures	delete_load_balancer
ELBv2	Component Failures	deregister_target
EMR	Component Failures	modify_cluster
EMR	Component Failures	modify_instance_fleet
EMR	Component Failures	modify_instance_groups_instance_count
EMR	Component Failures	modify_instance_groups_shrink_policy
IAM	Component Failures	detach_role_policy
EKS	Component Failures	Loss of pods
EKS	Component Failures	Remove service endpoint
EKS	Component Failures	Cordon node
EKS	Component Failures	Delete node
EKS	Component Failures	Delete service
EKS	Component Failures	Delete replicate set
EKS	Component Failures	Remove stateful set
EKS	Stress Conditions	High CPU on pods
EKS	Stress Conditions	High Memory on pods
EKS	Stress Conditions	High I/O on pods
EKS	Stress Conditions	Filesystem full on pods
EKS	Stress Conditions	Scale down pods
EKS	Stress Conditions	Scale down replica sets
EKS	Stress Conditions	Scale down stateful sets
EKS	Network conditions	Block Traffic (ALL) - Namespace
EKS	Network conditions	Block Traffic (Target) - Namespace
EKS	Network conditions	Remove network policy
EKS	Network conditions	Block Traffic (ALL) - Pod
EKS	Network conditions	Block Traffic (Target) - Pod
for azure, Resource Type	Category	Scenarios
VM	Component Failures	Delete VM
VM	Stress Conditions	Disk full
VM	Component Failures	Restart VM
VM	Component Failures	Terminate application process
VM	Component Failures	Hang application process
VM	Stress Conditions	High CPU
VM	Stress Conditions	High Memory
VM	Stress Conditions	High IO
VM	Stress Conditions	Disk full
VM	Network Conditions	Network Latency (ingress/egress)
VM	Network Conditions	Packet loss (ingress/egress)
VM	Network Conditions	Packet corruption (ingress/egress)
VM	Network Conditions	Packet duplication (ingress/egress)
VM	Internal Failures	Lock user
VM	Internal Failures	Expire user
VM	Internal Failures	Time drift
VM	Internal Failures	Certificate expiry
VMSS	Stress Conditions	High IO
VMSS	Component Failures	Deallocate VMSS
VMSS	Component Failures	Restart VMSS
VMSS	Component Failures	Loss of VMSS
VMSS	Network Conditions	Network latency
VMSS	Stress Conditions	High CPU on VMSS instance
Webapp	Component Failures	Delete webapp
Webapp	Component Failures	Restart webapp
Webapp	Component Failures	Stop webapp
AKS	Component Failures	Delete node
AKS	Component Failures	Restart node
AKS	Component Failures	Stop node
AKS	Component Failures	Loss of pods
AKS	Component Failures	Remove service endpoint
AKS	Component Failures	Cordon node
AKS	Component Failures	Delete node
AKS	Component Failures	Delete service
AKS	Component Failures	Delete replicate set
AKS	Component Failures	Remove stateful set
AKS	Stress Conditions	High CPU on pods
AKS	Stress Conditions	High Memory on pods
AKS	Stress Conditions	High I/O on pods
AKS	Stress Conditions	Filesystem full on pods
AKS	Stress Conditions	Scale down pods
AKS	Stress Conditions	Scale down replica sets
AKS	Stress Conditions	Scale down stateful sets
AKS	Network conditions	Block Traffic (ALL) - Namespace
AKS	Network conditions	Block Traffic (Target) - Namespace
AKS	Network conditions	Remove network policy
AKS	Network conditions	Block Traffic (ALL) - Pod
AKS	Network conditions	Block Traffic (Target) - Pod
for GCp Resource Type		Scenarios
Compute Engine		Terminate VM
		Detach storage
		Detach random storage
		Stop VM
		Restart VM
		Loss of interfacing system
		Loss of DNS
		Loss of LDAP
		Application process terminated
		Application process hung
		Loss of DB connectivity
		Loss of MQ connectivity
		Loss of filesystem
		Filesystem corruption
		Kernel Panic
		CPU starvation
		Memory starvation
		High I/O
		Filesystem full
		Loss of filesystem
		Network latency (ingress/egress)
		Packet loss
		Packet corruption
		Packet duplication
		User id locked
		User id expired
		Time drift
		Certificate expiry
		Zero byte file
		File format changed
		File binary corrupt
		Duplicate job run (idempotency)
		File text removal (header/trailer)
Cloud Storage		Delete object
		Toggle version
Cloud SQL		Stop Sql
		Terminate Sql
		Stop Sql
		Reboot Sql
		enable_replication
		Failover
GKE	Networking	namespace_network_block_full
		namespace_network_block_on_target
		remove_reinstate_networkpolicy
	Node	cordon_node
		delete_node
	Pod	filesystem_full_pods
		high_cpu_on_pod
		high_io_on_pod
		high_memory_on_pod
		loss_of_pods
		pod_network_block_full
		pod_network_block_on_target
		scale_down_pods
	Replica set	delete_replica_set
		scale_down_replica_set
	Service	delete_service
	Statefulset	remove_reinstate_statefulset
		scale_down_stateful_set

TARGET OUTPUT: Under 4096 tokens, comprehensive, actionable for SRE team. Don't need to give unnecessary information, stick to the plan"""
        return prompt

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_header():
    """Render the main header"""
    st.markdown(f"""
    <div class="main-header">
    <h1>⚡ Chaos Engineering Plan Generator</h1>
    <p>Analyze OpenSearch logs and generate comprehensive chaos engineering plans</p>
    <small>Version 1.0.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar"""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # OpenSearch Configuration
        st.subheader("OpenSearch Connection")
        endpoint = st.text_input(
            "Endpoint",
            value="http://a535cb3b72b21477894f7c62dda6d607-1503392638.ap-south-1.elb.amazonaws.com:9200/",
            key="os_endpoint"
        )
        username = st.text_input("Username", value="admin", key="os_username")
        password = st.text_input("Password", value="b#Z2xTpR$9MvYkHq", type="password", key="os_password")
        
        # Test Connection Button
        if st.button("Test OpenSearch Connection", key="test_os_button"):
            with st.spinner("Testing connection..."):
                client = OpenSearchClient(endpoint, username, password)
                success, message = client.test_connection()
                
                if success:
                    st.success(message)
                    # Get indices
                    indices = client.get_indices()
                    if indices:
                        st.session_state.os_client = client
                        st.session_state.indices = indices
                        st.session_state.connection_tested = True
                        st.rerun()  # Rerun to update the UI
                else:
                    st.error(message)
        
        # AWS Bedrock Configuration
        st.subheader("AWS Bedrock Configuration")

        # Get default region from environment or use ap-south-1
        default_region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
        region_options = ["us-east-1", "us-west-2", "ap-south-1", "eu-west-1", "ap-northeast-1"]
        default_index = region_options.index(default_region) if default_region in region_options else 2

        aws_region = st.selectbox(
            "AWS Region",
            region_options,
            index=default_index,
            key="aws_region"
        )

        llm_model = st.selectbox(
            "Bedrock Model",
            [
                "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            ],
            key="llm_model"
        )

        st.info("ℹ️ Claude Sonnet 4.5 requires inference profile IDs (e.g., 'global.', 'us.', 'eu.' prefix)")

        # Show credential status
        if os.getenv("AWS_ACCESS_KEY_ID"):
            st.success("✅ AWS credentials loaded from .env file")
        else:
            st.warning("⚠️ No AWS credentials found in .env file")

        if st.button("Test Bedrock Connection", key="test_llm_button"):
            with st.spinner("Testing AWS Bedrock connection..."):
                llm_client = LLMClient(llm_model, aws_region)
                success, message = llm_client.test_connection()

                if success:
                    st.success(message)
                    st.session_state.llm_client = llm_client
                else:
                    st.error(message)
        
        # Analysis Options
        st.subheader("Analysis Options")
        focus_area = st.selectbox(
            "Focus Area", 
            ["All", "Network", "Database", "Storage", "External APIs", "Security"],
            key="focus_area"
        )
        include_security = st.checkbox("Include Security Analysis", True, key="include_security")
        
        st.markdown("---")
        st.caption("Chaos Engineering SRE Tool")

def render_main_content():
    """Render the main content area"""
    
    # If connection is tested and we have indices, show them
    if st.session_state.connection_tested and st.session_state.indices:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📊 Available Indices")
            
            # Create a DataFrame for better display
            indices_df = pd.DataFrame(st.session_state.indices)
            
            # Clean up column names
            if not indices_df.empty:
                indices_df = indices_df[['index', 'health', 'status', 'docs.count', 'store.size']]
                indices_df['docs.count'] = pd.to_numeric(indices_df['docs.count'], errors='coerce')
                indices_df = indices_df.sort_values('docs.count', ascending=False)
                
                # Display indices
                st.dataframe(
                    indices_df,
                    use_container_width=True,
                    column_config={
                        "index": st.column_config.TextColumn("Index Name", width="large"),
                        "health": st.column_config.TextColumn("Health", width="small"),
                        "status": st.column_config.TextColumn("Status", width="small"),
                        "docs.count": st.column_config.NumberColumn("Document Count", format="%d"),
                        "store.size": st.column_config.TextColumn("Storage Size", width="medium")
                    }
                )
                
                # Get index names for dropdown
                index_names = indices_df['index'].tolist()
                
                # Create two columns for index selection and fetch button
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    selected_index = st.selectbox(
                        "Select an index for analysis:",
                        options=index_names,
                        key="index_selector"
                    )
                    st.session_state.selected_index = selected_index
                
                with col_b:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if st.button("📥 Fetch Index Data", type="primary", key="fetch_data_button"):
                        if selected_index and st.session_state.os_client:
                            with st.spinner(f"Fetching data from {selected_index}..."):
                                index_data = st.session_state.os_client.get_index_data(selected_index)
                                
                                if index_data and index_data.get('success'):
                                    st.session_state.index_data = index_data
                                    st.success(f"✅ Successfully fetched {index_data.get('sample_size', 0)} documents")
                                    st.rerun()  # Rerun to show the data summary
                                else:
                                    error_msg = index_data.get('error', 'Unknown error') if index_data else 'No data returned'
                                    st.error(f"❌ Failed to fetch data: {error_msg}")
        
        with col2:
            st.subheader("📈 Connection Status")
            
            # Connection status
            if st.session_state.os_client:
                st.markdown("<div class='status-success'>✅ OpenSearch Connected</div>", unsafe_allow_html=True)
            
            if st.session_state.llm_client:
                st.markdown("<div class='status-success'>✅ AWS Bedrock Connected</div>", unsafe_allow_html=True)
            
            # Selected index info
            if st.session_state.selected_index:
                st.markdown(f"""
                <div class='card'>
                    <strong>Selected Index:</strong><br>
                    <code>{st.session_state.selected_index}</code>
                </div>
                """, unsafe_allow_html=True)
    
    # If we have index data, show summary and generate plan button
    if st.session_state.index_data:
        st.markdown("---")
        
        # Data Summary
        st.subheader("📊 Data Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Documents", f"{st.session_state.index_data.get('total_hits', 0):,}")
        
        with col2:
            st.metric("Fetched Documents", st.session_state.index_data.get('sample_size', 0))
        
        with col3:
            status = "✅ Success" if st.session_state.index_data.get('success') else "❌ Failed"
            st.metric("Status", status)
        
        # Sample Preview
        with st.expander("📋 Preview Sample Document", expanded=False):
            if st.session_state.index_data.get('documents'):
                hits = st.session_state.index_data['documents'].get('hits', {}).get('hits', [])
                if hits:
                    sample = hits[0].get('_source', {})
                    st.json(sample, expanded=False)
        
        # Generate Plan Section
        st.markdown("---")
        st.subheader("⚡ Generate Chaos Plan")
        
        if st.session_state.llm_client:
            # Analysis options from sidebar
            analysis_options = {
                'focus': st.session_state.get('focus_area', 'All'),
                'security': st.session_state.get('include_security', True),
                'include_external': True
            }
            
            # Create two columns for the generate button
            col_gen, col_download = st.columns([1, 1])
            
            with col_gen:
                generate_clicked = st.button("🚀 Generate Chaos Plan", type="primary", key="generate_plan_button")

            # Handle streaming generation outside the column context
            if generate_clicked:
                st.markdown("---")
                st.subheader("📋 Generating Chaos Plan...")
                st.caption("⏳ Streaming response from AWS Bedrock...")

                generator = ChaosPlanGenerator(
                    st.session_state.os_client,
                    st.session_state.llm_client
                )

                start_time = time.time()

                try:
                    # Create the streaming generator
                    stream_generator = generator.generate_plan_streaming(
                        st.session_state.selected_index,
                        st.session_state.index_data,
                        analysis_options
                    )

                    # Use st.write_stream to display the streaming response
                    # This displays text progressively as it's generated
                    full_response = st.write_stream(stream_generator)

                    # Store the complete plan in session state
                    end_time = time.time()
                    st.session_state.chaos_plan = full_response
                    st.session_state.plan_metrics = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": end_time - start_time,
                        "plan_length": len(full_response),
                        "success": True
                    }
                    st.success("✅ Chaos plan generated successfully!")
                    st.rerun()  # Rerun to show the final plan with download option

                except Exception as e:
                    st.error(f"❌ Failed to generate plan: {str(e)}")
            
            # Show generated plan
            if st.session_state.chaos_plan:
                st.markdown("---")
                st.subheader("📋 Generated Chaos Plan")

                st.caption(f"Plan length: {len(st.session_state.chaos_plan):,} characters")
                with st.container(height=800):
                    st.markdown(st.session_state.chaos_plan)
                
                # Download button
                plan_filename = f"chaos_plan_{st.session_state.selected_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                
                with col_download:
                    st.download_button(
                        label="📥 Download Plan",
                        data=st.session_state.chaos_plan,
                        file_name=plan_filename,
                        mime="text/markdown",
                        key="download_plan_button"
                    )
                
                # Display the plan
                st.markdown(st.session_state.chaos_plan)
                
                # Show metrics in expander
                with st.expander("📊 Generation Metrics", expanded=False):
                    if 'plan_metrics' in st.session_state:
                        st.json(st.session_state.plan_metrics)
        else:
            st.warning("⚠️ Please test the AWS Bedrock connection first before generating a plan.")
    
    # Initial state - no connection tested
    elif not st.session_state.connection_tested:
        st.info("👈 Configure OpenSearch connection in the sidebar and click 'Test OpenSearch Connection' to begin.")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application function"""
    
    # Load CSS
    load_custom_css()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()
    
    # Footer
    st.markdown("---")
    st.caption(f"© {datetime.now().year} Chaos Engineering SRE Team | Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()