#!/usr/bin/env python3
"""
Project Cleaner for LLM Gateway
Removes temporary files and cleans up the project
"""

import os
import shutil
from pathlib import Path
from typing import List, Set

def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent

def find_temp_files(project_root: Path) -> List[Path]:
    """Find temporary files in project"""
    temp_files = []
    
    # Common temporary file patterns
    temp_patterns = [
        "*.tmp",
        "*.temp",
        "*.log",
        "*.pid",
        "*.lock",
        "*~",
        ".#*",
        "*.swp",
        "*.swo",
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini"
    ]
    
    for pattern in temp_patterns:
        temp_files.extend(project_root.rglob(pattern))
    
    return temp_files

def find_cache_dirs(project_root: Path) -> List[Path]:
    """Find cache directories"""
    cache_dirs = []
    
    # Common cache directory patterns
    cache_patterns = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        ".tox",
        ".cache",
        "node_modules",
        ".parcel-cache",
        ".next",
        "dist",
        "build"
    ]
    
    for pattern in cache_patterns:
        cache_dirs.extend(project_root.rglob(pattern))
    
    return cache_dirs

def find_duplicate_files(project_root: Path) -> List[Path]:
    """Find duplicate files"""
    duplicates = []
    
    # Known duplicate files
    known_duplicates = [
        "test_request.json",  # Should only be in deployments/
    ]
    
    for filename in known_duplicates:
        files = list(project_root.rglob(filename))
        if len(files) > 1:
            # Keep the one in deployments/, remove others
            for file_path in files:
                if "deployments" not in str(file_path):
                    duplicates.append(file_path)
    
    return duplicates

def clean_project(dry_run: bool = False) -> None:
    """Clean the project"""
    project_root = get_project_root()
    
    print("Cleaning LLM Gateway project...")
    print("=" * 50)
    
    # Find files to clean
    temp_files = find_temp_files(project_root)
    cache_dirs = find_cache_dirs(project_root)
    duplicate_files = find_duplicate_files(project_root)
    
    # Report findings
    print(f"\nFound {len(temp_files)} temporary files")
    print(f"Found {len(cache_dirs)} cache directories")
    print(f"Found {len(duplicate_files)} duplicate files")
    
    if not temp_files and not cache_dirs and not duplicate_files:
        print("\nProject is already clean!")
        return
    
    # Show what will be cleaned
    print("\nFiles to be removed:")
    
    if temp_files:
        print("\nTemporary files:")
        for file_path in temp_files:
            print(f"  - {file_path.relative_to(project_root)}")
    
    if cache_dirs:
        print("\nCache directories:")
        for dir_path in cache_dirs:
            print(f"  - {dir_path.relative_to(project_root)}/")
    
    if duplicate_files:
        print("\nDuplicate files:")
        for file_path in duplicate_files:
            print(f"  - {file_path.relative_to(project_root)}")
    
    if dry_run:
        print("\nDry run mode - no files will be deleted")
        return
    
    # Confirm deletion
    response = input("\nDo you want to proceed with deletion? (y/N): ")
    if response.lower() != 'y':
        print("Cleanup cancelled")
        return
    
    # Perform cleanup
    print("\nRemoving files...")
    
    removed_count = 0
    
    # Remove temporary files
    for file_path in temp_files:
        try:
            file_path.unlink()
            print(f"  Removed: {file_path.relative_to(project_root)}")
            removed_count += 1
        except Exception as e:
            print(f"  Failed to remove {file_path.relative_to(project_root)}: {e}")
    
    # Remove cache directories
    for dir_path in cache_dirs:
        try:
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path.relative_to(project_root)}/")
            removed_count += 1
        except Exception as e:
            print(f"  Failed to remove {dir_path.relative_to(project_root)}/: {e}")
    
    # Remove duplicate files
    for file_path in duplicate_files:
        try:
            file_path.unlink()
            print(f"  Removed: {file_path.relative_to(project_root)}")
            removed_count += 1
        except Exception as e:
            print(f"  Failed to remove {file_path.relative_to(project_root)}: {e}")
    
    print(f"\nCleanup completed! Removed {removed_count} items")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean LLM Gateway project")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without actually cleaning")
    
    args = parser.parse_args()
    
    clean_project(dry_run=args.dry_run)

if __name__ == "__main__":
    main()