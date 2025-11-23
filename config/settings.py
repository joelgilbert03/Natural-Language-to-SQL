"""
Configuration management using Pydantic for type safety and validation.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    model_config = ConfigDict(extra='ignore')
    
    readonly_connection_string: str = Field(..., description="Read-only PostgreSQL connection string")
    dba_connection_string: str = Field(..., description="DBA PostgreSQL connection string")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts for queries")


class APISettings(BaseModel):
    """API configuration for LLM services."""
    model_config = ConfigDict(extra='ignore')
    
    groq_api_key: str = Field(..., description="Groq API key for Llama models")
    cloudflare_account_id: str = Field(..., description="Cloudflare account ID")
    cloudflare_auth_token: str = Field(..., description="Cloudflare authentication token")


class UpstashSettings(BaseModel):
    """Upstash Vector database settings."""
    model_config = ConfigDict(extra='ignore')
    
    vector_url: str = Field(..., description="Upstash Vector URL")
    vector_token: str = Field(..., description="Upstash Vector authentication token")


class SecuritySettings(BaseModel):
    """Security and authentication settings."""
    model_config = ConfigDict(extra='ignore')
    
    dba_password: str = Field(..., description="DBA mode access password")
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    session_timeout_hours: int = Field(default=1, description="DBA session timeout in hours")


class Settings(BaseSettings):
    """Main application settings."""
    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra='ignore')
    
    # Database settings
    database: DatabaseSettings
    
    # API settings
    api: APISettings
    
    # Upstash settings
    upstash: UpstashSettings
    
    # Security settings
    security: SecuritySettings
    
    # Application settings
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")


def load_settings() -> Settings:
    """
    Load and validate application settings from environment variables.
    
    Returns:
        Settings: Validated configuration object
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    try:
        # Create nested settings from environment variables
        database_settings = DatabaseSettings(
            readonly_connection_string=os.getenv("NEON_READONLY_CONNECTION_STRING", ""),
            dba_connection_string=os.getenv("NEON_DBA_CONNECTION_STRING", ""),
            query_timeout=int(os.getenv("QUERY_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("MAX_QUERY_RETRIES", "3"))
        )
        
        api_settings = APISettings(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            cloudflare_account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
            cloudflare_auth_token=os.getenv("CLOUDFLARE_AUTH_TOKEN", "")
        )
        
        upstash_settings = UpstashSettings(
            vector_url=os.getenv("UPSTASH_VECTOR_URL", ""),
            vector_token=os.getenv("UPSTASH_VECTOR_TOKEN", "")
        )
        
        security_settings = SecuritySettings(
            dba_password=os.getenv("DBA_PASSWORD", ""),
            enable_audit_logging=os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true",
            session_timeout_hours=int(os.getenv("SESSION_TIMEOUT_HOURS", "1"))
        )
        
        settings = Settings(
            database=database_settings,
            api=api_settings,
            upstash=upstash_settings,
            security=security_settings,
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
        
        return settings
        
    except Exception as e:
        raise ValueError(f"Failed to load settings: {str(e)}")


# Global settings instance
settings = load_settings()
