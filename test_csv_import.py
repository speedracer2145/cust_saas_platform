#!/usr/bin/env python3
"""
Test CSV Import Functionality
"""

import requests
import json
import pandas as pd

API_BASE = "http://localhost:8000"

def test_csv_import():
    """Test the CSV import functionality"""
    
    print("Testing CSV Import Functionality")
    print("=" * 40)
    
    # Read the CSV file
    try:
        df = pd.read_csv("amazon_30_customers_with_product_details.csv")
        print(f"Loaded {len(df)} records from CSV")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return
    
    # Prepare data for bulk import (first 5 records for testing)
    test_data = df.head(5)
    
    reviews = []
    for _, row in test_data.iterrows():
        reviews.append({
            "Id": str(row['Id']),
            "ProductId": str(row['ProductId']),
            "Text": str(row['Text']),
            "Score": float(row['Score']),
            "Time": str(row['Time']),
            "Summary": str(row['Summary']),
            "HelpfulnessNumerator": int(row['HelpfulnessNumerator']),
            "HelpfulnessDenominator": int(row['HelpfulnessDenominator'])
        })
    
    bulk_data = {
        "reviews": reviews,
        "group_by_product": True,
        "include_top_comments": True,
        "top_comments_per_category": 5
    }
    
    print(f"Sending {len(reviews)} reviews for bulk import...")
    
    try:
        response = requests.post(
            f"{API_BASE}/analyze/bulk-import",
            json=bulk_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Processed {result['processed_reviews']} reviews")
            print(f"Processing time: {result['processing_time_seconds']:.2f} seconds")
            print(f"Products analyzed: {len(result.get('products', {}))}")
            
            # Test the statistics endpoint
            stats_response = requests.get(f"{API_BASE}/sentiment/statistics")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"\nUpdated Statistics:")
                print(f"Total analyses: {stats['total_analyses']}")
                print(f"Sentiment distribution: {stats['sentiment_distribution']}")
            
            print("\nCSV import test completed successfully!")
            print("You can now refresh your dashboard to see the updated data.")
            
        else:
            print(f"FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error during import: {e}")

if __name__ == "__main__":
    test_csv_import()