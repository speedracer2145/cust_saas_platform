import sqlite3
import os

# Connect to database
db_path = 'data/sentiment_results.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Database schema:')
    for table in tables:
        print(table[0])
    
    # Check column names
    cursor.execute("PRAGMA table_info(sentiment_results)")
    columns = cursor.fetchall()
    print('\nColumns in sentiment_results table:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check total records
    cursor.execute('SELECT COUNT(*) FROM sentiment_results')
    total_records = cursor.fetchone()[0]
    print(f'\nTotal records: {total_records}')
    
    # Check first few records
    cursor.execute('SELECT * FROM sentiment_results LIMIT 3')
    records = cursor.fetchall()
    print('\nFirst 3 records:')
    for record in records:
        print(f'  {record}')
    
    conn.close()
else:
    print('Database not found!')