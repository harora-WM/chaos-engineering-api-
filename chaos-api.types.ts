/**
 * TypeScript types for Chaos Engineering API
 * Base URL: https://chaos-engineering-api.onrender.com
 */

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface OpenSearchConfig {
  endpoint: string;
  username: string;
  password: string;
}

export interface AWSBedrockConfig {
  model?: string; // Default: "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
  region?: string; // Default: "ap-south-1"
}

export interface AnalysisOptions {
  focus?: "All" | "Network" | "Database" | "Storage" | "External APIs" | "Security";
  security?: boolean; // Default: true
  include_external?: boolean; // Default: true
}

export interface TestConnectionRequest {
  endpoint: string;
  username: string;
  password: string;
}

export interface GetIndicesRequest {
  endpoint: string;
  username: string;
  password: string;
}

export interface FetchIndexDataRequest {
  endpoint: string;
  username: string;
  password: string;
  index_name: string;
}

export interface GeneratePlanRequest {
  index_name: string;
  opensearch_config: OpenSearchConfig;
  aws_config: AWSBedrockConfig;
  analysis_options?: AnalysisOptions;
}

// ============================================================================
// RESPONSE TYPES
// ============================================================================

export interface HealthResponse {
  status: string;
  message: string;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
}

export interface IndexInfo {
  index: string;
  health: string;
  status: string;
  "docs.count"?: string;
  "store.size"?: string;
  pri?: string;
  rep?: string;
}

export interface GetIndicesResponse {
  success: boolean;
  indices: IndexInfo[];
  error?: string;
}

export interface FetchIndexDataResponse {
  success: boolean;
  mapping?: Record<string, any>;
  documents?: Record<string, any>;
  sample_size?: number;
  total_hits?: number;
  took_ms?: number;
  error?: string;
}

export interface GeneratePlanMetrics {
  start_time: number;
  end_time?: number;
  duration_seconds?: number;
  plan_length?: number;
  success: boolean;
  error?: string;
}

export interface GeneratePlanResponse {
  success: boolean;
  plan?: string;
  metrics?: GeneratePlanMetrics;
  error?: string;
}

// ============================================================================
// API CLIENT CLASS
// ============================================================================

export class ChaosEngineeringAPI {
  private baseUrl: string;

  constructor(baseUrl: string = "https://chaos-engineering-api.onrender.com") {
    this.baseUrl = baseUrl.replace(/\/$/, ""); // Remove trailing slash
  }

  /**
   * Health check
   */
  async health(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  /**
   * Test OpenSearch connection
   */
  async testOpenSearchConnection(
    config: TestConnectionRequest
  ): Promise<TestConnectionResponse> {
    const response = await fetch(`${this.baseUrl}/api/opensearch/test-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    return response.json();
  }

  /**
   * Get OpenSearch indices
   */
  async getIndices(config: GetIndicesRequest): Promise<GetIndicesResponse> {
    const response = await fetch(`${this.baseUrl}/api/opensearch/indices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    return response.json();
  }

  /**
   * Fetch data from specific index
   */
  async fetchIndexData(
    request: FetchIndexDataRequest
  ): Promise<FetchIndexDataResponse> {
    const response = await fetch(`${this.baseUrl}/api/opensearch/fetch-data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return response.json();
  }

  /**
   * Test AWS Bedrock connection
   */
  async testBedrockConnection(
    config: AWSBedrockConfig
  ): Promise<TestConnectionResponse> {
    const response = await fetch(`${this.baseUrl}/api/bedrock/test-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    return response.json();
  }

  /**
   * Generate chaos plan (non-streaming)
   */
  async generateChaosPlan(
    request: GeneratePlanRequest
  ): Promise<GeneratePlanResponse> {
    const response = await fetch(`${this.baseUrl}/api/chaos/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return response.json();
  }

  /**
   * Generate chaos plan with streaming (Server-Sent Events)
   */
  async *generateChaosPlanStream(
    request: GeneratePlanRequest
  ): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${this.baseUrl}/api/chaos/generate-stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.body) {
      throw new Error("ReadableStream not supported");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6); // Remove "data: " prefix
            if (data.trim()) {
              yield data;
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

// ============================================================================
// USAGE EXAMPLE
// ============================================================================

/*
// Initialize the API client
const api = new ChaosEngineeringAPI();

// Example 1: Health check
const health = await api.health();
console.log(health);

// Example 2: Get OpenSearch indices
const indicesResponse = await api.getIndices({
  endpoint: "http://your-opensearch:9200",
  username: "admin",
  password: "password"
});

if (indicesResponse.success) {
  console.log("Indices:", indicesResponse.indices);
}

// Example 3: Generate chaos plan
const planResponse = await api.generateChaosPlan({
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
});

if (planResponse.success) {
  console.log("Chaos Plan:", planResponse.plan);
}

// Example 4: Streaming generation
for await (const chunk of api.generateChaosPlanStream({
  index_name: "logs-2024",
  opensearch_config: { ... },
  aws_config: { ... }
})) {
  console.log("Chunk:", chunk);
  // Update UI progressively
}
*/
