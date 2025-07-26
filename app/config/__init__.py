"""
Configuration Management Module
Provides environment-specific configuration and secrets management
"""

from .environment import env_config, Environment, EnvironmentConfig
from .secrets import secrets_manager, SecretsManager

# Lazy import to avoid initialization issues during testing
def get_settings():
    """Get settings instance (lazy loading)"""
    from .settings import settings
    return settings

def get_Settings_class():
    """Get Settings class (lazy loading)"""
    from .settings import Settings
    return Settings

__all__ = [
    "get_settings",
    "get_Settings_class", 
    "env_config",
    "Environment",
    "EnvironmentConfig",
    "secrets_manager",
    "SecretsManager"
] 