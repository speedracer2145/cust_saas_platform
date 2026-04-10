#!/usr/bin/env python3
"""
Quick Data Loader - Adds sample data to demonstrate dashboard functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def load_sample_reviews():
    """Load sample reviews to demonstrate the dashboard."""
    
    # Sample reviews with varied sentiments and dates
    sample_reviews = [
        {
            "text": "I absolutely love this premium dog food! My Labrador has never been healthier and her coat is so shiny now.",
            "product": "Premium Dog Nutrition Food",
            "team": "Premium",
            "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
        },
        {
            "text": "The product arrived damaged and the customer service was terrible. Very disappointed.",
            "product": "Roasted Peanut Snack Pack", 
            "team": "Trial",
            "timestamp": (datetime.now() - timedelta(days=4)).isoformat()
        },
        {
            "text": "These Twizzlers are exactly what I expected. Good quality and fresh.",
            "product": "Twizzlers Strawberry Candy",
            "team": "Normal",
            "timestamp": (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            "text": "This hot sauce is incredible! The perfect balance of heat and flavor.",
            "product": "Gourmet Hot Sauce",
            "team": "Premium", 
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            "text": "The drill works fine but it's quite heavy for extended use.",
            "product": "Professional Power Drill",
            "team": "Normal",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "text": "Amazing results! My skin looks years younger after using this serum.",
            "product": "Anti-Aging Serum Premium",
            "team": "Premium",
            "timestamp": datetime.now().isoformat()
        },
        {
            "text": "The fitness tracker is way too complicated. I just wanted something simple.",
            "product": "Advanced Fitness Tracker",
            "team": "Normal",
            "timestamp": (datetime.now() - timedelta(days=6)).isoformat()
        },
        {
            "text": "Perfect espresso machine! Makes café-quality drinks at home.",
            "product": "Professional Espresso Machine", 
            "team": "Premium",
            "timestamp": (datetime.now() - timedelta(days=7)).isoformat()
        },
        {
            "text": "The chocolate is good but overpriced for what you get.",
            "product": "Gourmet Chocolate Assortment",
            "team": "Trial",
            "timestamp": (datetime.now() - timedelta(days=8)).isoformat()
        },
        {
            "text": "Excellent organic seeds! My garden is thriving.",
            "product": "Organic Garden Seed Collection",
            "team": "Premium",
            "timestamp": (datetime.now() - timedelta(days=9)).isoformat()
        }
    ]
    
    print(f"Loading {len(sample_reviews)} sample reviews...")
    
    success_count = 0
    for i, review in enumerate(sample_reviews):
        try:
            response = requests.post(f"{API_BASE}/analyze", json=review, timeout=10)
            if response.status_code == 200:
                success_count += 1
                print(f"SUCCESS: Loaded review {i+1}/{len(sample_reviews)}")
            else:
                print(f"FAILED: Review {i+1}: {response.status_code}")
        except Exception as e:
            print(f"ERROR: Loading review {i+1}: {e}")
        
        time.sleep(0.5)  # Small delay to avoid overwhelming the service
    
    print(f"\nCompleted! Successfully loaded {success_count}/{len(sample_reviews)} reviews")
    return success_count > 0

def main():
    print("Quick Data Loader for Dashboard Demo")
    print("=" * 40)
    
    # Check if service is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: Service is not healthy")
            return
    except:
        print("ERROR: Cannot connect to service. Please start it first:")
        print("python start_service.py --skip-checks")
        return
    
    print("Service is running. Loading sample data...")
    
    if load_sample_reviews():
        print("\nData loaded successfully!")
        print("Your dashboard should now show data and charts.")
        print("Open: http://localhost:8000/professional_dashboard.html")
    else:
        print("\nFailed to load data")

if __name__ == "__main__":
    main()