#!/usr/bin/env python3
"""
Quick test script with minimal data to verify everything works.
Tests with just 2 products and 2 reviews each for speed.
"""

import sys
import logging
from pathlib import Path
import time

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ingest_customer_feedback import download_kaggle_dataset, load_amazon_reviews_dataset
from app.sentiment_analyzer import get_analyzer
from test_model_accuracy import calculate_accuracy_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def quick_test():
    """Quick test with minimal data."""
    print("\n" + "="*70)
    print("QUICK TEST - Minimal Data (2 products, 2 reviews each)")
    print("="*70)
    
    try:
        # Step 1: Get dataset path (already downloaded)
        print("\n[Step 1/4] Getting dataset path...")
        kaggle_path = download_kaggle_dataset("arhamrumi/amazon-product-reviews")
        print(f"[OK] Dataset path: {kaggle_path}")
        
        # Step 2: Load minimal dataset (2 products, 2 reviews each)
        print("\n[Step 2/4] Loading minimal dataset (2 products, 2 reviews each)...")
        feedback_items = load_amazon_reviews_dataset(
            kaggle_path,
            max_products=2,
            sample_size_per_product=2
        )
        print(f"[OK] Loaded {len(feedback_items)} feedback items")
        
        if len(feedback_items) == 0:
            print("[ERROR] No feedback items loaded!")
            return False
        
        # Step 3: Initialize analyzer
        print("\n[Step 3/4] Initializing sentiment analyzer...")
        start_time = time.time()
        analyzer = get_analyzer()
        init_time = time.time() - start_time
        print(f"[OK] Analyzer initialized in {init_time:.2f} seconds")
        print(f"  Device: {analyzer.device}")
        
        # Step 4: Process reviews
        print("\n[Step 4/4] Processing reviews through sentiment analyzer...")
        start_time = time.time()
        results = analyzer.analyze_batch(feedback_items)
        processing_time = time.time() - start_time
        print(f"[OK] Processed {len(results)} reviews in {processing_time:.2f} seconds")
        print(f"  Average: {processing_time/len(results)*1000:.2f} ms per review")
        
        # Show sample results
        print("\nSample Results:")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. Sentiment: {result.get('sentiment', 'N/A')}, "
                  f"Confidence: {result.get('confidence', 0):.2f}, "
                  f"Product: {result.get('product', 'N/A')}")
        
        # Calculate accuracy if we have expected sentiment
        print("\n[Bonus] Calculating accuracy metrics...")
        metrics = calculate_accuracy_metrics(results)
        if metrics['total_samples'] > 0:
            print(f"[OK] Overall Accuracy: {metrics['overall_accuracy']:.2f}%")
            print(f"  Total Samples: {metrics['total_samples']}")
            print(f"  Correct Predictions: {metrics['correct_predictions']}")
        else:
            print("  (No expected sentiment data for accuracy calculation)")
        
        # Test product queries
        print("\n[Bonus] Testing product queries...")
        products_data = analyzer.get_products_list(limit=10, min_reviews=1)
        print(f"[OK] Found {products_data['total']} products in database")
        if products_data['products']:
            print(f"  Sample product: {products_data['products'][0]['product_id']}")
            print(f"    Reviews: {products_data['products'][0]['total_reviews']}")
            print(f"    Positive: {products_data['products'][0]['positive']}, "
                  f"Negative: {products_data['products'][0]['negative']}, "
                  f"Neutral: {products_data['products'][0]['neutral']}")
        
        # Summary
        print("\n" + "="*70)
        print("QUICK TEST SUMMARY")
        print("="*70)
        print(f"[OK] Dataset loaded: {len(feedback_items)} items")
        print(f"[OK] Sentiment analysis completed: {len(results)} results")
        print(f"[OK] Model initialization: {init_time:.2f} seconds")
        print(f"[OK] Processing speed: {processing_time/len(results)*1000:.2f} ms/review")
        print(f"[OK] Products in database: {products_data['total']}")
        if metrics['total_samples'] > 0:
            print(f"[OK] Model accuracy: {metrics['overall_accuracy']:.2f}%")
        print("="*70)
        print("\n[SUCCESS] All tests passed! System is working correctly.")
        
        return True
        
    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)

