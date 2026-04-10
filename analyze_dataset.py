import pandas as pd
import numpy as np

# Load and analyze the dataset
df = pd.read_csv('amazon_30_customers_with_product_details.csv')

print("=== DATASET STATISTICS ===")
print(f"Total Reviews: {len(df)}")
print(f"Unique Products: {df['ProductId'].nunique()}")
print(f"Unique Users: {df['UserId'].nunique()}")
print(f"Date Range: {len(df)} reviews over time")

print("\n=== SCORE DISTRIBUTION ===")
score_dist = df['Score'].value_counts().sort_index()
for score, count in score_dist.items():
    percentage = (count / len(df)) * 100
    print(f"Score {score}: {count} reviews ({percentage:.1f}%)")

print(f"\nAverage Rating: {df['Score'].mean():.2f}/5.0")

print("\n=== TEXT ANALYSIS ===")
df['text_length'] = df['Text'].str.len()
print(f"Average Review Length: {df['text_length'].mean():.0f} characters")
print(f"Shortest Review: {df['text_length'].min()} characters")
print(f"Longest Review: {df['text_length'].max()} characters")

print("\n=== CUSTOMER TYPE DISTRIBUTION ===")
customer_dist = df['Customer_Type'].value_counts()
for ctype, count in customer_dist.items():
    percentage = (count / len(df)) * 100
    print(f"{ctype}: {count} reviews ({percentage:.1f}%)")

print("\n=== PRODUCT CATEGORIES ===")
product_dist = df['ProductId'].value_counts()
print(f"Most Reviewed Product: {product_dist.index[0]} ({product_dist.iloc[0]} reviews)")
print(f"Product Distribution:")
for i, (product, count) in enumerate(product_dist.head(5).items()):
    percentage = (count / len(df)) * 100
    print(f"  {i+1}. {product}: {count} reviews ({percentage:.1f}%)")

print("\n=== HELPFULNESS METRICS ===")
df['helpfulness_ratio'] = df['HelpfulnessNumerator'] / df['HelpfulnessDenominator'].replace(0, 1)
print(f"Average Helpfulness Ratio: {df['helpfulness_ratio'].mean():.2f}")
print(f"Reviews with Perfect Helpfulness (1.0): {(df['helpfulness_ratio'] == 1.0).sum()}")

print("\n=== SENTIMENT PREDICTION (Based on Scores) ===")
# Predict sentiment based on scores for comparison
df['predicted_sentiment'] = df['Score'].apply(lambda x: 'positive' if x >= 4 else ('negative' if x <= 2 else 'neutral'))
sentiment_dist = df['predicted_sentiment'].value_counts()
for sentiment, count in sentiment_dist.items():
    percentage = (count / len(df)) * 100
    print(f"{sentiment.title()}: {count} reviews ({percentage:.1f}%)")