#!/usr/bin/env python3
"""
Configuration Management CLI
Provides command-line interface for managing LLM Gateway configuration
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.utils import config_manager, config_validator
from app.config.settings import settings
from app.config.environment import env_config
from app.config.secrets import secrets_manager

def print_json(data: Dict[str, Any], indent: int = 2):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=indent))

def cmd_show_config(args):
    """Show current configuration"""
    if args.summary:
        summary = config_manager.get_config_summary()
        print_json(summary)
    else:
        # Show full configuration
        config_data = {
            "environment": env_config.get_environment_name(),
            "settings": {
                "environment": settings.environment,
                "debug": settings.debug,
                "log_level": settings.log_level,
                "log_format": settings.log_format,
                "rate_limit_enabled": settings.rate_limit_enabled,
                "rate_limit_storage": settings.rate_limit_storage,
                "retry_enabled": settings.retry_enabled,
                "circuit_breaker_enabled": settings.circuit_breaker_enabled,
                "langfuse_enabled": settings.monitoring.langfuse_enabled,
                "prometheus_enabled": settings.monitoring.prometheus_enabled
            },
            "timeouts": {
                "request": settings.timeouts.request_timeout,
                "database": settings.timeouts.database_timeout,
                "redis": settings.timeouts.redis_timeout,
                "llm": settings.timeouts.llm_timeout
            },
            "database": {
                "url": settings.database.url,
                "pool_size": settings.database.pool_size,
                "max_overflow": settings.database.max_overflow
            },
            "redis": {
                "url": settings.redis.url,
                "host": settings.redis.host,
                "port": settings.redis.port,
                "db": settings.redis.db,
                "use_ssl": settings.redis.use_ssl
            },
            "cors": {
                "origins": settings.cors.origins,
                "allowed_hosts": settings.cors.allowed_hosts
            }
        }
        print_json(config_data)

def cmd_validate_config(args):
    """Validate configuration"""
    validation = config_validator.run_full_validation()
    
    if args.json:
        print_json(validation)
    else:
        print("🔍 Configuration Validation Results:")
        print("=" * 50)
        
        # Environment
        env_valid = validation["environment"]
        print(f"🌍 Environment: {'✅ Valid' if env_valid else '❌ Invalid'}")
        
        # Secrets
        print("\n🔐 Secrets:")
        for secret, valid in validation["secrets"].items():
            status = "✅ Valid" if valid else "❌ Missing"
            print(f"  {secret}: {status}")
        
        # API Keys
        print("\n🔑 API Keys:")
        for api, valid in validation["api_keys"].items():
            status = "✅ Valid" if valid else "❌ Missing"
            print(f"  {api}: {status}")
        
        # Database
        print("\n🗄️ Database:")
        for item, valid in validation["database"].items():
            status = "✅ Valid" if valid else "❌ Invalid"
            print(f"  {item}: {status}")
        
        # Redis
        print("\n📦 Redis:")
        for item, valid in validation["redis"].items():
            status = "✅ Valid" if valid else "❌ Invalid"
            print(f"  {item}: {status}")
        
        # Monitoring
        print("\n📊 Monitoring:")
        for item, valid in validation["monitoring"].items():
            status = "✅ Valid" if valid else "❌ Invalid"
            print(f"  {item}: {status}")
        
        # Overall status
        all_valid = all(
            validation["environment"] and
            all(validation["secrets"].values()) and
            any(validation["api_keys"].values()) and
            all(validation["database"].values()) and
            all(validation["redis"].values())
        )
        
        print("\n" + "=" * 50)
        if all_valid:
            print("🎉 Configuration is valid and ready to use!")
        else:
            print("⚠️ Configuration has issues. Please fix the problems above.")

def cmd_list_secrets(args):
    """List available secrets"""
    secrets = config_manager.list_available_secrets()
    
    if args.json:
        print_json(secrets)
    else:
        print("🔐 Available Secrets:")
        print("=" * 30)
        for secret_name, encrypted in secrets.items():
            status = "🔒 Encrypted" if encrypted else "📄 Plain text"
            print(f"{secret_name}: {status}")

def cmd_set_secret(args):
    """Set a secret value"""
    success = config_manager.set_secret(args.name, args.value, args.encrypt)
    
    if success:
        print(f"✅ Secret '{args.name}' set successfully")
    else:
        print(f"❌ Failed to set secret '{args.name}'")
        sys.exit(1)

def cmd_get_secret(args):
    """Get a secret value"""
    value = config_manager.get_secret(args.name)
    
    if value:
        if args.mask:
            # Mask the value for security
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
            print(f"{args.name}: {masked}")
        else:
            print(f"{args.name}: {value}")
    else:
        print(f"❌ Secret '{args.name}' not found")
        sys.exit(1)

def cmd_delete_secret(args):
    """Delete a secret"""
    success = config_manager.delete_secret(args.name)
    
    if success:
        print(f"✅ Secret '{args.name}' deleted successfully")
    else:
        print(f"❌ Failed to delete secret '{args.name}'")
        sys.exit(1)

def cmd_export_template(args):
    """Export configuration template"""
    success = config_manager.export_config_template(args.output)
    
    if success:
        print(f"✅ Configuration template exported to '{args.output}'")
    else:
        print(f"❌ Failed to export template to '{args.output}'")
        sys.exit(1)

def cmd_create_env_template(args):
    """Create .env template"""
    success = config_manager.create_env_file(args.output)
    
    if success:
        print(f"✅ .env template created at '{args.output}'")
        print("📝 Please copy this file to .env and fill in your values")
    else:
        print(f"❌ Failed to create .env template at '{args.output}'")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="LLM Gateway Configuration Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python config_cli.py show-config --summary
  python config_cli.py validate-config
  python config_cli.py list-secrets
  python config_cli.py set-secret supabase_url "https://your-project.supabase.co"
  python config_cli.py get-secret supabase_url --mask
  python config_cli.py export-template config.json
  python config_cli.py create-env-template .env.example
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Show config command
    show_parser = subparsers.add_parser("show-config", help="Show current configuration")
    show_parser.add_argument("--summary", action="store_true", help="Show summary only")
    show_parser.set_defaults(func=cmd_show_config)
    
    # Validate config command
    validate_parser = subparsers.add_parser("validate-config", help="Validate configuration")
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")
    validate_parser.set_defaults(func=cmd_validate_config)
    
    # List secrets command
    list_parser = subparsers.add_parser("list-secrets", help="List available secrets")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.set_defaults(func=cmd_list_secrets)
    
    # Set secret command
    set_parser = subparsers.add_parser("set-secret", help="Set a secret value")
    set_parser.add_argument("name", help="Secret name")
    set_parser.add_argument("value", help="Secret value")
    set_parser.add_argument("--no-encrypt", dest="encrypt", action="store_false", help="Don't encrypt the secret")
    set_parser.set_defaults(func=cmd_set_secret)
    
    # Get secret command
    get_parser = subparsers.add_parser("get-secret", help="Get a secret value")
    get_parser.add_argument("name", help="Secret name")
    get_parser.add_argument("--mask", action="store_true", help="Mask the value for security")
    get_parser.set_defaults(func=cmd_get_secret)
    
    # Delete secret command
    delete_parser = subparsers.add_parser("delete-secret", help="Delete a secret")
    delete_parser.add_argument("name", help="Secret name")
    delete_parser.set_defaults(func=cmd_delete_secret)
    
    # Export template command
    export_parser = subparsers.add_parser("export-template", help="Export configuration template")
    export_parser.add_argument("output", help="Output file path")
    export_parser.set_defaults(func=cmd_export_template)
    
    # Create env template command
    env_parser = subparsers.add_parser("create-env-template", help="Create .env template")
    env_parser.add_argument("output", help="Output file path")
    env_parser.set_defaults(func=cmd_create_env_template)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 