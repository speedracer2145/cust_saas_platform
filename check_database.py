import sqlite3
import os

# Connect to database
db_path = 'data/sentiment_results.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check total records
    cursor.execute('SELECT COUNT(*) FROM sentiment_results')
    total_records = cursor.fetchone()[0]
    print(f'Total records in database: {total_records}')
    
    # Check unique products
    cursor.execute('SELECT COUNT(DISTINCT product_id) FROM sentiment_results')
    unique_products = cursor.fetchone()[0]
    print(f'Unique products: {unique_products}')
    
    # Check top products by count
    cursor.execute('SELECT product_id, COUNT(*) FROM sentiment_results GROUP BY product_id ORDER BY COUNT(*) DESC LIMIT 10')
    print('\nTop products by review count:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} reviews')
    
    # Check date range
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sentiment_results')
    date_range = cursor.fetchone()
    print(f'\nDate range: {date_range[0]} to {date_range[1]}')
    
    # Check sentiment distribution
    cursor.execute('SELECT sentiment_label, COUNT(*) FROM sentiment_results GROUP BY sentiment_label')
    print('\nSentiment distribution:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]}')
    
    conn.close()
else:
    print('Database not found!')