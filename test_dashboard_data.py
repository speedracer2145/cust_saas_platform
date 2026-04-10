import requests
import json

print("Testing dashboard data loading...")

try:
    # Test health endpoint
    health_response = requests.get('http://localhost:8000/health')
    print(f"Health check: {health_response.status_code}")
    
    # Test statistics endpoint
    stats_response = requests.get('http://localhost:8000/sentiment/statistics')
    print(f"Statistics API: {stats_response.status_code}")
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"Total analyses: {stats.get('total_analyses', 0)}")
        
        distribution = stats.get('sentiment_distribution', {})
        positive = (distribution.get('positive', 0) + distribution.get('POSITIVE', 0) + distribution.get('joy', 0))
        negative = (distribution.get('negative', 0) + distribution.get('NEGATIVE', 0) + distribution.get('sadness', 0) + distribution.get('disgust', 0))
        neutral = (distribution.get('neutral', 0) + distribution.get('surprise', 0))
        
        print(f"Calculated sentiment stats:")
        print(f"  Positive: {positive}")
        print(f"  Negative: {negative}")
        print(f"  Neutral: {neutral}")
        print(f"  Total: {positive + negative + neutral}")
        
        print(f"Available emotions: {list(distribution.keys())}")
    else:
        print(f"Statistics API failed: {stats_response.text}")
    
    # Test products endpoint
    products_response = requests.get('http://localhost:8000/products?limit=5')
    print(f"Products API: {products_response.status_code}")
    
    if products_response.status_code == 200:
        products_data = products_response.json()
        products = products_data.get('products', [])
        print(f"Products found: {len(products)}")
        if products:
            print(f"First product: {products[0].get('product_id', 'Unknown')}")
    
    # Test timeseries endpoint
    timeseries_response = requests.get('http://localhost:8000/sentiment/timeseries?group_by=day&limit=5')
    print(f"Timeseries API: {timeseries_response.status_code}")
    
    if timeseries_response.status_code == 200:
        timeseries_data = timeseries_response.json()
        print(f"Timeseries points: {len(timeseries_data) if timeseries_data else 0}")
        if timeseries_data:
            print(f"First point: {timeseries_data[0]}")
    
    print("\nAll API tests completed!")
    
except Exception as e:
    print(f"Error during testing: {e}")