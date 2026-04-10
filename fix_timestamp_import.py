#!/usr/bin/env python3
"""
Fixed script to import CSV data with proper timestamps
"""

import sqlite3
import csv
import requests
import json
import time
from datetime import datetime

def clear_database():
    """Clear existing data from database"""
    print("Clearing old data from database...")
    
    db_path = 'data/sentiment_results.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete all records
    cursor.execute('DELETE FROM sentiment_results')
    conn.commit()
    
    # Reset the auto-increment counter
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="sentiment_results"')
    conn.commit()
    
    print(f"Database cleared. Records remaining: {cursor.execute('SELECT COUNT(*) FROM sentiment_results').fetchone()[0]}")
    conn.close()

def load_csv_with_timestamps():
    """Load CSV data with proper timestamp handling"""
    print("\nLoading CSV data with proper timestamps...")
    
    csv_file = 'amazon_30_customers_with_product_details.csv'
    reviews = []
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i >= 50:  # Limit to first 50 reviews
                break
            if row.get('Text') and row.get('Text').strip():
                # Parse timestamp properly
                timestamp_str = None
                if row.get('Time'):
                    try:
                        # Convert Unix timestamp to ISO format
                        unix_ts = float(row['Time'])
                        timestamp_str = datetime.fromtimestamp(unix_ts).isoformat()
                    except (ValueError, TypeError):
                        timestamp_str = datetime.now().isoformat()
                else:
                    timestamp_str = datetime.now().isoformat()
                
                reviews.append({
                    'Id': row.get('Id', ''),
                    'ProductId': row.get('ProductId', ''),
                    'Text': row.get('Text', ''),
                    'Score': float(row.get('Score', 3)),
                    'Time': row.get('Time', str(int(time.time()))),
                    'Summary': row.get('Summary', ''),
                    'HelpfulnessNumerator': int(row.get('HelpfulnessNumerator', 0)),
                    'HelpfulnessDenominator': int(row.get('HelpfulnessDenominator', 0)),
                    'timestamp': timestamp_str  # Add explicit timestamp field
                })
    
    print(f"Found {len(reviews)} valid reviews in CSV")
    return reviews

def direct_database_insert(reviews):
    """Insert reviews directly into database with proper timestamps"""
    print("Inserting data directly into database with proper timestamps...")
    
    db_path = 'data/sentiment_results.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table already exists, no need to create
    
    # Mock sentiment analysis for demo purposes
    # In real scenario, this would go through the actual sentiment analyzer
    sentiment_labels = ['positive', 'negative', 'neutral']
    
    inserted_count = 0
    for review in reviews:
        try:
            # Simple sentiment prediction based on score for demo
            score = float(review.get('Score', 3))
            if score >= 4:
                sentiment = 'positive'
                confidence = 0.85 + (score - 4) * 0.1
            elif score <= 2:
                sentiment = 'negative' 
                confidence = 0.80 + (2 - score) * 0.1
            else:
                sentiment = 'neutral'
                confidence = 0.75
            
            # Use the timestamp from CSV
            timestamp = review['timestamp']
            
            # Prepare metadata
            metadata = {
                'rating': score,
                'review_id': review.get('Id', ''),
                'user_id': review.get('UserId', ''),
                'summary': review.get('Summary', ''),
                'helpfulness_numerator': review.get('HelpfulnessNumerator', 0),
                'helpfulness_denominator': review.get('HelpfulnessDenominator', 0)
            }
            
            # Insert into database
            cursor.execute('''
                INSERT INTO sentiment_results 
                (text, sentiment_label, confidence_score, timestamp, team, product, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                review['Text'],
                sentiment,
                confidence,
                timestamp,
                None,  # team
                review.get('ProductId', 'unknown'),
                json.dumps(metadata)
            ))
            
            inserted_count += 1
            
        except Exception as e:
            print(f"Error inserting review {review.get('Id', 'unknown')}: {e}")
    
    conn.commit()
    
    # Verify insertion
    cursor.execute('SELECT COUNT(*) FROM sentiment_results')
    total_count = cursor.fetchone()[0]
    
    # Show sentiment distribution
    cursor.execute('SELECT sentiment_label, COUNT(*) FROM sentiment_results GROUP BY sentiment_label')
    print(f"\nSuccessfully inserted {inserted_count} reviews")
    print(f"Total records in database: {total_count}")
    print("\nSentiment distribution:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Show timestamp range
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sentiment_results')
    min_ts, max_ts = cursor.fetchone()
    print(f"\nTimestamp range:")
    print(f"  From: {min_ts}")
    print(f"  To: {max_ts}")
    
    conn.close()

def main():
    """Main function"""
    clear_database()
    reviews = load_csv_with_timestamps()
    
    if reviews:
        direct_database_insert(reviews)
        print("\nDone! Your dashboard should now show data with proper timestamps.")
        print("The graph should display data points distributed over time.")
    else:
        print("No valid reviews found in CSV file")

if __name__ == "__main__":
    main()