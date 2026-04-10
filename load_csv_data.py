#!/usr/bin/env python3
"""
Enhanced CSV Data Loader for RoBERTa Sentiment Analysis Service

This script loads the amazon_30_customers_with_product_details.csv data 
and processes it through the sentiment analysis service.
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import sys
import os

def load_and_analyze_csv(csv_file_path="amazon_30_customers_with_product_details.csv", api_url="http://localhost:8000"):
    """Load CSV data and analyze it through the service."""
    
    # Check if service is running
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("ERROR: Service is not healthy. Please start the service first.")
            return False
    except:
        print("ERROR: Cannot connect to service. Please start the service first.")
        return False
    
    print("SUCCESS: Service is running. Loading and analyzing CSV data...")
    
    # Load CSV data
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Loaded {len(df)} records from CSV")
    except Exception as e:
        print(f"ERROR: Error loading CSV: {e}")
        return False
    
    # Process and analyze each row
    successful_analyses = 0
    total_rows = len(df)
    
    print(f"Processing {total_rows} reviews...")
    
    for index, row in df.iterrows():
        try:
            # Convert timestamp
            try:
                timestamp = datetime.fromtimestamp(int(row['Time'])).isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            # Prepare data for analysis
            analysis_data = {
                'text': str(row['Text']),
                'product': str(row['Product_Name']),
                'team': str(row['Customer_Type']),
                'timestamp': timestamp,
                'metadata': {
                    'product_id': str(row['ProductId']),
                    'original_score': float(row['Score']),
                    'summary': str(row['Summary']),
                    'helpfulness': f"{row['HelpfulnessNumerator']}/{row['HelpfulnessDenominator']}",
                    'profile_name': str(row['ProfileName']),
                    'suggestion': str(row['Suggestions']),
                    'product_description': str(row['Product_Description'])
                }
            }
            
            # Send for analysis
            response = requests.post(
                f"{api_url}/analyze",
                json=analysis_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                successful_analyses += 1
                
                # Show progress
                if successful_analyses % 5 == 0 or successful_analyses == total_rows:
                    print(f"Processed {successful_analyses}/{total_rows} reviews")
                    
            else:
                print(f"WARNING: Failed to analyze review {index + 1}: {response.status_code}")
                
        except Exception as e:
            print(f"ERROR: Error processing review {index + 1}: {e}")
            continue
        
        # Small delay to avoid overwhelming the service
        time.sleep(0.1)
    
    print(f"\nAnalysis Complete!")
    print(f"Successfully analyzed: {successful_analyses}/{total_rows} reviews")
    print(f"Success rate: {successful_analyses/total_rows*100:.1f}%")
    
    return successful_analyses > 0

def get_analysis_summary(api_url="http://localhost:8000"):
    """Get summary of analyzed data."""
    try:
        # Get statistics
        stats_response = requests.get(f"{api_url}/sentiment/statistics", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"\nAnalysis Summary:")
            print(f"   Total analyses: {stats.get('total_analyses', 0)}")
            print(f"   Average confidence: {stats.get('average_confidence', 0):.3f}")
            print(f"   Sentiment distribution: {stats.get('sentiment_distribution', {})}")
        
        # Get products
        products_response = requests.get(f"{api_url}/products?limit=10", timeout=10)
        if products_response.status_code == 200:
            products = products_response.json()
            print(f"\nTop Products Analyzed:")
            for product in products.get('products', [])[:5]:
                print(f"   - {product['product_id']}: {product['total_reviews']} reviews")
                print(f"     Positive: {product['positive_percentage']:.1f}% | "
                      f"Negative: {product['negative_percentage']:.1f}% | "
                      f"Neutral: {product['neutral_percentage']:.1f}%")
        
    except Exception as e:
        print(f"WARNING: Could not get analysis summary: {e}")

def main():
    """Main function."""
    print("RoBERTa Sentiment Analysis - CSV Data Loader")
    print("=" * 60)
    
    csv_file = "amazon_30_customers_with_product_details.csv"
    
    if not os.path.exists(csv_file):
        print(f"ERROR: CSV file not found: {csv_file}")
        print("Please make sure the file is in the current directory.")
        return
    
    # Load and analyze data
    success = load_and_analyze_csv(csv_file)
    
    if success:
        # Get summary
        get_analysis_summary()
        
        print(f"\nYour dashboard is ready!")
        print(f"   Open: http://localhost:8000/professional_dashboard.html")
        print(f"   API Docs: http://localhost:8000/docs")
        print(f"\nThe dashboard now shows real data from your CSV file!")
        
    else:
        print(f"\nData loading failed. Please check the service and try again.")

if __name__ == "__main__":
    main()