#!/usr/bin/env python3
"""
Test script for bulk import API endpoint.
Tests bulk import with Amazon dataset format and verifies product grouping and top comments.
"""

import requests
import json
import time
from typing import List, Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_bulk_import():
    """Test the bulk import API endpoint."""
    print("\n" + "="*70)
    print("TESTING BULK IMPORT API")
    print("="*70)
    
    # Sample Amazon format reviews (multiple products)
    amazon_reviews = {
        "reviews": [
            # Product 1 - Positive reviews
            {
                "Id": "1",
                "ProductId": "B001234567",
                "Text": "I absolutely love this product! The quality is exceptional and it works perfectly. Highly recommend to everyone!",
                "Score": 5.0,
                "Time": "1346976000",
                "Summary": "Excellent product",
                "HelpfulnessNumerator": 10,
                "HelpfulnessDenominator": 10
            },
            {
                "Id": "2",
                "ProductId": "B001234567",
                "Text": "Great value for money. Works as expected and delivery was fast.",
                "Score": 4.0,
                "Time": "1347062400",
                "Summary": "Good value",
                "HelpfulnessNumerator": 8,
                "HelpfulnessDenominator": 9
            },
            {
                "Id": "3",
                "ProductId": "B001234567",
                "Text": "This product broke after just one week. Very disappointed with the quality.",
                "Score": 1.0,
                "Time": "1347148800",
                "Summary": "Poor quality",
                "HelpfulnessNumerator": 5,
                "HelpfulnessDenominator": 6
            },
            # Product 2 - Mixed reviews
            {
                "Id": "4",
                "ProductId": "B007654321",
                "Text": "The product is okay, does what it's supposed to do but nothing special. Average quality.",
                "Score": 3.0,
                "Time": "1347235200",
                "Summary": "Average",
                "HelpfulnessNumerator": 3,
                "HelpfulnessDenominator": 5
            },
            {
                "Id": "5",
                "ProductId": "B007654321",
                "Text": "Amazing quality! This exceeded all my expectations. Will definitely buy again.",
                "Score": 5.0,
                "Time": "1347321600",
                "Summary": "Amazing",
                "HelpfulnessNumerator": 12,
                "HelpfulnessDenominator": 12
            },
            {
                "Id": "6",
                "ProductId": "B007654321",
                "Text": "Terrible experience. The product doesn't work as advertised.",
                "Score": 1.0,
                "Time": "1347408000",
                "Summary": "Terrible",
                "HelpfulnessNumerator": 4,
                "HelpfulnessDenominator": 4
            },
            # Product 3 - Mostly positive
            {
                "Id": "7",
                "ProductId": "B009876543",
                "Text": "Outstanding product! Fast shipping and great packaging. Very satisfied!",
                "Score": 5.0,
                "Time": "1347494400",
                "Summary": "Outstanding",
                "HelpfulnessNumerator": 15,
                "HelpfulnessDenominator": 15
            },
            {
                "Id": "8",
                "ProductId": "B009876543",
                "Text": "Good product overall, excellent value for money. Delivery was fast.",
                "Score": 4.0,
                "Time": "1347580800",
                "Summary": "Good value",
                "HelpfulnessNumerator": 7,
                "HelpfulnessDenominator": 8
            }
        ],
        "group_by_product": True,
        "include_top_comments": True,
        "top_comments_per_category": 10
    }
    
    # Test endpoint
    endpoint = f"{BASE_URL}/analyze/bulk-import"
    
    print(f"\n[1] Testing bulk import API endpoint...")
    print(f"    URL: {endpoint}")
    print(f"    Reviews: {len(amazon_reviews['reviews'])}")
    print(f"    Products: {len(set(r['ProductId'] for r in amazon_reviews['reviews']))}")
    
    try:
        # Make request
        start_time = time.time()
        response = requests.post(
            endpoint,
            json=amazon_reviews,
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[OK] Successfully processed {result['processed_reviews']} reviews")
            print(f"    Processing time: {result['processing_time_seconds']:.2f} seconds")
            print(f"    Request time: {request_time:.2f} seconds")
            print(f"    Products analyzed: {len(result['products'])}")
            
            # Display results by product
            print("\n" + "="*70)
            print("RESULTS BY PRODUCT")
            print("="*70)
            
            for product_id, product_data in result['products'].items():
                print(f"\nProduct: {product_id}")
                print(f"  Total Reviews: {product_data['total_reviews']}")
                print(f"  Positive: {product_data['positive_count']} ({product_data['positive_percentage']:.1f}%)")
                print(f"  Negative: {product_data['negative_count']} ({product_data['negative_percentage']:.1f}%)")
                print(f"  Neutral: {product_data['neutral_count']} ({product_data['neutral_percentage']:.1f}%)")
                print(f"  Avg Confidence: {product_data['avg_confidence']:.2f}")
                
                # Top comments
                if product_data['top_positive_comments']:
                    print(f"\n  Top Positive Comments ({len(product_data['top_positive_comments'])}):")
                    for i, comment in enumerate(product_data['top_positive_comments'][:3], 1):
                        print(f"    {i}. Score: {comment['ranking_score']:.3f}, Confidence: {comment['confidence']:.2f}")
                        print(f"       Text: {comment['text'][:60]}...")
                
                if product_data['top_negative_comments']:
                    print(f"\n  Top Negative Comments ({len(product_data['top_negative_comments'])}):")
                    for i, comment in enumerate(product_data['top_negative_comments'][:3], 1):
                        print(f"    {i}. Score: {comment['ranking_score']:.3f}, Confidence: {comment['confidence']:.2f}")
                        print(f"       Text: {comment['text'][:60]}...")
                
                if product_data['top_neutral_comments']:
                    print(f"\n  Top Neutral Comments ({len(product_data['top_neutral_comments'])}):")
                    for i, comment in enumerate(product_data['top_neutral_comments'][:3], 1):
                        print(f"    {i}. Score: {comment['ranking_score']:.3f}, Confidence: {comment['confidence']:.2f}")
                        print(f"       Text: {comment['text'][:60]}...")
            
            # Summary
            print("\n" + "="*70)
            print("SUMMARY")
            print("="*70)
            print(f"Total reviews processed: {result['processed_reviews']}")
            print(f"Products analyzed: {len(result['products'])}")
            print(f"Processing time: {result['processing_time_seconds']:.2f} seconds")
            print(f"Average time per review: {result['processing_time_seconds']/result['processed_reviews']*1000:.2f} ms")
            
            return True
        else:
            print(f"\n[ERROR] Request failed with status {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Could not connect to {BASE_URL}")
        print("    Make sure the service is running:")
        print("    1. Local: python start_service.py")
        print("    2. K8s: kubectl port-forward -n roberta-sentiment svc/roberta-sentiment-service 8000:8000")
        return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_csv_file(csv_file_path: str, limit: int = 100):
    """Test bulk import with a CSV file in Amazon format."""
    import pandas as pd
    
    print(f"\n[2] Testing with CSV file: {csv_file_path}")
    print(f"    Limit: {limit} reviews")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file_path, nrows=limit)
        print(f"    Loaded {len(df)} reviews from CSV")
        
        # Convert to Amazon format
        reviews = []
        for _, row in df.iterrows():
            review = {
                "Text": str(row.get('Text', row.get('text', ''))),
                "ProductId": str(row.get('ProductId', row.get('productId', 'unknown'))),
            }
            
            # Add optional fields
            if 'Score' in row:
                review["Score"] = float(row['Score'])
            if 'Time' in row:
                review["Time"] = str(row['Time'])
            if 'Summary' in row:
                review["Summary"] = str(row.get('Summary', ''))
            if 'Id' in row:
                review["Id"] = str(row['Id'])
            if 'UserId' in row:
                review["UserId"] = str(row.get('UserId', ''))
            if 'HelpfulnessNumerator' in row:
                review["HelpfulnessNumerator"] = int(row['HelpfulnessNumerator']) if pd.notna(row['HelpfulnessNumerator']) else None
            if 'HelpfulnessDenominator' in row:
                review["HelpfulnessDenominator"] = int(row['HelpfulnessDenominator']) if pd.notna(row['HelpfulnessDenominator']) else None
            
            reviews.append(review)
        
        # Make request
        endpoint = f"{BASE_URL}/analyze/bulk-import"
        request_data = {
            "reviews": reviews,
            "group_by_product": True,
            "include_top_comments": True,
            "top_comments_per_category": 10
        }
        
        print(f"    Sending {len(reviews)} reviews to API...")
        start_time = time.time()
        response = requests.post(
            endpoint,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minutes for large batches
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[OK] Successfully processed {result['processed_reviews']} reviews")
            print(f"    Processing time: {result['processing_time_seconds']:.2f} seconds")
            print(f"    Request time: {request_time:.2f} seconds")
            print(f"    Products analyzed: {len(result['products'])}")
            
            # Show top products
            print("\nTop Products by Review Count:")
            sorted_products = sorted(
                result['products'].items(),
                key=lambda x: x[1]['total_reviews'],
                reverse=True
            )
            
            for product_id, product_data in sorted_products[:10]:
                print(f"  {product_id}: {product_data['total_reviews']} reviews "
                      f"(+{product_data['positive_count']}, -{product_data['negative_count']}, ~{product_data['neutral_count']})")
            
            return True
        else:
            print(f"\n[ERROR] Request failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test bulk import API')
    parser.add_argument('--csv', type=str, help='Path to CSV file in Amazon format')
    parser.add_argument('--limit', type=int, default=100, help='Limit number of reviews from CSV (default: 100)')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='API base URL')
    
    args = parser.parse_args()
    
    BASE_URL = args.url
    
    # Test with sample data
    success = test_bulk_import()
    
    # Test with CSV file if provided
    if args.csv:
        test_with_csv_file(args.csv, args.limit)
    
    if success:
        print("\n" + "="*70)
        print("[SUCCESS] Bulk import test passed!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("[FAILED] Bulk import test failed")
        print("="*70)

