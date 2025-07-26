"""
Configuration utilities for management and validation
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.config.settings import settings
from app.config.environment import env_config
from app.config.secrets import secrets_manager

class ConfigManager:
    """Configuration management utilities"""
    
    @staticmethod
    def export_config_template(output_path: str = "config_template.json") -> bool:
        """Export configuration template"""
        try:
            template = {
                "environment": env_config.get_environment_name(),
                "settings": {
                    "environment": "development|staging|production|testing",
                    "debug": "true|false",
                    "log_level": "DEBUG|INFO|WARNING|ERROR|CRITICAL",
                    "log_format": "json|text",
                    "rate_limit_enabled": "true|false",
                    "rate_limit_storage": "redis|memory",
                    "retry_enabled": "true|false",
                    "circuit_breaker_enabled": "true|false",
                    "langfuse_enabled": "true|false",
                    "prometheus_enabled": "true|false"
                },
                "timeouts": {
                    "request_timeout": "30",
                    "database_timeout": "10", 
                    "redis_timeout": "5",
                    "llm_timeout": "60"
                },
                "database": {
                    "url": "postgresql://user:pass@host:port/db",
                    "pool_size": "5",
                    "max_overflow": "10"
                },
                "redis": {
                    "url": "redis://localhost:6379",
                    "host": "localhost",
                    "port": "6379",
                    "db": "0",
                    "password": "optional",
                    "use_ssl": "false"
                },
                "cors": {
                    "origins": ["http://localhost:3000"],
                    "allowed_hosts": ["localhost"]
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_current_config() -> Dict[str, Any]:
        """Validate current configuration"""
        validation = {
            "environment": {
                "current": env_config.get_environment_name(),
                "valid": True
            },
            "secrets": secrets_manager.validate_secrets([
                "supabase_url", "supabase_key", "jwt_secret"
            ]),
            "settings": settings.validate_configuration(),
            "health": {
                "database_url": bool(settings.database.url),
                "redis_url": bool(settings.redis.url),
                "api_keys": bool(settings.openai_api_key or settings.anthropic_api_key or settings.google_gemini_api_key)
            }
        }
        
        return validation
    
    @staticmethod
    def get_config_summary() -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "environment": env_config.get_environment_name(),
            "debug": settings.debug,
            "log_level": settings.log_level,
            "log_format": settings.log_format,
            "features": {
                "rate_limiting": settings.rate_limit_enabled,
                "retries": settings.retry_enabled,
                "circuit_breakers": settings.circuit_breaker_enabled,
                "langfuse": settings.monitoring.langfuse_enabled,
                "prometheus": settings.monitoring.prometheus_enabled
            },
            "timeouts": {
                "request": settings.timeouts.request_timeout,
                "database": settings.timeouts.database_timeout,
                "redis": settings.timeouts.redis_timeout,
                "llm": settings.timeouts.llm_timeout
            },
            "validation": ConfigManager.validate_current_config()
        }
    
    @staticmethod
    def create_env_file(template_path: str = ".env.template") -> bool:
        """Create .env file template"""
        try:
            template = f"""# LLM Gateway Environment Configuration
# Copy this file to .env and fill in your values

# Environment
ENVIRONMENT=development

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# JWT Configuration
JWT_SECRET=your_jwt_secret_here

# Langfuse Configuration
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here

# Redis Configuration (optional)
REDIS_PASSWORD=your_redis_password_here

# Database Configuration (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/db_name

# Secrets Encryption (optional)
SECRETS_ENCRYPTION_KEY=your_encryption_key_here
"""
            
            with open(template_path, 'w') as f:
                f.write(template)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def list_available_secrets() -> Dict[str, bool]:
        """List all available secrets"""
        return secrets_manager.list_secrets()
    
    @staticmethod
    def set_secret(secret_name: str, value: str, encrypt: bool = True) -> bool:
        """Set a secret value"""
        return secrets_manager.set_secret(secret_name, value, encrypt)
    
    @staticmethod
    def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value"""
        return secrets_manager.get_secret(secret_name, default)
    
    @staticmethod
    def delete_secret(secret_name: str) -> bool:
        """Delete a secret"""
        return secrets_manager.delete_secret(secret_name)

class ConfigValidator:
    """Configuration validation utilities"""
    
    @staticmethod
    def validate_environment() -> bool:
        """Validate environment configuration"""
        valid_environments = ["development", "staging", "production", "testing"]
        return env_config.get_environment_name() in valid_environments
    
    @staticmethod
    def validate_secrets() -> Dict[str, bool]:
        """Validate required secrets"""
        required_secrets = [
            "supabase_url", "supabase_key", "jwt_secret"
        ]
        
        validation = {}
        for secret in required_secrets:
            value = secrets_manager.get_secret(secret)
            validation[secret] = value is not None and value.strip() != ""
        
        return validation
    
    @staticmethod
    def validate_api_keys() -> Dict[str, bool]:
        """Validate API keys"""
        api_keys = {
            "openai": settings.openai_api_key,
            "anthropic": settings.anthropic_api_key,
            "google_gemini": settings.google_gemini_api_key,
            "google": settings.google_api_key
        }
        
        validation = {}
        for name, key in api_keys.items():
            validation[name] = key is not None and key.strip() != ""
        
        return validation
    
    @staticmethod
    def validate_database_config() -> Dict[str, bool]:
        """Validate database configuration"""
        return {
            "url": bool(settings.database.url),
            "pool_size": settings.database.pool_size > 0,
            "max_overflow": settings.database.max_overflow >= 0
        }
    
    @staticmethod
    def validate_redis_config() -> Dict[str, bool]:
        """Validate Redis configuration"""
        return {
            "url": bool(settings.redis.url),
            "host": bool(settings.redis.host),
            "port": 0 < settings.redis.port < 65536,
            "db": 0 <= settings.redis.db <= 15
        }
    
    @staticmethod
    def validate_monitoring_config() -> Dict[str, bool]:
        """Validate monitoring configuration"""
        return {
            "langfuse_enabled": settings.monitoring.langfuse_enabled,
            "langfuse_keys": bool(
                settings.monitoring.langfuse_secret_key and 
                settings.monitoring.langfuse_public_key
            ),
            "prometheus_enabled": settings.monitoring.prometheus_enabled
        }
    
    @staticmethod
    def run_full_validation() -> Dict[str, Any]:
        """Run full configuration validation"""
        return {
            "environment": ConfigValidator.validate_environment(),
            "secrets": ConfigValidator.validate_secrets(),
            "api_keys": ConfigValidator.validate_api_keys(),
            "database": ConfigValidator.validate_database_config(),
            "redis": ConfigValidator.validate_redis_config(),
            "monitoring": ConfigValidator.validate_monitoring_config()
        }

# Global instances
config_manager = ConfigManager()
config_validator = ConfigValidator() 