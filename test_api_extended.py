import requests
import json
from datetime import datetime, timedelta

# Test timeseries API with extended time range
print("Testing timeseries API with extended time range...")

# Get data for the last 30 days
end_time = datetime.now()
start_time = end_time - timedelta(days=30)

url = f'http://localhost:8000/sentiment/timeseries?group_by=day&limit=30&start_time={start_time.isoformat()}&end_time={end_time.isoformat()}'
print(f"URL: {url}")

r = requests.get(url)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    print(f'Number of data points: {len(data)}')
    print('Sample dates:')
    for item in data[:10]:
        print(f'{item["time"]}: {item["total"]} records (P:{item["positive"]}, N:{item["negative"]}, Neu:{item["neutral"]})')
else:
    print(f'Error: {r.text}')

# Also test statistics
print("\nTesting statistics API...")
r2 = requests.get('http://localhost:8000/sentiment/statistics')
print(f'Statistics Status: {r2.status_code}')
if r2.status_code == 200:
    stats = r2.json()
    print(f'Total analyses: {stats.get("total_analyses", 0)}')
    print(f'Date range: {stats.get("first_analysis", "N/A")} to {stats.get("last_analysis", "N/A")}')
    print(f'Sentiment distribution: {stats.get("sentiment_distribution", {})}')