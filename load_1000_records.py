#!/usr/bin/env python3
"""
Loader for the 1000-record CSV dataset.
Handles the column mapping for amazon_1000_customers_unique_suggestions.csv.
"""

import pandas as pd
import requests
import time
from datetime import datetime
import os
import sys

def load_and_analyze_csv(csv_file_path, api_url="http://localhost:8000"):
    """Load CSV data and analyze it through the service."""
    
    # Check if service is running
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("ERROR: Service is not healthy. Please start the service first.")
            return False
    except:
        print("ERROR: Cannot connect to service at localhost:8000. Please start the service first.")
        return False
    
    print(f"SUCCESS: Service is running. Loading data from {csv_file_path}...")
    
    # Load CSV data
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Loaded {len(df)} records from CSV")
    except Exception as e:
        print(f"ERROR: Error loading CSV: {e}")
        return False
    
    successful_analyses = 0
    total_rows = len(df)
    
    print(f"Processing {total_rows} reviews...")
    
    # Use bulk-import endpoint if available, but the load_csv_data.py uses /analyze
    # Let's use the bulk-import endpoint which is much faster for 1000 records
    
    try:
        # Prepare reviews for bulk import
        reviews = []
        for index, row in df.iterrows():
            # Handle timestamps (Time is Unix timestamp in CSV)
            try:
                # Some CSVs have floating point or scientific notation for Time
                raw_time = float(row['Time'])
                # If timestamp is in far future or scientific notation it might be wrong
                # But amazon dataset uses seconds since epoch
                # 1774006467 looks like a recent/future timestamp
            except:
                raw_time = time.time()

            review_item = {
                "Id": str(row['Id']),
                "ProductId": str(row['ProductId']),
                "UserId": str(row.get('UserId', '')),
                "ProfileName": str(row.get('ProfileName', '')),
                "HelpfulnessNumerator": int(row.get('HelpfulnessNumerator', 0)),
                "HelpfulnessDenominator": int(row.get('HelpfulnessDenominator', 0)),
                "Score": float(row.get('Score', 0)),
                "Time": str(raw_time),
                "Summary": str(row.get('Summary', '')),
                "Text": str(row['Text']),
                "Customer_Type": str(row.get('Customer_Type', 'Normal')),
                "Suggestions": str(row.get('Suggestions', ''))
            }
            reviews.append(review_item)

        # Batch the bulk import (e.g., 200 at a time)
        batch_size = 200
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i+batch_size]
            print(f"Sending batch {i//batch_size + 1} ({len(batch)} records)...")
            
            response = requests.post(
                f"{api_url}/analyze/bulk-import",
                json={"reviews": batch, "group_by_product": True},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                successful_analyses += result.get('processed_reviews', 0)
                print(f"✅ Batch {i//batch_size + 1} processed. Total: {successful_analyses}/{total_rows}")
            else:
                print(f"❌ Batch {i//batch_size + 1} failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"ERROR: Error in bulk processing: {e}")
        return False
    
    print(f"\nAnalysis Complete!")
    print(f"Successfully analyzed: {successful_analyses}/{total_rows} reviews")
    
    return successful_analyses > 0

def main():
    csv_file = "../../amazon_1000_customers_unique_suggestions.csv"
    if not os.path.exists(csv_file):
        # Try local folder
        csv_file = "amazon_1000_customers_unique_suggestions.csv"
    
    if not os.path.exists(csv_file):
        print(f"ERROR: CSV file not found at {csv_file}")
        return

    success = load_and_analyze_csv(csv_file)
    
    if success:
        print(f"\nYour dashboard is ready!")
        print(f"   Open: http://localhost:8000/professional_dashboard.html")
    else:
        print(f"\nData loading failed.")

if __name__ == "__main__":
    main()
