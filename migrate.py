#!/usr/bin/env python3
"""
Migration Script for Social Deduction Game Arena
------------------------------------------------
This script helps automate the refactoring process by creating the new directory structure
and moving files to their appropriate locations.
"""

import os
import shutil
from pathlib import Path


def create_directory_structure():
    """Create the new modular directory structure"""
    print("Creating new directory structure...")
    
    directories = [
        "src/game",
        "src/agents", 
        "src/llm",
        "src/experiments",
        "utils",
        "config",
        "rules/sample_rules",
        "rules/generated_rules",
        "tests",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}/")


def main():
    """Main migration function"""
    print("Social Deduction Game Arena - Migration Script")
    print("=" * 50)
    
    try:
        create_directory_structure()
        print("\n🎉 Directory structure created successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")


if __name__ == "__main__":
    main() 