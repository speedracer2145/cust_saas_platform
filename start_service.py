#!/usr/bin/env python3
"""
Startup script for the RoBERTa Sentiment Analysis Service

This script provides an easy way to start the service with proper configuration.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        # Set console output encoding to UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # If reconfiguration fails, continue without emojis
        pass


def check_requirements():
    """Check if all requirements are installed."""
    try:
        import torch
        import transformers
        import fastapi
        import uvicorn
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ["data", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directory '{directory}' ready")


def start_service(host="0.0.0.0", port=8000, reload=False, log_level="info"):
    """Start the FastAPI service."""
    print(f"🚀 Starting RoBERTa Sentiment Analysis Service...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Log Level: {log_level}")
    print(f"   API Docs: http://localhost:{port}/docs")
    print(f"   App UI:   http://localhost:{port}/")
    print("=" * 50)
    
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Build uvicorn command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port),
        "--log-level", log_level
    ]
    
    if reload:
        cmd.append("--reload")
    
    # Start the service
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Service failed to start: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Start RoBERTa Sentiment Analysis Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], 
                       help="Log level (default: info)")
    parser.add_argument("--skip-checks", action="store_true", help="Skip requirement checks")
    
    args = parser.parse_args()
    
    print("🔧 RoBERTa Sentiment Analysis Service Startup")
    print("=" * 50)
    
    # Check requirements
    if not args.skip_checks:
        if not check_requirements():
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Set environment variables
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    os.environ["LOG_LEVEL"] = args.log_level
    
    # Start service
    start_service(args.host, args.port, args.reload, args.log_level)


if __name__ == "__main__":
    main()
