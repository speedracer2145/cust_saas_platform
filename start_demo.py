#!/usr/bin/env python3
"""
Professional Demo Starter for RoBERTa Sentiment Analysis

This script helps you start the professional demo quickly.
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def print_banner():
    """Print a nice banner."""
    print("=" * 70)
    print("🚀 RoBERTa Sentiment Analysis - Professional Demo")
    print("=" * 70)
    print("Final Year Project - Enhanced Dashboard")
    print()

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check if we're in the right directory
    if not Path("start_service.py").exists():
        print("❌ Please run this script from the roberta directory")
        return False
    
    # Check if model exists
    if not Path("models/roberta-sentiment").exists():
        print("❌ Model not found. Please ensure the model is in models/roberta-sentiment/")
        return False
    
    # Check if CSV data exists
    if not Path("amazon_30_customers_unique_suggestions.csv").exists():
        print("⚠️  CSV data file not found. Demo will work with limited sample data.")
    
    print("✅ Requirements check completed")
    return True

def start_service():
    """Start the sentiment analysis service."""
    print("\n🚀 Starting RoBERTa Sentiment Analysis Service...")
    print("This may take a moment to load the model...")
    
    try:
        # Start the service in the background
        process = subprocess.Popen(
            [sys.executable, "start_service.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for the service to start
        print("⏳ Loading model and starting service...")
        time.sleep(10)
        
        # Check if service is running
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Service started successfully!")
                return process
            else:
                print("❌ Service health check failed")
                return None
        except:
            print("⏳ Service is still starting up...")
            time.sleep(5)
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Service started successfully!")
                    return process
            except:
                print("❌ Service failed to start properly")
                return None
                
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        return None

def open_dashboard():
    """Open the professional dashboard."""
    print("\n🌐 Opening Professional Dashboard...")
    dashboard_url = "http://localhost:8000/professional_dashboard.html"
    
    try:
        webbrowser.open(dashboard_url)
        print(f"✅ Dashboard opened: {dashboard_url}")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print(f"Please manually open: {dashboard_url}")

def show_instructions():
    """Show usage instructions."""
    print("\n📋 Dashboard Features:")
    print("  🏠 Dashboard    - Overview with live statistics and charts")
    print("  🔍 Analyze     - Single text sentiment analysis")
    print("  📊 Batch       - Bulk text analysis")
    print("  💡 Suggestions - AI-powered recommendations")
    print("  📈 Insights    - Detailed analytics and trends")
    
    print("\n🎯 For Final Year Project Demo:")
    print("  1. Start with the Dashboard tab to show overview")
    print("  2. Use Analyze tab to demonstrate real-time analysis")
    print("  3. Show Suggestions tab for AI recommendations")
    print("  4. Navigate to Insights for detailed analytics")
    
    print("\n🔗 Additional Resources:")
    print("  📚 API Docs: http://localhost:8000/docs")
    print("  📖 Setup Guide: PROFESSIONAL_SETUP.md")
    print("  💾 Load Data: python load_sample_data.py")

def main():
    """Main function."""
    print_banner()
    
    if not check_requirements():
        print("\n❌ Requirements not met. Please check the setup.")
        return
    
    service_process = start_service()
    if not service_process:
        print("\n❌ Failed to start service. Please check the logs.")
        return
    
    open_dashboard()
    show_instructions()
    
    print("\n" + "=" * 70)
    print("🎉 Professional Demo Ready!")
    print("=" * 70)
    print("The service is running in the background.")
    print("Press Ctrl+C to stop the service when you're done.")
    print("=" * 70)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping service...")
        service_process.terminate()
        print("✅ Service stopped. Thank you for using the demo!")

if __name__ == "__main__":
    main()