# RoBERTa Sentiment Analysis Service

A high-performance REST API service for sentiment analysis using pre-trained RoBERTa models from Hugging Face Transformers. This service provides real-time sentiment classification, batch processing, historical data aggregation, and interactive visualizations for timeseries analysis.

## 🚀 Features

### Core Functionality
- **Real-time Sentiment Analysis**: Analyze single texts or batches using RoBERTa models
- **Batch Processing**: Efficient processing of large text datasets with configurable batch sizes (default: 128)
- **Bulk Import**: Import Amazon format reviews with automatic product grouping
- **Product Grouping**: Automatic grouping of results by product with sentiment statistics
- **Top Comments Ranking**: Intelligent ranking of top comments per sentiment category per product
- **Keyword Extraction**: Extract relevant keywords using KeyBERT for each sentiment category
- **Product Comparison**: Compare sentiment metrics between multiple products

### Data Management
- **SQLite Database**: Persistent storage with optimized indexes for fast queries
- **Multi-dimensional Context**: Support for team and product categorization with metadata
- **Advanced Filtering**: Filter timeseries data by team, product, or time ranges
- **Historical Data Storage**: Store and retrieve sentiment analysis results with full query capabilities

### API & Integration
- **REST API**: Clean, well-documented REST endpoints with automatic OpenAPI documentation
- **FastAPI Framework**: Modern async Python web framework with automatic validation
- **CORS Support**: Configured for cross-origin requests
- **Health Checks**: Built-in health monitoring endpoints
- **Interactive Documentation**: Swagger UI and ReDoc available at `/docs` and `/redoc`

### Visualization
- **Interactive Charts**: Plotly-based time series visualizations
- **Multiple Chart Types**: Line, bar, and area charts
- **Dashboard Views**: Comprehensive sentiment dashboards with filtering
- **Product-specific Visualizations**: Time series charts per product

### Performance & Scalability
- **GPU Acceleration**: Automatic CUDA detection and GPU support
- **Optimized Inference**: Batch processing with `torch.no_grad()` for faster inference
- **Model Optimization**: Float16 on GPU, float32 on CPU
- **Database Indexing**: Strategic indexes on timestamp, sentiment, team, and product columns
- **Connection Pooling**: Efficient database connection management

