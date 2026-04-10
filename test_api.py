import requests
import json

# Test timeseries API
print("Testing timeseries API...")
r = requests.get('http://localhost:8000/sentiment/timeseries?group_by=day&limit=30')
print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    print(f'Number of data points: {len(data)}')
    print('Sample dates:')
    for item in data[:10]:
        print(f'{item["time"]}: {item["total"]} records (P:{item["positive"]}, N:{item["negative"]}, Neu:{item["neutral"]})')
else:
    print(f'Error: {r.text}')