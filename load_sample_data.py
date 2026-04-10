#!/usr/bin/env python3
"""
Data Loader for RoBERTa Sentiment Analysis Service

This script loads the sample CSV data into the database for demonstration purposes.
"""

import pandas as pd
import sqlite3
import requests
import json
import time
from datetime import datetime
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def load_csv_data(csv_file_path):
    """Load and process the CSV data."""
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Loaded {len(df)} records from CSV")
        
        # Process the data
        processed_data = []
        
        for _, row in df.iterrows():
            # Convert timestamp
            try:
                timestamp = datetime.fromtimestamp(int(row['Time'])).isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            # Determine sentiment based on score (basic heuristic)
            score = float(row['Score'])
            if score >= 4:
                sentiment_hint = 'positive'
            elif score <= 2:
                sentiment_hint = 'negative'
            else:
                sentiment_hint = 'neutral'
            
            processed_data.append({
                'text': str(row['Text']),
                'product': str(row['ProductId']),
                'team': str(row['Customer_Type']),
                'timestamp': timestamp,
                'metadata': {
                    'original_score': score,
                    'summary': str(row['Summary']),
                    'helpfulness': f"{row['HelpfulnessNumerator']}/{row['HelpfulnessDenominator']}",
                    'profile_name': str(row['ProfileName']),
                    'suggestion': str(row['Suggestions']),
                    'sentiment_hint': sentiment_hint
                }
            })
        
        return processed_data
        
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        return []

def send_to_api(data_batch, api_url="http://localhost:8000"):
    """Send data to the sentiment analysis API."""
    try:
        response = requests.post(
            f"{api_url}/analyze/batch",
            json={"feedback_items": data_batch},
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error sending to API: {e}")
        return None

def load_data_to_service(csv_file_path, batch_size=10, api_url="http://localhost:8000"):
    """Load CSV data into the sentiment analysis service."""
    
    # Check if service is running
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("Service is not healthy. Please start the service first.")
            return False
    except:
        print("Cannot connect to service. Please start the service first with: python start_service.py")
        return False
    
    print("Service is running. Loading data...")
    
    # Load and process CSV data
    processed_data = load_csv_data(csv_file_path)
    if not processed_data:
        print("No data to load.")
        return False
    
    print(f"Processing {len(processed_data)} records in batches of {batch_size}")
    
    # Send data in batches
    total_processed = 0
    successful_batches = 0
    
    for i in range(0, len(processed_data), batch_size):
        batch = processed_data[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(processed_data) + batch_size - 1)//batch_size}")
        
        result = send_to_api(batch, api_url)
        if result:
            total_processed += len(batch)
            successful_batches += 1
            print(f"  ✓ Batch processed successfully ({len(batch)} items)")
        else:
            print(f"  ✗ Batch failed")
        
        # Small delay to avoid overwhelming the service
        time.sleep(1)
    
    print(f"\nData loading complete!")
    print(f"Total records processed: {total_processed}")
    print(f"Successful batches: {successful_batches}")
    print(f"Success rate: {successful_batches * batch_size / len(processed_data) * 100:.1f}%")
    
    return True

def main():
    """Main function."""
    csv_file_path = "amazon_30_customers_unique_suggestions.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        print("Please make sure the file is in the current directory.")
        return
    
    print("🚀 RoBERTa Sentiment Analysis - Data Loader")
    print("=" * 50)
    
    success = load_data_to_service(csv_file_path)
    
    if success:
        print("\n✅ Data loading completed successfully!")
        print("You can now use the dashboard to view the analyzed data.")
        print("Open: http://localhost:8000/professional_dashboard.html")
    else:
        print("\n❌ Data loading failed.")
        print("Please check the service status and try again.")

if __name__ == "__main__":
    main()