### Production Ready
- **Kubernetes Ready**: Complete K8s manifests for production deployment
- **Docker Support**: Containerized deployment with Dockerfile
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Health Monitoring**: Built-in health check endpoints for service monitoring

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Process Flow](#process-flow)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 📦 Prerequisites

- **Python**: 3.8 or higher
- **CUDA**: Optional, but recommended for faster inference (CUDA-compatible GPU)
- **Memory**: Minimum 4GB RAM (8GB+ recommended for batch processing)
- **Disk Space**: ~2GB for model files and dependencies

**Note for Windows users:** This project uses a specific Python installation at:
```
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe
```

See [USING_PYTHON_PATH.md](USING_PYTHON_PATH.md) for helper scripts and usage instructions.

## 🔧 Installation

### 1. Clone or Download the Project

```bash
cd roberta-sentiment-service
```

### 2. Install Dependencies

**On Windows (using specified Python path):**
```powershell
# Direct installation
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe -m pip install -r requirements.txt

# Or using helper script (recommended)
.\run_python.ps1 -m pip install -r requirements.txt
```

**On Linux/Mac:**
```bash
pip install -r requirements.txt
```

### 3. Model Files

The service will attempt to load models in this order:
1. Local model files in `models/roberta-sentiment/`
2. Cached models from Hugging Face cache
3. Download from Hugging Face (requires internet connection)

For offline usage, ensure model files are available in the `models/` directory.

## 🚀 Quick Start

### Start the Service

**On Windows (using helper script - recommended):**
```powershell
.\run_service.ps1
```

**On Windows (direct):**
```powershell
C:\Users\svijapur\AppData\Local\Programs\Python\Python314\python.exe start_service.py
```

**On Linux/Mac:**
```bash
python start_service.py
# Or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will start on `http://localhost:8000`

### Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Or visit in browser
http://localhost:8000/docs
```

## 🔄 Process Flow

This section describes the complete flow of data processing from bulk import to querying results.

### Bulk Import Process Flow

When bulk import is initiated via `POST /analyze/bulk-import`, the following steps occur:

#### 1. **Request Validation & Format Conversion**
- Validates that reviews are provided (max 10,000 reviews per request)
- Converts Amazon format reviews to internal format:
  - Extracts `Text` field as the main text for analysis
  - Extracts `ProductId` as product identifier (defaults to 'unknown' if missing)
  - Parses `Time` field (supports Unix timestamp or ISO format)
  - Builds metadata dictionary from:
    - `Score` (rating 1-5) → stored as `rating` and `expected_sentiment`
    - `Id` → stored as `review_id`
    - `UserId` → stored as `user_id`
    - `ProfileName` → stored as `profile_name`
    - `Summary` → stored as `summary`
    - `HelpfulnessNumerator` and `HelpfulnessDenominator` → stored for ranking

#### 2. **Batch Sentiment Analysis**
- Processes all feedback items through `analyze_batch()` method:
  - **Text Preprocessing**: Truncates texts longer than 1536 characters (max_length * 3) for efficiency
  - **Batch Processing**: Groups texts into batches of 128 items (configurable)
  - **Model Inference**: 
    - Uses RoBERTa model via Hugging Face pipeline
    - Applies tokenization with max_length=512, truncation=True, padding=True
    - Runs inference with `torch.no_grad()` for faster processing (no gradient computation)
    - Processes batches sequentially for memory efficiency
  - **Result Extraction**: 
    - Extracts sentiment label (LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive)
    - Extracts confidence score for each sentiment class
    - Selects highest confidence sentiment as primary result
  - **Database Storage**: Each result is immediately stored in SQLite database:
    - Table: `sentiment_results`
    - Columns: text, sentiment_label, confidence_score, timestamp, team, product, metadata
    - Metadata is JSON-encoded before storage

#### 3. **Product Grouping & Statistics**
- Groups all results by `product_id`:
  - Creates a dictionary structure per product containing:
    - List of all review results
    - Count of positive reviews (LABEL_2 or contains 'positive')
    - Count of negative reviews (LABEL_0 or contains 'negative')
    - Count of neutral reviews (LABEL_1 or contains 'neutral')
    - Sum of confidence scores for averaging
- Calculates per-product statistics:
  - Total reviews count
  - Positive/negative/neutral counts and percentages
  - Average confidence score across all reviews

#### 4. **Top Comments Extraction**
- For each product and sentiment category (positive/negative/neutral):
  - Filters reviews matching the sentiment category
  - Ranks comments using composite scoring:
    1. **Confidence score** (higher is better)
    2. **Helpfulness score** (if available: numerator/denominator ratio)
    3. **Recency** (newer timestamps ranked higher)
    4. **Text length** (longer, more detailed reviews preferred)
  - Selects top N comments (default: 10, configurable via `top_comments_per_category`)

#### 5. **Keyword Extraction**
- For each product and sentiment category:
  - Filters reviews by sentiment category
  - Combines all review texts into a single document
  - Uses KeyBERT (BERT-based keyword extraction):
    - Model: `all-MiniLM-L6-v2` (lightweight and fast)
    - Extracts 1-2 word phrases (n-grams)
    - Applies English stop words filtering
    - Uses Maximal Marginal Relevance (MMR) for diversity
    - Returns top 10 keywords per category
  - Fallback: If KeyBERT fails, uses simple word frequency analysis

#### 6. **Response Assembly**
- Builds `ProductSentimentSummary` for each product containing:
  - Product ID
  - Total reviews count
  - Sentiment counts (positive, negative, neutral)
  - Sentiment percentages
  - Average confidence score
  - Top comments per category (if `include_top_comments=True`)
  - Keywords per category
- Returns `BulkImportResponse` with:
  - Total reviews processed
  - Number of successfully processed reviews
  - Dictionary of product summaries
  - Processing time in seconds
  - Timestamp of completion

### Data Query Flow

After data is stored in the database, the following query flows are available:

#### Timeseries Aggregation (`GET /sentiment/timeseries`)
1. **Query Construction**: Builds SQL query with filters:
   - Time range filter (start_time to end_time)
   - Optional team filter
   - Optional product filter
2. **Time Grouping**: Groups data by time period:
   - `group_by=hour`: Groups by hour using `strftime('%Y-%m-%dT%H:00:00', timestamp)`
   - `group_by=day`: Groups by day using `strftime('%Y-%m-%dT00:00:00', timestamp)`
   - `group_by=week`: Groups by week starting from Sunday
3. **Aggregation**: SQL aggregation:
   - Counts sentiment labels per time period
   - Calculates average confidence per time period
   - Groups by time_period, sentiment_label, team, product
4. **Result Formatting**: 
   - Normalizes sentiment labels (LABEL_0→negative, LABEL_1→neutral, LABEL_2→positive)
   - Structures data with time, sentiment counts, totals, and averages

#### Product Listing (`GET /products`)
1. **Filtering**: Filters products with:
   - Minimum review count threshold
   - Excludes NULL and 'unknown' products
2. **Aggregation**: SQL aggregation per product:
   - Total review count
   - Sentiment label counts (using CASE statements)
   - Average confidence
   - First and last review timestamps
3. **Pagination**: Applies LIMIT and OFFSET for pagination
4. **Calculation**: Calculates percentages and formats response

#### Product Timeseries (`GET /products/{product_id}/timeseries`)
- Uses same aggregation logic as general timeseries but filtered by specific product_id
- Returns time-series data points for a single product

#### Statistics (`GET /sentiment/statistics`)
1. **Overall Statistics**: 
   - Total analyses count
   - Days analyzed (distinct dates)
   - Average confidence across all analyses
   - First and last analysis timestamps
2. **Sentiment Distribution**: 
   - Counts per sentiment label
   - Groups by sentiment_label

### Visualization Flow

#### Chart Generation (`GET /api/viz/sentiment-timeseries`)
1. **Data Retrieval**: Calls `get_aggregated_sentiment()` to get timeseries data
2. **DataFrame Conversion**: Converts results to pandas DataFrame
3. **Chart Creation**: Uses Plotly to create interactive charts:
   - Line charts: Shows sentiment trends over time
   - Bar charts: Shows sentiment distribution per time period
   - Area charts: Shows cumulative sentiment over time
4. **Chart Configuration**: 
   - Separate traces for positive, negative, neutral
   - Hover tooltips with detailed information
   - Zoom and pan capabilities
5. **JSON Serialization**: Converts Plotly figure to JSON for frontend rendering

### Database Operations

All database operations use SQLite with the following characteristics:

- **Connection Management**: Uses context managers (`with sqlite3.connect()`) for automatic connection handling
- **Indexes**: Strategic indexes on frequently queried columns:
  - `idx_timestamp` for time-based queries
  - `idx_sentiment_label` for sentiment filtering
  - `idx_team` and `idx_product` for filtering
  - `idx_team_product` composite index for combined filters
- **Parameterized Queries**: All queries use parameterized statements to prevent SQL injection
- **Transaction Safety**: Each INSERT operation is atomic (auto-commit on connection close)

## 📡 API Endpoints

### Health & Status

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-20T10:30:00",
  "model_loaded": true,
  "device": "cuda"
}
```

### Sentiment Analysis

#### `POST /analyze`
Analyze sentiment for a single text.

**Request:**
```json
{
  "text": "I love this product!",
  "team": "TeamA",
  "product": "ProductX",
  "timestamp": "2025-01-20T10:30:00",
  "metadata": {"source": "customer_feedback"}
}
```

**Response:**
```json
{
  "text": "I love this product!",
  "sentiment": "LABEL_2",
  "confidence": 0.9998,
  "all_scores": {
    "LABEL_0": 0.0001,
    "LABEL_1": 0.0001,
    "LABEL_2": 0.9998
  },
  "timestamp": "2025-01-20T10:30:00",
  "team": "TeamA",
  "product": "ProductX",
  "metadata": {"source": "customer_feedback"}
}
```

#### `POST /analyze/batch`
Analyze sentiment for a batch of feedback items.

**Request:**
```json
{
  "feedback_items": [
    {
      "text": "I love this product!",
      "team": "TeamA",
      "product": "ProductX",
      "timestamp": "2025-01-20T10:30:00",
      "metadata": {"source": "review_1"}
    },
    {
      "text": "This is terrible.",
      "team": "TeamB",
      "product": "ProductY",
      "timestamp": "2025-01-20T10:31:00",
      "metadata": {"source": "review_2"}
    }
  ]
}
```

**Response:** Array of sentiment results (same format as single analysis)

#### `POST /analyze/bulk-import`
Bulk import reviews in Amazon dataset format with product grouping.

**Request:**
```json
{
  "reviews": [
    {
      "Text": "I love this product!",
      "ProductId": "B001234567",
      "Score": 5.0,
      "Time": "1346976000",
      "Summary": "Great product",
      "HelpfulnessNumerator": 10,
      "HelpfulnessDenominator": 10
    }
  ],
  "group_by_product": true,
  "include_top_comments": true,
  "top_comments_per_category": 10
}
```

**Response:**
```json
{
  "total_reviews": 100,
  "processed_reviews": 100,
  "products": {
    "B001234567": {
      "product_id": "B001234567",
      "total_reviews": 50,
      "positive_count": 35,
      "negative_count": 10,
      "neutral_count": 5,
      "positive_percentage": 70.0,
      "negative_percentage": 20.0,
      "neutral_percentage": 10.0,
      "avg_confidence": 0.92,
      "top_positive_comments": [...],
      "top_negative_comments": [...],
      "top_neutral_comments": [...],
      "positive_keywords": ["excellent", "amazing", ...],
      "negative_keywords": ["terrible", "poor", ...],
      "neutral_keywords": ["okay", "average", ...]
    }
  },
  "processing_time_seconds": 12.5,
  "timestamp": "2025-01-20T10:30:00"
}
```

#### `POST /analyze/amazon-format`
Analyze reviews in Amazon format without grouping.

**Request:** Same as bulk-import but returns individual results.

### Timeseries & Aggregation

#### `GET /sentiment/timeseries`
Get aggregated sentiment data over time.

**Query Parameters:**
- `start_time` (optional): Start time in ISO format
- `end_time` (optional): End time in ISO format
- `group_by` (optional): Time grouping - "hour", "day", or "week" (default: "hour")
- `team` (optional): Filter by team name
- `product` (optional): Filter by product name

**Example:**
```
GET /sentiment/timeseries?start_time=2025-01-01T00:00:00&end_time=2025-01-02T00:00:00&group_by=hour&team=TeamA&product=ProductX
```

**Response:**
```json
[
  {
    "time": "2025-01-20T00:00:00",
    "positive": 45,
    "neutral": 30,
    "negative": 25,
    "total": 100,
    "avg_confidence": 0.85,
    "team": "TeamA",
    "product": "ProductX"
  }
]
```

#### `GET /sentiment/statistics`
Get overall statistics about stored sentiment data.

**Response:**
```json
{
  "total_analyses": 10000,
  "days_analyzed": 30,
  "average_confidence": 0.87,
  "first_analysis": "2025-01-01T00:00:00",
  "last_analysis": "2025-01-30T23:59:59",
  "sentiment_distribution": {
    "LABEL_0": 2000,
    "LABEL_1": 3000,
    "LABEL_2": 5000
  }
}
```

### Products

#### `GET /products`
Get list of products with pagination.

**Query Parameters:**
- `limit` (optional): Maximum number of products (default: 100)
- `offset` (optional): Number of products to skip (default: 0)
- `min_reviews` (optional): Minimum number of reviews per product (default: 1)

**Response:**
```json
{
  "products": [
    {
      "product_id": "B001234567",
      "total_reviews": 500,
      "positive": 350,
      "negative": 100,
      "neutral": 50,
      "positive_percentage": 70.0,
      "negative_percentage": 20.0,
      "neutral_percentage": 10.0,
      "avg_confidence": 0.92,
      "first_review": "2025-01-01T00:00:00",
      "last_review": "2025-01-30T23:59:59"
    }
  ],
  "total": 50,
  "limit": 100,
  "offset": 0,
  "has_more": false
}
```

#### `GET /products/{product_id}/timeseries`
Get time series data for a specific product.

**Query Parameters:**
- `start_time` (optional): Start time in ISO format
- `end_time` (optional): End time in ISO format
- `group_by` (optional): Time grouping - "hour", "day", or "week" (default: "day")

#### `GET /products/timeseries/all`
Get time series data for multiple products.

**Query Parameters:**
- `product_ids` (optional): Comma-separated list of product IDs
- `limit` (optional): Maximum number of products if product_ids not specified (default: 50)
- `start_time` (optional): Start time in ISO format
- `end_time` (optional): End time in ISO format
- `group_by` (optional): Time grouping (default: "day")

### Product Comparison

#### `POST /products/compare`
Compare two products based on their sentiment analysis results.

**Request:**
```json
{
  "product_1": {
    "product_id": "B001234567",
    "total_reviews": 500,
    "positive_count": 350,
    "negative_count": 100,
    "neutral_count": 50,
    "positive_percentage": 70.0,
    "negative_percentage": 20.0,
    "neutral_percentage": 10.0,
    "avg_confidence": 0.92,
    "positive_keywords": ["excellent", "amazing"],
    "negative_keywords": ["terrible", "poor"]
  },
  "product_2": {
    "product_id": "B007654321",
    "total_reviews": 300,
    "positive_count": 200,
    "negative_count": 50,
    "neutral_count": 50,
    "positive_percentage": 66.7,
    "negative_percentage": 16.7,
    "neutral_percentage": 16.7,
    "avg_confidence": 0.89,
    "positive_keywords": ["good", "nice"],
    "negative_keywords": ["bad", "disappointing"]
  }
}
```

**Response:** Comparison metrics including differences and common/unique keywords.

### Visualization

#### `GET /api/viz/sentiment-timeseries`
Get sentiment time series data with visualization configuration.

**Query Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `team` (optional): Filter by team name
- `product` (optional): Filter by product name
- `group_by` (optional): Time grouping - "hour", "day", or "week" (default: "hour")
- `chart_type` (optional): Chart type - "line", "bar", or "area" (default: "line")

**Response:** JSON data with Plotly chart configuration.

#### `GET /api/viz/sentiment-dashboard`
Get comprehensive sentiment dashboard data.

**Query Parameters:** Same as sentiment-timeseries

**Response:** Dashboard data with multiple visualizations.

## 💻 Usage Examples

### Python Client Example

```python
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# 1. Health Check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. Single Text Analysis
response = requests.post(f"{BASE_URL}/analyze", json={
    "text": "This is amazing!",
    "team": "TeamA",
    "product": "ProductX",
    "timestamp": datetime.now().isoformat(),
    "metadata": {"source": "test"}
})
result = response.json()
print(f"Sentiment: {result['sentiment']}, Confidence: {result['confidence']}")

# 3. Batch Analysis
response = requests.post(f"{BASE_URL}/analyze/batch", json={
    "feedback_items": [
        {"text": "I love this!", "team": "TeamA", "product": "ProductX"},
        {"text": "This is terrible", "team": "TeamB", "product": "ProductY"},
        {"text": "It's okay", "team": "TeamA", "product": "ProductZ"}
    ]
})
results = response.json()
for result in results:
    print(f"{result['text'][:30]}... -> {result['sentiment']}")

# 4. Bulk Import (Amazon Format)
response = requests.post(f"{BASE_URL}/analyze/bulk-import", json={
    "reviews": [
        {
            "Text": "I absolutely love this product!",
            "ProductId": "B001234567",
            "Score": 5.0,
            "Time": "1346976000",
            "Summary": "Excellent product"
        },
        {
            "Text": "This product broke after one week.",
            "ProductId": "B001234567",
            "Score": 1.0,
            "Time": "1347148800",
            "Summary": "Poor quality"
        }
    ],
    "group_by_product": True,
    "include_top_comments": True,
    "top_comments_per_category": 10
})
result = response.json()
for product_id, product_data in result['products'].items():
    print(f"\nProduct: {product_id}")
    print(f"  Total Reviews: {product_data['total_reviews']}")
    print(f"  Positive: {product_data['positive_percentage']:.1f}%")
    print(f"  Negative: {product_data['negative_percentage']:.1f}%")

# 5. Get Timeseries Data
end_time = datetime.now()
start_time = end_time - timedelta(days=7)
response = requests.get(
    f"{BASE_URL}/sentiment/timeseries",
    params={
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "group_by": "day",
        "team": "TeamA"
    }
)
timeseries = response.json()
for data_point in timeseries:
    print(f"Time: {data_point['time']}, Positive: {data_point['positive']}, Negative: {data_point['negative']}")

# 6. Get Products List
response = requests.get(f"{BASE_URL}/products", params={"limit": 10, "min_reviews": 5})
products = response.json()
for product in products['products']:
    print(f"Product: {product['product_id']}, Reviews: {product['total_reviews']}")

# 7. Get Product Timeseries
response = requests.get(
    f"{BASE_URL}/products/B001234567/timeseries",
    params={"group_by": "day"}
)
product_timeseries = response.json()
print(f"Product timeseries data points: {len(product_timeseries)}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

// Single text analysis
async function analyzeText(text) {
    try {
        const response = await axios.post(`${BASE_URL}/analyze`, {
            text: text,
            metadata: { source: 'web_app' }
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Batch analysis
async function analyzeBatch(texts) {
    try {
        const response = await axios.post(`${BASE_URL}/analyze/batch`, {
            feedback_items: texts.map(text => ({ text }))
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Get timeseries data
async function getTimeseries(startDate, endDate, groupBy = 'day') {
    try {
        const response = await axios.get(`${BASE_URL}/sentiment/timeseries`, {
            params: {
                start_time: startDate,
                end_time: endDate,
                group_by: groupBy
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Usage
(async () => {
    const result = await analyzeText("This is great!");
    console.log(`Sentiment: ${result.sentiment}, Confidence: ${result.confidence}`);
})();
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Single analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I love this product!",
    "team": "TeamA",
    "product": "ProductX"
  }'

# Batch analysis
curl -X POST http://localhost:8000/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{
    "feedback_items": [
      {"text": "Great product!", "team": "TeamA"},
      {"text": "Not good", "team": "TeamB"}
    ]
  }'

# Get timeseries
curl "http://localhost:8000/sentiment/timeseries?group_by=day&team=TeamA"

# Get products
curl "http://localhost:8000/products?limit=10&min_reviews=5"
```

## 🗄️ Database Schema

### Table: `sentiment_results`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing unique identifier |
| `text` | TEXT NOT NULL | The analyzed text |
| `sentiment_label` | TEXT NOT NULL | Sentiment label (LABEL_0, LABEL_1, LABEL_2) |
| `confidence_score` | REAL NOT NULL | Confidence score (0.0 to 1.0) |
| `timestamp` | DATETIME | Analysis timestamp (default: CURRENT_TIMESTAMP) |
| `team` | TEXT | Team name for categorization |
| `product` | TEXT | Product name for categorization |
| `metadata` | TEXT | JSON-encoded metadata |

### Indexes

- `idx_timestamp` on `timestamp`
- `idx_sentiment_label` on `sentiment_label`
- `idx_team` on `team`
- `idx_product` on `product`
- `idx_team_product` on `(team, product)`

### Database Location

- **Default**: `data/sentiment_results.db`
- **Docker**: `/app/data/sentiment_results.db`
- **Kubernetes**: Persistent Volume at `/app/data/sentiment_results.db`

## ⚙️ Configuration

### Model Configuration

The service uses `cardiffnlp/twitter-roberta-base-sentiment-latest` by default. To change the model, modify `app/sentiment_analyzer.py`:

```python
# In SentimentAnalyzer.__init__()
self.model_name = "your-preferred-model-name"
```

### Performance Tuning

1. **Batch Size**: Adjust in `analyze_batch()` method (default: 128)
   ```python
   results = analyzer.analyze_batch(feedback_items, batch_size=256)
   ```

2. **Device**: Automatically detects CUDA availability
   - GPU: Uses float16 for faster inference
   - CPU: Uses float32 for compatibility

3. **Max Length**: Configure token truncation (default: 512)
   ```python
   results = analyzer.analyze_batch(feedback_items, max_length=256)
   ```

### Environment Variables

```bash
# Model configuration
export MODEL_NAME="cardiffnlp/twitter-roberta-base-sentiment-latest"

# Server configuration
export HOST="0.0.0.0"
export PORT="8000"
export LOG_LEVEL="info"

# Database configuration
export DB_PATH="data/sentiment_results.db"
```

### Database Configuration

For production, consider:
- **PostgreSQL**: Better concurrency and scalability
- **Redis**: Caching for frequent queries
- **Connection Pooling**: For high-traffic scenarios

## 🚢 Deployment

The service can be deployed using Docker or Kubernetes. Deployment configurations are available in the repository.

### Docker Deployment

The service includes a `Dockerfile` for containerized deployment. The Docker image packages the application with all dependencies and can be run as a container.

### Kubernetes Deployment

Kubernetes manifests are provided in the `k8s/` directory including:
- Deployment configuration
- Service definitions
- Ingress rules
- Horizontal Pod Autoscaler (HPA)
- Persistent Volume Claims for database storage

See [K8S_DEPLOYMENT_GUIDE.md](K8S_DEPLOYMENT_GUIDE.md) for detailed Kubernetes deployment instructions.

### Production Considerations

1. **Resource Limits**: Configure appropriate CPU/memory limits based on workload
2. **Auto-scaling**: Use HPA for automatic scaling based on load metrics
3. **Monitoring**: Integrate with monitoring solutions (Prometheus/Grafana)
4. **Logging**: Use centralized logging solutions (ELK Stack)
5. **Database**: Consider PostgreSQL migration for production scale and better concurrency
6. **Security**: Configure CORS appropriately, add authentication, and implement rate limiting

## 📁 Project Structure

```
roberta-sentiment-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application and endpoints
│   ├── sentiment_analyzer.py   # Core sentiment analysis logic
│   ├── visualization_api.py    # Visualization endpoints
│   └── config.py               # Configuration settings
├── data/
│   └── sentiment_results.db   # SQLite database
├── models/                     # Model files directory
│   └── roberta-sentiment/     # Local model files
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── pvc.yaml
├── tests/                      # Test files
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── start_service.py           # Service startup script
└── README.md                   # This file
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_service.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Files

- `test_service.py`: API endpoint tests
- `test_local_sentiment.py`: Local sentiment analysis tests
- `test_bulk_import.py`: Bulk import functionality tests
- `test_performance.py`: Performance benchmarking

### Quick Test

```bash
# Test single analysis
python quick_test.py

# Test complete pipeline
python test_complete_pipeline.py
```

## 🔍 API Documentation

Once the service is running, visit:

- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🐛 Troubleshooting

### Common Issues

1. **Model Download Fails**
   - **Solution**: Check internet connection and Hugging Face access
   - **Alternative**: Use local model files in `models/` directory

2. **CUDA Out of Memory**
   - **Solution**: Reduce batch size or use CPU-only mode
   - **Command**: Set `CUDA_VISIBLE_DEVICES=""` to force CPU

3. **Database Locked**
   - **Solution**: Ensure only one instance accesses SQLite database
   - **Alternative**: Use PostgreSQL for concurrent access

4. **Slow Performance**
   - **Solution**: Enable GPU acceleration or reduce batch size
   - **Check**: Verify GPU is detected with `nvidia-smi`

5. **Import Errors**
   - **Solution**: Ensure all dependencies are installed
   - **Command**: `pip install -r requirements.txt --upgrade`

### Logs Location

- **Application logs**: Console output (stdout/stderr)
- **Database**: `data/sentiment_results.db`
- **Docker logs**: `docker logs <container-name>`
- **Kubernetes logs**: `kubectl logs <pod-name> -n roberta-sentiment`

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL="debug"
```

## 📚 Additional Documentation

- [BULK_IMPORT_GUIDE.md](BULK_IMPORT_GUIDE.md) - Bulk import instructions
- [K8S_DEPLOYMENT_GUIDE.md](K8S_DEPLOYMENT_GUIDE.md) - Kubernetes deployment
- [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md) - Local testing guide
- [USING_PYTHON_PATH.md](USING_PYTHON_PATH.md) - Python path configuration
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - General deployment guide
- [FEATURE_ENHANCEMENTS.md](FEATURE_ENHANCEMENTS.md) - Future enhancements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the API documentation at `/docs`
3. Check existing issues in the repository
4. Open a new issue with detailed error information

## 🙏 Acknowledgments

- [Hugging Face Transformers](https://huggingface.co/transformers/) for the RoBERTa model
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Cardiff NLP](https://cardiffnlp.github.io/) for the sentiment model

---

**Made with ❤️ for sentiment analysis**
