#!/usr/bin/env python3
"""
Setup Verification Script
Checks if all dependencies and configurations are correct
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print("✓ Python version OK:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("✗ Python version too old. Need 3.8+, have:", f"{version.major}.{version.minor}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'google.oauth2',
        'googleapiclient',
        'selenium',
        'PIL'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            missing.append(package)
    
    if missing:
        print("\nTo install missing packages:")
        print("pip install -r requirements.txt")
        return False
    return True

def check_credentials():
    """Check if credentials.json exists"""
    i