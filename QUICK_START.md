# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Service
```bash
python start_service.py
```

### 3. Test the Service
```bash
python test_service.py
```

## 📋 What You Get

✅ **REST API** with 5 endpoints:
- `GET /health` - Health check
- `POST /analyze` - Single text analysis  
- `POST /analyze/batch` - Batch text analysis
- `GET /sentiment/timeseries` - Aggregated sentiment data
- `GET /sentiment/statistics` - Service statistics

✅ **Interactive API Documentation**: http://localhost:8000/docs

✅ **Automatic Model Download**: RoBERTa model downloads on first run

✅ **Database Storage**: SQLite database for historical data

✅ **Timeseries Aggregation**: Hourly/daily/weekly sentiment trends

## 🔧 Key Features

- **High Performance**: GPU acceleration when available
- **Batch Processing**: Efficient processing of large datasets
- **Production Ready**: Health checks, logging, error handling
- **Docker Support**: Ready-to-use Docker configuration
- **Comprehensive Testing**: Built-in test suite

## 📊 Example Usage

```python
import requests

# Analyze single text
response = requests.post("http://localhost:8000/analyze", json={
    "text": "I love this product!"
})
result = response.json()
print(f"Sentiment: {result['sentiment']}, Confidence: {result['confidence']}")

# Get timeseries data
response = requests.get("http://localhost:8000/sentiment/timeseries?group_by=day")
timeseries = response.json()
```

## 🐳 Docker Usage

```bash
# Build and run with Docker
docker-compose up --build

# Or build manually
docker build -t roberta-sentiment-service .
docker run -p 8000:8000 roberta-sentiment-service
```

## 📈 Integration with ETL Services

The service is designed to work seamlessly with ETL pipelines:

1. **ETL Service** uploads bulk data (CSV/JSON)
2. **ETL Service** cleans and preprocesses text
3. **ETL Service** sends batches to `/analyze/batch`
4. **Frontend** calls `/sentiment/timeseries` for visualization

## 🎯 Perfect For

- Customer feedback analysis
- Social media sentiment monitoring  
- Product review analysis
- Real-time sentiment dashboards
- ETL pipeline integration
- Microservices architecture

---

**Need help?** Check the full [README.md](README.md) for detailed documentation.
