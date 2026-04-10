#!/usr/bin/env python3
"""
Script to update timestamps in the CSV file to create better visualization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def update_csv_timestamps():
    """Update timestamps in the CSV file to create varied time distribution"""
    
    # Read the CSV file
    csv_file = "amazon_30_customers_with_product_details.csv"
    df = pd.read_csv(csv_file)
    
    print(f"Original data shape: {df.shape}")
    print(f"Original timestamp range: {df['Time'].min()} to {df['Time'].max()}")
    
    # Create varied timestamps over the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Generate random timestamps
    time_range = (end_date - start_date).total_seconds()
    random_times = []
    
    for i in range(len(df)):
        # Create some clustering around certain periods to make it more realistic
        if i < len(df) // 3:
            # Recent period (last 10 days)
            days_back = random.uniform(0, 10)
        elif i < 2 * len(df) // 3:
            # Middle period (10-20 days back)
            days_back = random.uniform(10, 20)
        else:
            # Earlier period (20-30 days back)
            days_back = random.uniform(20, 30)
        
        random_time = end_date - timedelta(days=days_back, 
                                         hours=random.uniform(0, 24),
                                         minutes=random.uniform(0, 60))
        random_times.append(random_time)
    
    # Sort timestamps to create a realistic progression
    random_times.sort()
    
    # Convert to Unix timestamps
    unix_timestamps = [int(dt.timestamp()) for dt in random_times]
    
    # Update the DataFrame
    df['Time'] = unix_timestamps
    
    # Save the updated CSV
    df.to_csv(csv_file, index=False)
    
    print(f"Updated timestamp range: {df['Time'].min()} to {df['Time'].max()}")
    print(f"Updated CSV saved to: {csv_file}")
    
    # Show some sample timestamps for verification
    print("\nSample updated timestamps:")
    for i in range(min(5, len(df))):
        dt = datetime.fromtimestamp(df['Time'].iloc[i])
        print(f"Row {i+1}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    update_csv_timestamps()