#!/usr/bin/env python3
"""
Documentation Checker for LLM Gateway
Checks if documentation is up to date with the codebase
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_python_files(directory: Path) -> List[Path]:
    """Get all Python files in directory"""
    return list(directory.rglob("*.py"))

def extract_endpoints_from_code() -> Set[str]:
    """Extract API endpoints from FastAPI code"""
    endpoints = set()
    
    # Check main.py
    main_py = project_root / "app" / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find @app.get and @app.post decorators
            for line in content.split('\n'):
                if '@app.get(' in line or '@app.post(' in line:
                    match = re.search(r'@app\.(get|post)\(["\']([^"\']+)["\']', line)
                    if match:
                        endpoints.add(f"{match.group(1).upper()} {match.group(2)}")
    
    # Check api.py
    api_py = project_root / "app" / "routers" / "api.py"
    if api_py.exists():
        with open(api_py, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find @router.get and @router.post decorators
            for line in content.split('\n'):
                if '@router.get(' in line or '@router.post(' in line:
                    match = re.search(r'@router\.(get|post)\(["\']([^"\']+)["\']', line)
                    if match:
                        endpoints.add(f"{match.group(1).upper()} {match.group(2)}")
    
    return endpoints

def extract_endpoints_from_docs() -> Set[str]:
    """Extract API endpoints from documentation"""
    endpoints = set()
    
    api_ref = project_root / "docs" / "API_REFERENCE.md"
    if api_ref.exists():
        with open(api_ref, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find endpoint definitions
            for line in content.split('\n'):
                if '#### ' in line and ('GET' in line or 'POST' in line):
                    match = re.search(r'#### (GET|POST) ([^\n]+)', line)
                    if match:
                        endpoints.add(f"{match.group(1)} {match.group(2).strip()}")
    
    return endpoints

def extract_models_from_code() -> Set[str]:
    """Extract supported models from code"""
    models = set()
    
    litellm_service = project_root / "app" / "services" / "litellm_service.py"
    if litellm_service.exists():
        with open(litellm_service, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find model definitions in router
            for line in content.split('\n'):
                if '"model_name":' in line:
                    match = re.search(r'"model_name":\s*"([^"]+)"', line)
                    if match:
                        models.add(match.group(1))
    
    return models

def extract_models_from_docs() -> Set[str]:
    """Extract supported models from documentation"""
    models = set()
    
    # Check README.md
    readme = project_root / "README.md"
    if readme.exists():
        with open(readme, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find model table
            for line in content.split('\n'):
                if '|' in line and ('gpt' in line.lower() or 'claude' in line.lower() or 'gemini' in line.lower()):
                    parts = line.split('|')
                    if len(parts) >= 3:
                        model_part = parts[2].strip()
                        if model_part and not model_part.startswith('--'):
                            models.update([m.strip() for m in model_part.split(',')])
    
    return models

def extract_env_vars_from_code() -> Set[str]:
    """Extract environment variables from code"""
    env_vars = set()
    
    # Check settings.py
    settings_py = project_root / "app" / "config" / "settings.py"
    if settings_py.exists():
        with open(settings_py, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find Field definitions with env_file
            for line in content.split('\n'):
                if 'Field(' in line and 'description=' in line:
                    # Look for common env var patterns
                    if 'api_key' in line.lower() or 'secret' in line.lower() or 'url' in line.lower():
                        # Try to extract variable name
                        match = re.search(r'(\w+):\s*str\s*=', line)
                        if match:
                            env_vars.add(match.group(1).upper())
    
    return env_vars

def extract_env_vars_from_example() -> Set[str]:
    """Extract environment variables from env.example"""
    env_vars = set()
    
    env_example = project_root / "env.example"
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    var_name = line.split('=')[0]
                    env_vars.add(var_name)
    
    return env_vars

def check_file_structure() -> Dict[str, bool]:
    """Check if documented file structure matches actual structure"""
    structure = {}
    
    # Check if main directories exist
    main_dirs = ['app', 'deployments', 'docs', 'tests']
    for dir_name in main_dirs:
        structure[f"Directory {dir_name}/ exists"] = (project_root / dir_name).exists()
    
    # Check if main files exist
    main_files = [
        'README.md',
        'pyproject.toml',
        'requirements.txt',
        'env.example',
        'Makefile'
    ]
    for file_name in main_files:
        structure[f"File {file_name} exists"] = (project_root / file_name).exists()
    
    return structure

def main():
    """Main documentation check function"""
    print("Checking documentation consistency...")
    print("=" * 50)
    
    issues = []
    warnings = []
    
    # Check API endpoints
    print("\nChecking API endpoints...")
    code_endpoints = extract_endpoints_from_code()
    docs_endpoints = extract_endpoints_from_docs()
    
    missing_in_docs = code_endpoints - docs_endpoints
    extra_in_docs = docs_endpoints - code_endpoints
    
    if missing_in_docs:
        issues.append(f"Endpoints missing in documentation: {missing_in_docs}")
    if extra_in_docs:
        warnings.append(f"Endpoints in docs but not in code: {extra_in_docs}")
    
    # Check models
    print("Checking supported models...")
    code_models = extract_models_from_code()
    docs_models = extract_models_from_docs()
    
    missing_in_docs = code_models - docs_models
    extra_in_docs = docs_models - code_models
    
    if missing_in_docs:
        issues.append(f"Models missing in documentation: {missing_in_docs}")
    if extra_in_docs:
        warnings.append(f"Models in docs but not in code: {extra_in_docs}")
    
    # Check environment variables
    print("Checking environment variables...")
    code_env_vars = extract_env_vars_from_code()
    example_env_vars = extract_env_vars_from_example()
    
    missing_in_example = code_env_vars - example_env_vars
    extra_in_example = example_env_vars - code_env_vars
    
    if missing_in_example:
        warnings.append(f"Env vars in code but not in env.example: {missing_in_example}")
    if extra_in_example:
        warnings.append(f"Env vars in env.example but not in code: {extra_in_example}")
    
    # Check file structure
    print("Checking file structure...")
    structure_checks = check_file_structure()
    
    for check, result in structure_checks.items():
        if not result:
            issues.append(f"Structure issue: {check}")
    
    # Report results
    print("\nResults:")
    print("=" * 50)
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nNo critical issues found")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\nNo warnings")
    
    # Summary
    print(f"\nSummary:")
    print(f"  - API endpoints in code: {len(code_endpoints)}")
    print(f"  - API endpoints in docs: {len(docs_endpoints)}")
    print(f"  - Models in code: {len(code_models)}")
    print(f"  - Models in docs: {len(docs_models)}")
    print(f"  - Env vars in code: {len(code_env_vars)}")
    print(f"  - Env vars in example: {len(example_env_vars)}")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)