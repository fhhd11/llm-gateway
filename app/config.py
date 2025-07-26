"""
Legacy config module - now uses the new configuration system
This module provides backward compatibility
"""

from .config.settings import settings, Settings
from .config.environment import env_config, Environment
from .config.secrets import secrets_manager

# Re-export for backward compatibility
__all__ = ["settings", "Settings", "env_config", "Environment", "secrets_manager"]