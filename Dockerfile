# Dockerfile for RoBERTa Sentiment Analysis Service

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p data logs

# Copy application code
COPY app/ ./app/

# Copy data ingestion and preload scripts
COPY ingest_customer_feedback.py ./
COPY preload_data.py ./
COPY load_1000_records.py ./
COPY amazon_1000_customers_unique_suggestions.csv ./
COPY example_customer_feedback.csv ./
COPY example_customer_feedback.json ./
COPY example_amazon_format.json ./

# Set environment variables
ENV PYTHONPATH=/app
ENV MODEL_NAME=cardiffnlp/twitter-roberta-base-sentiment-latest
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=info

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "app/main.py"]
