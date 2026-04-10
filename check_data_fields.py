import sqlite3
import json

conn = sqlite3.connect('data/sentiment_results.db')
cursor = conn.cursor()

# Check what data fields are populated
cursor.execute('SELECT product, team, metadata FROM sentiment_results LIMIT 5')
rows = cursor.fetchall()

print('Sample data from database:')
for i, row in enumerate(rows):
    product, team, metadata = row
    print(f'Row {i+1}:')
    print(f'  Product: {product}')
    print(f'  Team: {team}')
    if metadata:
        try:
            meta_obj = json.loads(metadata)
            print(f'  Metadata keys: {list(meta_obj.keys())}')
            if 'Customer_Type' in meta_obj:
                print(f'  Customer_Type: {meta_obj["Customer_Type"]}')
        except:
            print(f'  Metadata: {metadata[:100]}...')
    else:
        print(f'  Metadata: None')
    print()

# Check if metadata contains customer type info
cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE metadata LIKE "%Customer_Type%"')
customer_type_count = cursor.fetchone()[0]
print(f'Records with Customer_Type in metadata: {customer_type_count}')

# Check distinct products
cursor.execute('SELECT DISTINCT product FROM sentiment_results LIMIT 10')
products = cursor.fetchall()
print(f'Available products: {[p[0] for p in products]}')

conn.close()