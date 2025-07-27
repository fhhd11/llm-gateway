#!/usr/bin/env python3
"""
Pre-commit hook for LLM Gateway
Automatically checks documentation consistency before commits
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd: list) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def check_documentation() -> bool:
    """Check if documentation is up to date"""
    print("🔍 Checking documentation consistency...")
    return run_command([sys.executable, "scripts/check_documentation.py"])

def run_tests() -> bool:
    """Run tests"""
    print("🧪 Running tests...")
    return run_command([sys.executable, "-m", "pytest", "tests/", "-v"])

def run_linting() -> bool:
    """Run code linting"""
    print("🔍 Running linting...")
    return run_command([sys.executable, "-m", "flake8", "app/", "tests/"])

def run_formatting() -> bool:
    """Run code formatting"""
    print("🎨 Running code formatting...")
    return run_command([sys.executable, "-m", "black", "--check", "app/", "tests/"])

def main():
    """Main pre-commit hook function"""
    print("🚀 Running pre-commit checks...")
    print("=" * 50)
    
    checks = [
        ("Documentation", check_documentation),
        ("Tests", run_tests),
        ("Linting", run_linting),
        ("Formatting", run_formatting),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"\n📋 Running {check_name} check...")
        if not check_func():
            failed_checks.append(check_name)
    
    if failed_checks:
        print(f"\n❌ Pre-commit checks failed: {', '.join(failed_checks)}")
        print("💡 Please fix the issues above before committing")
        return False
    else:
        print("\n✅ All pre-commit checks passed!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)