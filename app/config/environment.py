"""
Environment-specific configuration management
Supports development, staging, and production environments
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path

class Environment(Enum):
    """Environment enumeration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class EnvironmentConfig:
    """Environment-specific configuration manager"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.config_dir = Path(__file__).parent / "environments"
        self.secrets_dir = Path(__file__).parent / "secrets"
        
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env = os.getenv("ENVIRONMENT", "development").lower()
        
        if env == "production":
            return Environment.PRODUCTION
        elif env == "staging":
            return Environment.STAGING
        elif env == "testing":
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT
    
    def get_environment_name(self) -> str:
        """Get current environment name"""
        return self.environment.value
    
    def is_production(self) -> bool:
        """Check if current environment is production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if current environment is development"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_staging(self) -> bool:
        """Check if current environment is staging"""
        return self.environment == Environment.STAGING
    
    def is_testing(self) -> bool:
        """Check if current environment is testing"""
        return self.environment == Environment.TESTING
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        configs = {
            Environment.DEVELOPMENT: {
                "debug": True,
                "log_level": "DEBUG",
                "rate_limit_enabled": True,
                "retry_enabled": True,
                "circuit_breaker_enabled": True,
                "langfuse_enabled": True,
                "prometheus_enabled": True,
                "redis_url": "redis://localhost:6379",
                "rate_limit_storage": "memory",  # Use memory for development
                "jwt_verify": True,  # Enable JWT verification for development
                "jwt_secret": "eNgFIjCXpALMij51Yiyu0go1pdHhvSEH44MK7QKMTIii/Y3aT9pwIIfTvdBNU4NAh/qX7MTyCC4F7z2eg0D4lg==",  # Supabase JWT secret
                "monitoring_log_level": "DEBUG",
                "log_format": "text",  # More readable for development
                "health_check_interval": 30,  # 30 seconds
                "max_request_size": "10MB",
                "cors_origins": ["http://localhost:3000", "http://localhost:8080"],
                "allowed_hosts": ["localhost", "127.0.0.1"],
                "database_pool_size": 5,
                "database_max_overflow": 10,
                "timeout_settings": {
                    "request_timeout": 30,
                    "database_timeout": 10,
                    "redis_timeout": 5,
                    "llm_timeout": 60
                }
            },
            Environment.STAGING: {
                "debug": False,
                "log_level": "INFO",
                "rate_limit_enabled": True,
                "retry_enabled": True,
                "circuit_breaker_enabled": True,
                "langfuse_enabled": True,
                "prometheus_enabled": True,
                "redis_url": os.getenv("REDIS_URL", "redis://redis:6379"),
                "rate_limit_storage": "redis",
                "jwt_verify": True,
                "monitoring_log_level": "INFO",
                "log_format": "json",
                "health_check_interval": 60,  # 1 minute
                "max_request_size": "10MB",
                "cors_origins": ["https://staging.airflow-ai.com"],
                "allowed_hosts": ["staging.airflow-ai.com"],
                "database_pool_size": 10,
                "database_max_overflow": 20,
                "timeout_settings": {
                    "request_timeout": 30,
                    "database_timeout": 10,
                    "redis_timeout": 5,
                    "llm_timeout": 60
                }
            },
            Environment.PRODUCTION: {
                "debug": False,
                "log_level": "WARNING",
                "rate_limit_enabled": True,
                "retry_enabled": True,
                "circuit_breaker_enabled": True,
                "langfuse_enabled": True,
                "prometheus_enabled": True,
                "redis_url": os.getenv("REDIS_URL", "redis://redis:6379"),
                "rate_limit_storage": "redis",
                "jwt_verify": True,
                "monitoring_log_level": "WARNING",
                "log_format": "json",
                "health_check_interval": 120,  # 2 minutes
                "max_request_size": "10MB",
                "cors_origins": ["https://airflow-ai.com", "https://app.airflow-ai.com"],
                "allowed_hosts": ["airflow-ai.com", "app.airflow-ai.com"],
                "database_pool_size": 20,
                "database_max_overflow": 30,
                "timeout_settings": {
                    "request_timeout": 30,
                    "database_timeout": 10,
                    "redis_timeout": 5,
                    "llm_timeout": 60
                }
            },
            Environment.TESTING: {
                "debug": True,
                "log_level": "DEBUG",
                "rate_limit_enabled": False,
                "retry_enabled": False,
                "circuit_breaker_enabled": False,
                "langfuse_enabled": False,
                "prometheus_enabled": False,
                "redis_url": "redis://localhost:6379",
                "rate_limit_storage": "memory",
                "jwt_verify": False,
                "monitoring_log_level": "DEBUG",
                "log_format": "text",
                "health_check_interval": 10,  # 10 seconds for tests
                "max_request_size": "1MB",
                "cors_origins": ["http://localhost:3000"],
                "allowed_hosts": ["localhost", "127.0.0.1"],
                "database_pool_size": 1,
                "database_max_overflow": 0,
                "timeout_settings": {
                    "request_timeout": 5,
                    "database_timeout": 2,
                    "redis_timeout": 1,
                    "llm_timeout": 10
                }
            }
        }
        
        return configs.get(self.environment, configs[Environment.DEVELOPMENT])
    
    def get_secret_path(self, secret_name: str) -> Optional[Path]:
        """Get path to secret file"""
        secret_file = self.secrets_dir / f"{secret_name}.txt"
        return secret_file if secret_file.exists() else None
    
    def load_secret(self, secret_name: str) -> Optional[str]:
        """Load secret from file"""
        secret_path = self.get_secret_path(secret_name)
        if secret_path and secret_path.exists():
            try:
                return secret_path.read_text().strip()
            except Exception:
                return None
        return None
    
    def get_database_url(self) -> str:
        """Get database URL for current environment"""
        if self.is_testing():
            return "postgresql://test:test@localhost:5432/test_db"
        elif self.is_production():
            return os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/prod_db")
        else:
            # For development, try to get Supabase URL from environment
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                # Fallback to Supabase URL construction
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                if supabase_url and supabase_key:
                    # Extract host from Supabase URL
                    if supabase_url.startswith("https://"):
                        host = supabase_url.replace("https://", "").split(".")[0]
                        database_url = f"postgresql://postgres:{supabase_key}@db.{host}.supabase.co:5432/postgres"
                    else:
                        database_url = f"postgresql://postgres:{supabase_key}@db.{supabase_url}.supabase.co:5432/postgres"
                else:
                    database_url = "postgresql://user:pass@localhost:5432/dev_db"
            
            return database_url
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration for current environment"""
        env_config = self.get_environment_config()
        redis_url = env_config.get("redis_url", "redis://localhost:6379")
        
        # Parse Redis URL
        if redis_url.startswith("redis://"):
            parts = redis_url.replace("redis://", "").split("@")
            if len(parts) == 2:
                auth, host_port = parts
                username, password = auth.split(":") if ":" in auth else (None, auth)
            else:
                host_port = parts[0]
                username, password = None, None
            
            host, port_db = host_port.split(":")
            if "/" in port_db:
                port, db = port_db.split("/")
            else:
                port, db = port_db, "0"
            
            return {
                "host": host,
                "port": int(port),
                "db": int(db),
                "password": password,
                "username": username,
                "ssl": env_config.get("redis_use_ssl", False)
            }
        
        return {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "username": None,
            "ssl": False
        }

# Global environment config instance
env_config = EnvironmentConfig() 