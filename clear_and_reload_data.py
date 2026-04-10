import sqlite3
import csv
import requests
import json
import time

print("Clearing old data from database...")

# Clear the database
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

print("\nLoading your CSV data...")

# Read your CSV file
csv_file = 'amazon_30_customers_with_product_details.csv'
reviews = []

with open(csv_file, 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for i, row in enumerate(reader):
        if i >= 50:  # Limit to first 50 reviews for faster processing
            break
        if row.get('Text') and row.get('Text').strip():
            reviews.append({
                'Id': row.get('Id', ''),
                'ProductId': row.get('ProductId', ''),
                'Text': row.get('Text', ''),
                'Score': float(row.get('Score', 3)),
                'Time': row.get('Time', str(int(time.time()))),
                'Summary': row.get('Summary', ''),
                'HelpfulnessNumerator': int(row.get('HelpfulnessNumerator', 0)),
                'HelpfulnessDenominator': int(row.get('HelpfulnessDenominator', 0))
            })

print(f"Found {len(reviews)} valid reviews in your CSV")

if reviews:
    # Send to bulk import API
    print("Sending to sentiment analysis service...")
    
    bulk_data = {
        'reviews': reviews,
        'group_by_product': True,
        'include_top_comments': True,
        'top_comments_per_category': 5
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/analyze/bulk-import',
            headers={'Content-Type': 'application/json'},
            json=bulk_data,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Successfully processed {result.get('processed_reviews', 0)} reviews")
            print(f"Processing time: {result.get('processing_time_seconds', 0):.2f} seconds")
            print(f"Products analyzed: {len(result.get('products', {}))}")
            
            # Verify the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sentiment_results')
            new_count = cursor.fetchone()[0]
            print(f"Database now contains: {new_count} records")
            
            # Show sentiment distribution
            cursor.execute('SELECT sentiment_label, COUNT(*) FROM sentiment_results GROUP BY sentiment_label')
            print("\nSentiment distribution:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]}")
            
            conn.close()
            
        else:
            print(f"API request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No valid reviews found in CSV file")

print("\nDone! Your dashboard should now show only your CSV data.")