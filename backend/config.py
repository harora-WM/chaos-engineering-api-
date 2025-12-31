"""Configuration module for the backend"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""

    # API Settings
    API_TITLE = "Chaos Engineering Plan Generator API"
    API_DESCRIPTION = "API for generating chaos engineering plans from OpenSearch logs using AWS Bedrock"
    API_VERSION = "1.0.0"

    # CORS Settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # AWS Settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0")

    # Default OpenSearch Settings (optional, can be overridden per request)
    DEFAULT_OPENSEARCH_ENDPOINT = os.getenv("DEFAULT_OPENSEARCH_ENDPOINT", "")
    DEFAULT_OPENSEARCH_USERNAME = os.getenv("DEFAULT_OPENSEARCH_USERNAME", "")
    DEFAULT_OPENSEARCH_PASSWORD = os.getenv("DEFAULT_OPENSEARCH_PASSWORD", "")


settings = Settings()
