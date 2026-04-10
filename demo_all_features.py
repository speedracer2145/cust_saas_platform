#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Demo Script for RoBERTa Sentiment Analysis Service

This script demonstrates ALL features of the service:
1. Health check
2. Single text analysis
3. Batch analysis
4. Bulk import with product grouping
5. Top comments and keyword extraction
6. Timeseries aggregation
7. Product queries
8. Statistics

Run this script to showcase the complete functionality.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_service():
    """Check if service is running."""
    print_section("1. SERVICE HEALTH CHECK")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("[OK] Service is healthy")
            print(f"   Status: {health['status']}")
            print(f"   Device: {health['device']}")
            print(f"   Model loaded: {health['model_loaded']}")
            return True
        else:
            print(f"[ERROR] Service returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to service!")
        print("   Please start the service first:")
        print("   python start_service.py")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def demo_single_analysis():
    """Demonstrate single text analysis."""
    print_section("2. SINGLE TEXT ANALYSIS")
    
    test_texts = [
        {"text": "I absolutely love this product! It's amazing!", "team": "TeamA", "product": "ProductX"},
        {"text": "This is terrible. I hate it.", "team": "TeamB", "product": "ProductY"},
        {"text": "It's okay, nothing special.", "team": "TeamA", "product": "ProductZ"}
    ]
    
    for i, feedback in enumerate(test_texts, 1):
        try:
            response = requests.post(f"{BASE_URL}/analyze", json=feedback, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Text {i}: '{feedback['text'][:40]}...'")
                print(f"   Sentiment: {result['sentiment']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                print(f"   Team: {result['team']}, Product: {result['product']}")
            else:
                print(f"[ERROR] Failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Error: {e}")

def demo_batch_analysis():
    """Demonstrate batch analysis."""
    print_section("3. BATCH ANALYSIS")
    
    batch_items = [
        {"text": "Great product!", "team": "TeamA", "product": "ProductX"},
        {"text": "Not good at all", "team": "TeamB", "product": "ProductY"},
        {"text": "Average quality", "team": "TeamA", "product": "ProductZ"},
        {"text": "Excellent service!", "team": "TeamC", "product": "ProductX"},
        {"text": "Poor quality", "team": "TeamB", "product": "ProductY"}
    ]
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/analyze/batch",
            json={"feedback_items": batch_items},
            timeout=120
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            results = response.json()
            print(f"[OK] Processed {len(results)} items in {elapsed:.2f} seconds")
            print(f"   Average: {elapsed/len(results)*1000:.2f} ms per item")
            print("\n   Results:")
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result['sentiment']} ({result['confidence']:.3f}) - {result['text'][:30]}...")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def demo_bulk_import():
    """Demonstrate bulk import with product grouping."""
    print_section("4. BULK IMPORT WITH PRODUCT GROUPING")
    
    amazon_reviews = {
        "reviews": [
            # Product 1 - Mixed reviews
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
            # Product 2 - Positive reviews
            {
                "Id": "4",
                "ProductId": "B007654321",
                "Text": "Amazing quality! This exceeded all my expectations. Will definitely buy again.",
                "Score": 5.0,
                "Time": "1347235200",
                "Summary": "Amazing",
                "HelpfulnessNumerator": 12,
                "HelpfulnessDenominator": 12
            },
            {
                "Id": "5",
                "ProductId": "B007654321",
                "Text": "Outstanding product! Fast shipping and great packaging. Very satisfied!",
                "Score": 5.0,
                "Time": "1347321600",
                "Summary": "Outstanding",
                "HelpfulnessNumerator": 15,
                "HelpfulnessDenominator": 15
            },
            {
                "Id": "6",
                "ProductId": "B007654321",
                "Text": "Good product overall, excellent value for money. Delivery was fast.",
                "Score": 4.0,
                "Time": "1347408000",
                "Summary": "Good value",
                "HelpfulnessNumerator": 7,
                "HelpfulnessDenominator": 8
            }
        ],
        "group_by_product": True,
        "include_top_comments": True,
        "top_comments_per_category": 5
    }
    
    try:
        print(f"   Processing {len(amazon_reviews['reviews'])} reviews...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/analyze/bulk-import",
            json=amazon_reviews,
            timeout=300
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Processed {result['processed_reviews']} reviews in {result['processing_time_seconds']:.2f} seconds")
            print(f"   Products analyzed: {len(result['products'])}")
            
            # Show product summaries
            for product_id, product_data in result['products'].items():
                print(f"\n   Product: {product_id}")
                print(f"      Total Reviews: {product_data['total_reviews']}")
                print(f"      Positive: {product_data['positive_count']} ({product_data['positive_percentage']:.1f}%)")
                print(f"      Negative: {product_data['negative_count']} ({product_data['negative_percentage']:.1f}%)")
                print(f"      Neutral: {product_data['neutral_count']} ({product_data['neutral_percentage']:.1f}%)")
                print(f"      Avg Confidence: {product_data['avg_confidence']:.3f}")
                
                # Show top comments
                if product_data['top_positive_comments']:
                    print(f"      Top Positive Comment: {product_data['top_positive_comments'][0]['text'][:50]}...")
                if product_data['top_negative_comments']:
                    print(f"      Top Negative Comment: {product_data['top_negative_comments'][0]['text'][:50]}...")
                
                # Show keywords
                if product_data['positive_keywords']:
                    print(f"      Positive Keywords: {', '.join(product_data['positive_keywords'][:5])}")
                if product_data['negative_keywords']:
                    print(f"      Negative Keywords: {', '.join(product_data['negative_keywords'][:5])}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def demo_timeseries():
    """Demonstrate timeseries aggregation."""
    print_section("5. TIMESERIES AGGREGATION")
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Overall timeseries
        response = requests.get(
            f"{BASE_URL}/sentiment/timeseries",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "group_by": "hour"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Retrieved {len(data)} time periods")
            if data:
                print("\n   Sample data points:")
                for point in data[:3]:
                    print(f"   Time: {point['time']}")
                    print(f"      Positive: {point['positive']}, Negative: {point['negative']}, Neutral: {point['neutral']}")
                    print(f"      Total: {point['total']}, Avg Confidence: {point['avg_confidence']:.3f}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def demo_products():
    """Demonstrate product queries."""
    print_section("6. PRODUCT QUERIES")
    
    try:
        response = requests.get(
            f"{BASE_URL}/products",
            params={"limit": 5, "min_reviews": 1},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Found {data['total']} products")
            if data['products']:
                print("\n   Top products:")
                for product in data['products'][:3]:
                    print(f"   Product: {product['product_id']}")
                    print(f"      Reviews: {product['total_reviews']}")
                    print(f"      Positive: {product['positive']} ({product['positive_percentage']:.1f}%)")
                    print(f"      Negative: {product['negative']} ({product['negative_percentage']:.1f}%)")
                    print(f"      Neutral: {product['neutral']} ({product['neutral_percentage']:.1f}%)")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def demo_statistics():
    """Demonstrate service statistics."""
    print_section("7. SERVICE STATISTICS")
    
    try:
        response = requests.get(f"{BASE_URL}/sentiment/statistics", timeout=60)
        
        if response.status_code == 200:
            stats = response.json()
            print("[OK] Service Statistics:")
            print(f"   Total analyses: {stats['total_analyses']}")
            print(f"   Days analyzed: {stats['days_analyzed']}")
            print(f"   Average confidence: {stats['average_confidence']:.3f}")
            print(f"   First analysis: {stats['first_analysis']}")
            print(f"   Last analysis: {stats['last_analysis']}")
            print(f"   Sentiment distribution: {stats['sentiment_distribution']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def main():
    """Run complete demo."""
    print("\n" + "="*70)
    print("  RoBERTa Sentiment Analysis Service - Complete Feature Demo")
    print("="*70)
    print(f"\nService URL: {BASE_URL}")
    print("Make sure the service is running before starting the demo!")
    
    # Check service
    if not check_service():
        return
    
    # Run all demos
    demo_single_analysis()
    demo_batch_analysis()
    demo_bulk_import()
    demo_timeseries()
    demo_products()
    demo_statistics()
    
    # Summary
    print_section("DEMO COMPLETE")
    print("[OK] All features demonstrated successfully!")
    print("\nKey Features Shown:")
    print("  1. Health monitoring")
    print("  2. Single text sentiment analysis")
    print("  3. Batch processing")
    print("  4. Bulk import with product grouping")
    print("  5. Top comments ranking")
    print("  6. Keyword extraction")
    print("  7. Timeseries aggregation")
    print("  8. Product queries")
    print("  9. Service statistics")
    print("\nFor interactive API documentation, visit:")
    print(f"  {BASE_URL}/docs")

if __name__ == "__main__":
    main()

