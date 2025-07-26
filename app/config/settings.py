"""
Main settings configuration
Integrates environment-specific config and secrets management
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

from .environment import env_config, Environment
from .secrets import secrets_manager

# Load environment variables
load_dotenv()

class TimeoutSettings(BaseModel):
    """Timeout configuration"""
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    database_timeout: int = Field(default=10, description="Database timeout in seconds")
    redis_timeout: int = Field(default=5, description="Redis timeout in seconds")
    llm_timeout: int = Field(default=60, description="LLM request timeout in seconds")

class CorsSettings(BaseModel):
    """CORS configuration"""
    origins: List[str] = Field(default_factory=list, description="Allowed CORS origins")
    allowed_hosts: List[str] = Field(default_factory=list, description="Allowed hosts")

class DatabaseSettings(BaseModel):
    """Database configuration"""
    url: str = Field(default="postgresql://user:pass@localhost:5432/db", description="Database connection URL")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum overflow connections")

class RedisSettings(BaseModel):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    username: Optional[str] = Field(default=None, description="Redis username")
    use_ssl: bool = Field(default=False, description="Use SSL for Redis connection")

class MonitoringSettings(BaseModel):
    """Monitoring configuration"""
    langfuse_enabled: bool = Field(default=True, description="Enable Langfuse monitoring")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", description="Langfuse host")
    langfuse_public_key: Optional[str] = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: Optional[str] = Field(default=None, description="Langfuse secret key")
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    log_level: str = Field(default="INFO", description="Logging level")

class SecuritySettings(BaseModel):
    """Security configuration"""
    jwt_verify: bool = Field(default=False, description="Enable JWT verification")
    jwt_secret: Optional[str] = Field(default="", description="JWT secret key")
    allowed_hosts: List[str] = Field(default_factory=list, description="Allowed hosts")

class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", description="Current environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API Keys (from secrets)
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase service role key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    google_gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    
    # Business logic
    lite_llm_markup: float = Field(default=0.25, description="LiteLLM markup percentage")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_storage: str = Field(default="redis", description="Rate limit storage backend")
    
    # Retry settings
    retry_enabled: bool = Field(default=True, description="Enable retries")
    retry_max_attempts: int = Field(default=3, description="Maximum retry attempts")
    retry_base_delay: float = Field(default=1.0, description="Base delay for retries")
    retry_max_delay: float = Field(default=60.0, description="Maximum delay for retries")
    retry_exponential_base: float = Field(default=2.0, description="Exponential base for retries")
    retry_jitter: bool = Field(default=True, description="Enable jitter for retries")
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = Field(default=True, description="Enable circuit breakers")
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_recovery_timeout: float = Field(default=60.0, description="Circuit breaker recovery timeout")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    
    # Health checks
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # Request limits
    max_request_size: str = Field(default="10MB", description="Maximum request size")
    
    # Timeouts
    timeouts: TimeoutSettings = Field(default_factory=TimeoutSettings)
    
    # CORS
    cors: CorsSettings = Field(default_factory=CorsSettings)
    
    # Database
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    # Redis
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    # Monitoring
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    # Security
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        extra = "ignore"  # Ignore extra fields from environment variables
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_environment_config()
        self._load_secrets()
    
    def _load_environment_config(self):
        """Load environment-specific configuration"""
        env_config_data = env_config.get_environment_config()
        
        # Update settings with environment config
        for key, value in env_config_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Set environment
        self.environment = env_config.get_environment_name()
        self.debug = env_config_data.get("debug", False)
        
        # Load database URL from environment config
        database_url = env_config.get_database_url()
        if database_url:
            self.database.url = database_url
        
        # Load nested configurations
        self.timeouts = TimeoutSettings(**env_config_data.get("timeout_settings", {}))
        self.cors.origins = env_config_data.get("cors_origins", [])
        self.cors.allowed_hosts = env_config_data.get("allowed_hosts", [])
        self.database.pool_size = env_config_data.get("database_pool_size", 5)
        self.database.max_overflow = env_config_data.get("database_max_overflow", 10)
        
        # Load security settings
        self.security.jwt_verify = env_config_data.get("jwt_verify", False)
        if "jwt_secret" in env_config_data:
            self.security.jwt_secret = env_config_data["jwt_secret"]
        
        # Load Redis config
        redis_config = env_config.get_redis_config()
        # Filter out None values to avoid validation errors
        filtered_redis_config = {k: v for k, v in redis_config.items() if v is not None}
        self.redis = RedisSettings(**filtered_redis_config)
    
    def _load_secrets(self):
        """Load secrets from secrets manager"""
        # Load secrets that exist in the Settings model
        settings_secrets = [
            "supabase_url", "supabase_key", "openai_api_key", 
            "anthropic_api_key", "google_gemini_api_key", "google_api_key"
        ]
        
        for secret_name in settings_secrets:
            if hasattr(self, secret_name):
                secret_value = secrets_manager.get_secret(secret_name)
                if secret_value and not getattr(self, secret_name, None):
                    setattr(self, secret_name, secret_value)
        
        # Update nested configurations with secrets
        if self.monitoring.langfuse_secret_key is None:
            self.monitoring.langfuse_secret_key = secrets_manager.get_secret("langfuse_secret_key")
        
        if self.monitoring.langfuse_public_key is None:
            self.monitoring.langfuse_public_key = secrets_manager.get_secret("langfuse_public_key")
        
        if self.security.jwt_secret is None or self.security.jwt_secret == "":
            self.security.jwt_secret = secrets_manager.get_secret("jwt_secret")
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate configuration completeness"""
        validation = {
            "environment": True,
            "supabase": bool(self.supabase_url and self.supabase_key),
            "api_keys": bool(self.openai_api_key or self.anthropic_api_key or self.google_gemini_api_key),
            "jwt": bool(self.security.jwt_secret),
            "monitoring": bool(self.monitoring.langfuse_secret_key and self.monitoring.langfuse_public_key),
            "redis": bool(self.redis.url),
            "database": bool(self.database.url)
        }
        
        return validation
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for health checks"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_storage": self.rate_limit_storage,
            "retry_enabled": self.retry_enabled,
            "circuit_breaker_enabled": self.circuit_breaker_enabled,
            "monitoring": {
                "langfuse_enabled": self.monitoring.langfuse_enabled,
                "prometheus_enabled": self.monitoring.prometheus_enabled
            },
            "validation": self.validate_configuration()
        }

# Global settings instance - lazy loading
_settings_instance = None

def get_settings():
    """Get or create settings instance (lazy loading)"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

# For backward compatibility
settings = get_settings() 