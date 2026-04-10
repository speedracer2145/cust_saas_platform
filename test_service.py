"""
Test script for the RoBERTa Sentiment Analysis Service

This script demonstrates how to use the service and can be used for testing.
"""

import requests
import json
import time
from datetime import datetime, timedelta


def test_service():
    """Test the sentiment analysis service endpoints."""
    
    BASE_URL = "http://localhost:8000"
    
    print("🧪 Testing RoBERTa Sentiment Analysis Service")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service is healthy")
            print(f"   Status: {health_data['status']}")
            print(f"   Device: {health_data['device']}")
            print(f"   Model loaded: {health_data['model_loaded']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to service. Make sure it's running on localhost:8000")
        return
    
    # Test 2: Single Text Analysis
    print("\n2. Testing Single Text Analysis...")
    test_feedback = [
        {
            "text": "I absolutely love this product! It's amazing!",
            "team": "TeamA",
            "product": "ProductX",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        },
        {
            "text": "This is terrible. I hate it.",
            "team": "TeamB",
            "product": "ProductY",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        },
        {
            "text": "It's okay, nothing special.",
            "team": "TeamA",
            "product": "ProductZ",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        },
        {
            "text": "The weather is nice today.",
            "team": "TeamC",
            "product": "ProductX",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        },
        {
            "text": "I'm feeling neutral about this.",
            "team": "TeamB",
            "product": "ProductZ",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        }
    ]
    
    for feedback in test_feedback:
        try:
            response = requests.post(f"{BASE_URL}/analyze", json=feedback)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ '{feedback['text'][:30]}...' -> {result['sentiment']} (confidence: {result['confidence']:.3f}) [Team: {result['team']}, Product: {result['product']}]")
            else:
                print(f"❌ Analysis failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 3: Batch Analysis
    print("\n3. Testing Batch Analysis...")
    try:
        response = requests.post(f"{BASE_URL}/analyze/batch", json={
            "feedback_items": test_feedback
        })
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Batch analysis completed for {len(results)} feedback items")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result['sentiment']} (confidence: {result['confidence']:.3f}) [Team: {result['team']}, Product: {result['product']}]")
        else:
            print(f"❌ Batch analysis failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Timeseries Data
    print("\n4. Testing Timeseries Data...")
    try:
        # Get data for the last hour
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        # Test overall timeseries
        response = requests.get(f"{BASE_URL}/sentiment/timeseries", params={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "group_by": "hour"
        })
        
        if response.status_code == 200:
            timeseries_data = response.json()
            print(f"✅ Retrieved {len(timeseries_data)} overall timeseries data points")
            for data_point in timeseries_data:
                print(f"   Time: {data_point['time']}, Team: {data_point.get('team', 'All')}, Product: {data_point.get('product', 'All')}")
                print(f"   Positive: {data_point['positive']}, Neutral: {data_point['neutral']}, Negative: {data_point['negative']}")
        else:
            print(f"❌ Timeseries request failed: {response.status_code} - {response.text}")
        
        # Test filtered timeseries by team
        response = requests.get(f"{BASE_URL}/sentiment/timeseries", params={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "group_by": "hour",
            "team": "TeamA"
        })
        
        if response.status_code == 200:
            timeseries_data = response.json()
            print(f"✅ Retrieved {len(timeseries_data)} timeseries data points for TeamA")
            for data_point in timeseries_data:
                print(f"   Time: {data_point['time']}, Team: {data_point.get('team', 'All')}, Product: {data_point.get('product', 'All')}")
                print(f"   Positive: {data_point['positive']}, Neutral: {data_point['neutral']}, Negative: {data_point['negative']}")
        
        # Test filtered timeseries by product
        response = requests.get(f"{BASE_URL}/sentiment/timeseries", params={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "group_by": "hour",
            "product": "ProductX"
        })
        
        if response.status_code == 200:
            timeseries_data = response.json()
            print(f"✅ Retrieved {len(timeseries_data)} timeseries data points for ProductX")
            for data_point in timeseries_data:
                print(f"   Time: {data_point['time']}, Team: {data_point.get('team', 'All')}, Product: {data_point.get('product', 'All')}")
                print(f"   Positive: {data_point['positive']}, Neutral: {data_point['neutral']}, Negative: {data_point['negative']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Service Statistics
    print("\n5. Testing Service Statistics...")
    try:
        response = requests.get(f"{BASE_URL}/sentiment/statistics")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Service Statistics:")
            print(f"   Total analyses: {stats['total_analyses']}")
            print(f"   Days analyzed: {stats['days_analyzed']}")
            print(f"   Average confidence: {stats['average_confidence']:.3f}")
            print(f"   Sentiment distribution: {stats['sentiment_distribution']}")
        else:
            print(f"❌ Statistics request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")


def generate_sample_data():
    """Generate sample data for testing timeseries visualization."""
    
    BASE_URL = "http://localhost:8000"
    
    print("\n📊 Generating sample data for timeseries visualization...")
    
    # Sample feedback with different sentiments, teams, and products
    sample_feedback = [
        # Positive texts
        {"text": "This is absolutely fantastic! I love it!", "team": "TeamA", "product": "ProductX"},
        {"text": "Amazing product, highly recommended!", "team": "TeamB", "product": "ProductY"},
        {"text": "Excellent service, thank you so much!", "team": "TeamA", "product": "ProductZ"},
        {"text": "Perfect! Exactly what I was looking for.", "team": "TeamC", "product": "ProductX"},
        {"text": "Outstanding quality and great value!", "team": "TeamB", "product": "ProductY"},
        
        # Negative texts
        {"text": "This is terrible, completely disappointed.", "team": "TeamA", "product": "ProductY"},
        {"text": "Worst experience ever, avoid at all costs.", "team": "TeamC", "product": "ProductZ"},
        {"text": "Poor quality, waste of money.", "team": "TeamB", "product": "ProductX"},
        {"text": "Absolutely horrible, would not recommend.", "team": "TeamA", "product": "ProductZ"},
        {"text": "Disgusting, I want my money back.", "team": "TeamC", "product": "ProductY"},
        
        # Neutral texts
        {"text": "It's okay, nothing special.", "team": "TeamB", "product": "ProductZ"},
        {"text": "Average product, does the job.", "team": "TeamA", "product": "ProductY"},
        {"text": "Not bad, but not great either.", "team": "TeamC", "product": "ProductX"},
        {"text": "It's fine, I guess.", "team": "TeamB", "product": "ProductY"},
        {"text": "Standard quality, as expected.", "team": "TeamA", "product": "ProductZ"}
    ]
    
    # Generate data for the last 24 hours
    for hour in range(24):
        # Create a batch of feedback items for this hour
        batch_feedback = []
        
        # Add some random feedback for this hour
        import random
        num_items = random.randint(5, 15)
        for _ in range(num_items):
            feedback_item = random.choice(sample_feedback)
            batch_feedback.append({
                "text": feedback_item["text"],
                "team": feedback_item["team"],
                "product": feedback_item["product"],
                "timestamp": (datetime.now() - timedelta(hours=24-hour)).isoformat(),
                "metadata": {
                    "generated": True,
                    "hour": hour
                }
            })
        
        try:
            response = requests.post(f"{BASE_URL}/analyze/batch", json={
                "feedback_items": batch_feedback
            })
            
            if response.status_code == 200:
                print(f"✅ Generated {len(batch_feedback)} analyses for hour {hour}")
            else:
                print(f"❌ Failed to generate data for hour {hour}")
        except Exception as e:
            print(f"❌ Error generating data for hour {hour}: {e}")
        
        # Small delay to spread data across time
        time.sleep(0.1)
    
    print("✅ Sample data generation completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_sample_data()
    else:
        test_service()
        
        # Ask if user wants to generate sample data
        response = input("\nWould you like to generate sample data for timeseries visualization? (y/n): ")
        if response.lower() in ['y', 'yes']:
            generate_sample_data()
