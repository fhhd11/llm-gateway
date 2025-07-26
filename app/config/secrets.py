"""
Secrets management system
Supports file-based and environment-based secrets
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
from app.config.environment import env_config

class SecretsManager:
    """Secrets management for different environments"""
    
    def __init__(self):
        self.secrets_dir = Path(__file__).parent / "secrets"
        self.secrets_dir.mkdir(exist_ok=True)
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key from environment or generate one"""
        key = os.getenv("SECRETS_ENCRYPTION_KEY")
        if key:
            return key.encode()
        
        # Generate key for development
        if env_config.is_development():
            key = Fernet.generate_key()
            print(f"Generated encryption key for development: {key.decode()}")
            return key
        
        return None
    
    def _get_secret_file_path(self, secret_name: str) -> Path:
        """Get path to secret file"""
        return self.secrets_dir / f"{secret_name}.txt"
    
    def _get_encrypted_secret_file_path(self, secret_name: str) -> Path:
        """Get path to encrypted secret file"""
        return self.secrets_dir / f"{secret_name}.enc"
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value from multiple sources"""
        
        # 1. Try environment variable first
        env_value = os.getenv(secret_name.upper())
        if env_value:
            return env_value
        
        # 2. Try encrypted file
        encrypted_path = self._get_encrypted_secret_file_path(secret_name)
        if encrypted_path.exists() and self.fernet:
            try:
                encrypted_data = encrypted_path.read_bytes()
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return decrypted_data.decode()
            except Exception:
                pass
        
        # 3. Try plain text file
        secret_path = self._get_secret_file_path(secret_name)
        if secret_path.exists():
            try:
                return secret_path.read_text().strip()
            except Exception:
                pass
        
        # 4. Try environment-specific secret
        env_secret = os.getenv(f"{secret_name.upper()}_{env_config.get_environment_name().upper()}")
        if env_secret:
            return env_secret
        
        return default
    
    def set_secret(self, secret_name: str, value: str, encrypt: bool = True) -> bool:
        """Set secret value"""
        try:
            if encrypt and self.fernet:
                # Save encrypted
                encrypted_data = self.fernet.encrypt(value.encode())
                encrypted_path = self._get_encrypted_secret_file_path(secret_name)
                encrypted_path.write_bytes(encrypted_data)
                return True
            else:
                # Save plain text
                secret_path = self._get_secret_file_path(secret_name)
                secret_path.write_text(value)
                return True
        except Exception:
            return False
    
    def delete_secret(self, secret_name: str) -> bool:
        """Delete secret file"""
        try:
            secret_path = self._get_secret_file_path(secret_name)
            encrypted_path = self._get_encrypted_secret_file_path(secret_name)
            
            if secret_path.exists():
                secret_path.unlink()
            if encrypted_path.exists():
                encrypted_path.unlink()
            
            return True
        except Exception:
            return False
    
    def list_secrets(self) -> Dict[str, bool]:
        """List all available secrets"""
        secrets = {}
        
        # Check plain text files
        for file_path in self.secrets_dir.glob("*.txt"):
            secret_name = file_path.stem
            secrets[secret_name] = False  # Not encrypted
        
        # Check encrypted files
        for file_path in self.secrets_dir.glob("*.enc"):
            secret_name = file_path.stem
            secrets[secret_name] = True  # Encrypted
        
        return secrets
    
    def get_all_secrets(self) -> Dict[str, str]:
        """Get all secrets as dictionary"""
        secrets = {}
        secret_names = self.list_secrets().keys()
        
        for secret_name in secret_names:
            value = self.get_secret(secret_name)
            if value:
                secrets[secret_name] = value
        
        return secrets
    
    def validate_secrets(self, required_secrets: list) -> Dict[str, bool]:
        """Validate that required secrets are available"""
        validation = {}
        
        for secret_name in required_secrets:
            value = self.get_secret(secret_name)
            validation[secret_name] = value is not None
        
        return validation
    
    def export_secrets_template(self, template_path: str) -> bool:
        """Export secrets template for documentation"""
        try:
            template = {
                "environment": env_config.get_environment_name(),
                "required_secrets": [
                    "supabase_url",
                    "supabase_key", 
                    "openai_api_key",
                    "anthropic_api_key",
                    "google_gemini_api_key",
                    "langfuse_secret_key",
                    "langfuse_public_key",
                    "jwt_secret"
                ],
                "optional_secrets": [
                    "redis_password",
                    "database_password"
                ],
                "notes": {
                    "supabase_url": "Supabase project URL",
                    "supabase_key": "Supabase service role key",
                    "openai_api_key": "OpenAI API key for GPT models",
                    "anthropic_api_key": "Anthropic API key for Claude models",
                    "google_gemini_api_key": "Google API key for Gemini models",
                    "langfuse_secret_key": "Langfuse secret key for observability",
                    "langfuse_public_key": "Langfuse public key for observability",
                    "jwt_secret": "JWT secret for token verification",
                    "redis_password": "Redis password (if required)",
                    "database_password": "Database password (if required)"
                }
            }
            
            template_file = Path(template_path)
            template_file.write_text(json.dumps(template, indent=2))
            return True
        except Exception:
            return False

# Global secrets manager instance
secrets_manager = SecretsManager() 