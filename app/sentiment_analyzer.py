"""
RoBERTa Sentiment Analysis Service

This module provides the core sentiment analysis functionality using a pre-trained
RoBERTa model from Hugging Face Transformers.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from pathlib import Path
import os

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    pipeline
)
import numpy as np

# No SSL configuration needed - using local model files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    RoBERTa-based sentiment analysis service that provides:
    1. Text sentiment classification
    2. Batch processing capabilities
    3. Historical data storage and aggregation
    """
    
    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base"):
        """
        Initialize the sentiment analyzer with a pre-trained RoBERTa model.
        
        Args:
            model_name: Hugging Face model identifier for RoBERTa sentiment model
                        Default is now an emotion detection model supporting:
                        anger, disgust, fear, joy, neutral, sadness, surprise
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # No SSL configuration needed - using local model files
        
        # Initialize model and tokenizer with fallback mechanisms
        self._load_model_with_fallbacks()
        
        # Initialize database for storing results
        self._init_database()
    
    def _load_model_with_fallbacks(self):
        """Load the RoBERTa model and tokenizer with multiple fallback strategies."""
        # First, try to load from local model directory
        try:
            logger.info("Attempting to load from local model directory...")
            self._try_load_local_model()
            logger.info("Successfully loaded local model")
            return
        except Exception as e:
            logger.warning(f"Failed to load local model: {e}")
        
        # If local model fails, try to use cached models
        try:
            logger.info("Attempting to use cached models...")
            self._try_load_cached_model()
            logger.info("Successfully loaded cached model")
            return
        except Exception as e:
            logger.warning(f"Failed to load cached model: {e}")
        
        # Last resort: try to download models (will likely fail due to SSL)
        model_candidates = [
            self.model_name,  # Target emotion model
            "j-hartmann/emotion-english-distilroberta-base", # Explicit fallback
            "cardiffnlp/twitter-roberta-base-sentiment-latest",  # Original model fallback
            "distilbert-base-uncased-finetuned-sst-2-english",  # Smaller DistilBERT
        ]
        
        for i, model_name in enumerate(model_candidates):
            try:
                logger.info(f"Attempting to download model {i+1}/{len(model_candidates)}: {model_name}")
                success = self._try_load_model(model_name)
                if success:
                    self.model_name = model_name
                    logger.info(f"Successfully loaded model: {model_name}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                continue
        
        # If all strategies fail
        logger.error("All model loading strategies failed")
        raise RuntimeError("Unable to load any sentiment analysis model. Please ensure the local model files are available in the 'models' directory.")
    
    def _try_load_model(self, model_name: str) -> bool:
        """Try to load a specific model with SSL fixes."""
        try:
            # Load tokenizer with SSL fixes
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                use_auth_token=False,
                local_files_only=False
            )
            
            # Load model with SSL fixes
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                use_auth_token=False,
                local_files_only=False
            )
            
            # Move model to appropriate device
            self.model.to(self.device)
            
            # Set model to evaluation mode for faster inference
            self.model.eval()
            
            # Create pipeline for easier inference
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                top_k=None,  # This replaces return_all_scores=True
                batch_size=64,  # Default batch size for pipeline
                truncation=True,  # Enable truncation by default
                padding=True,  # Enable padding by default
                max_length=512  # Max length for efficiency
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load model {model_name}: {e}")
            return False
    
    def _try_load_local_model(self):
        """Try to load the model from local files."""
        try:
            # Define local model paths - check for the actual structure
            possible_paths = [
                Path("models/roberta-sentiment"),  # Expected structure
                Path("models/roberta_sentiment_models(1)/models/roberta-sentiment"),  # Actual structure
                Path("models/roberta_sentiment_models/models/roberta-sentiment"),  # Alternative
            ]
            
            local_model_dir = None
            for path in possible_paths:
                if (path / "model").exists() and (path / "tokenizer").exists():
                    local_model_dir = path
                    break
            
            if local_model_dir is None:
                raise FileNotFoundError(f"Local model files not found. Checked paths: {[str(p) for p in possible_paths]}")
            
            model_path = local_model_dir / "model"
            tokenizer_path = local_model_dir / "tokenizer"
            
            # Check if local model files exist
            if not model_path.exists() or not tokenizer_path.exists():
                raise FileNotFoundError(f"Local model files not found. Expected paths: {model_path}, {tokenizer_path}")
            
            logger.info(f"Loading model from: {model_path}")
            logger.info(f"Loading tokenizer from: {tokenizer_path}")
            
            # Find the actual model files in the Hugging Face cache structure
            model_snapshots = list(model_path.glob("*/snapshots/*"))
            tokenizer_snapshots = list(tokenizer_path.glob("*/snapshots/*"))
            
            if not model_snapshots or not tokenizer_snapshots:
                raise FileNotFoundError(f"Model snapshots not found in {model_path} or {tokenizer_path}")
            
            # Use the first available snapshot
            actual_model_path = model_snapshots[0]
            actual_tokenizer_path = tokenizer_snapshots[0]
            
            logger.info(f"Loading model from snapshot: {actual_model_path}")
            logger.info(f"Loading tokenizer from snapshot: {actual_tokenizer_path}")
            
            # Load tokenizer from local files
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(actual_tokenizer_path),
                local_files_only=True,
                trust_remote_code=True
            )
            
            # Load model from local files
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(actual_model_path),
                local_files_only=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True
            )
            
            # Move model to appropriate device
            self.model.to(self.device)
            
            # Set model to evaluation mode for faster inference
            self.model.eval()
            
            # Create pipeline for easier inference
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                top_k=None,  # This replaces return_all_scores=True
                batch_size=64,  # Default batch size for pipeline
                truncation=True,  # Enable truncation by default
                padding=True,  # Enable padding by default
                max_length=512  # Max length for efficiency
            )
            
            logger.info("Successfully loaded local model")
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            raise
    
    def _try_load_cached_model(self):
        """Try to load a cached model if available."""
        try:
            # Try to use any cached sentiment analysis model
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                top_k=None  # This replaces return_all_scores=True
            )
            
            # Extract model and tokenizer from pipeline
            self.model = self.classifier.model
            self.tokenizer = self.classifier.tokenizer
            
            logger.info("Successfully loaded cached model")
            
        except Exception as e:
            logger.error(f"Failed to load cached model: {e}")
            raise
    
    def _init_database(self):
        """Initialize SQLite database for storing sentiment results."""
        db_path = Path("data/sentiment_results.db")
        db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = str(db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    sentiment_label TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    team TEXT,
                    product TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON sentiment_results(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sentiment_label 
                ON sentiment_results(sentiment_label)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team 
                ON sentiment_results(team)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_product 
                ON sentiment_results(product)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_product 
                ON sentiment_results(team, product)
            """)
    
    def analyze_single(self, text: str, team: Optional[str] = None, product: Optional[str] = None, 
                      timestamp: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze sentiment for a single text.
        
        Args:
            text: Input text to analyze
            team: Team name for categorization
            product: Product name for categorization
            timestamp: Timestamp of the feedback
            metadata: Optional metadata to store with the result
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Run sentiment analysis
            results = self.classifier(text)
            
            # Handle different result formats
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list):
                    # Format: [[{'label': 'positive', 'score': 0.99}, ...]]
                    results = results[0]
                # Extract the highest confidence result
                best_result = max(results, key=lambda x: x['score'])
            else:
                # Fallback for unexpected format
                best_result = results[0] if isinstance(results, list) else results
            
            result = {
                'text': text,
                'sentiment': best_result['label'],
                'confidence': best_result['score'],
                'all_scores': {r['label']: r['score'] for r in results},
                'timestamp': timestamp or datetime.now().isoformat(),
                'team': team,
                'product': product,
                'metadata': metadata or {}
            }
            
            # Store in database
            self._store_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            raise
    
    def analyze_batch(self, feedback_items: List[Dict[str, Any]], 
                     batch_size: int = 128, 
                     store_results: bool = True,
                     max_length: int = 512) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of feedback items.
        
        Args:
            feedback_items: List of feedback items with text, team, product, timestamp, and metadata
            batch_size: Number of items to process per batch (default: 64, increased for speed)
            store_results: Whether to store results in database (default: True, set False for faster testing)
            max_length: Maximum token length for truncation (default: 512)
            
        Returns:
            List of sentiment analysis results
        """
        
        results = []
        
        try:
            # Extract texts for batch processing and truncate if needed
            # More aggressive truncation for speed
            texts = []
            for item in feedback_items:
                text = item['text']
                # Truncate text if too long (keep first max_length * 3 characters for speed)
                # This is more aggressive than before to reduce processing time
                if len(text) > max_length * 3:
                    text = text[:max_length * 3]
                texts.append(text)
            
            # Process in batches - increased batch size for better throughput
            # Use torch.no_grad() for faster inference (no gradient computation)
            with torch.no_grad():
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    batch_items = feedback_items[i:i + batch_size]
                    
                    # Run batch inference with truncation and padding
                    # Using faster settings: truncation=True, padding=True, max_length
                    # Pipeline handles batching internally, so we pass the list directly
                    batch_results = self.classifier(
                        batch_texts,
                        truncation=True,
                        padding=True,
                        max_length=max_length
                    )
                    
                    # Handle batch results - pipeline returns list of results
                    for j, (item, result) in enumerate(zip(batch_items, batch_results)):
                        # Handle different result formats
                        if isinstance(result, list) and len(result) > 0:
                            if isinstance(result[0], list):
                                # Format: [[{'label': 'positive', 'score': 0.99}, ...]]
                                result = result[0]
                            # Extract the highest confidence result
                            best_result = max(result, key=lambda x: x['score'])
                        else:
                            # Fallback for unexpected format
                            best_result = result[0] if isinstance(result, list) else result
                        
                        analysis_result = {
                            'text': item['text'],
                            'sentiment': best_result['label'],
                            'confidence': best_result['score'],
                            'all_scores': {r['label']: r['score'] for r in result} if isinstance(result, list) else {},
                            'timestamp': item.get('timestamp') or datetime.now().isoformat(),
                            'team': item.get('team'),
                            'product': item.get('product'),
                            'metadata': item.get('metadata', {})
                        }
                        
                        results.append(analysis_result)
                        # Only store in database if requested (faster for testing)
                        if store_results:
                            self._store_result(analysis_result)
                    
                    # Log progress less frequently for speed
                    if (i // batch_size + 1) % 10 == 0 or i + batch_size >= len(texts):
                        logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        except Exception as e:
            logger.error(f"Error analyzing batch: {e}")
            raise
        
        return results
    
    def _store_result(self, result: Dict[str, Any]):
        """Store sentiment analysis result in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO sentiment_results 
                    (text, sentiment_label, confidence_score, timestamp, team, product, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['text'],
                    result['sentiment'],
                    result['confidence'],
                    result['timestamp'],
                    result.get('team'),
                    result.get('product'),
                    json.dumps(result['metadata'])
                ))
        except Exception as e:
            logger.error(f"Error storing result: {e}")
    
    def get_aggregated_sentiment(self, 
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None,
                                group_by: str = "hour",
                                team: Optional[str] = None,
                                product: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get aggregated sentiment data over time with optional team/product filtering.
        
        Args:
            start_time: Start time for aggregation (default: 24 hours ago)
            end_time: End time for aggregation (default: now)
            group_by: Time grouping ("hour", "day", "week")
            team: Filter by team name (optional)
            product: Filter by product name (optional)
            
        Returns:
            List of aggregated sentiment data
        """
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = end_time - timedelta(days=1)
        
        # Determine time format based on group_by
        if group_by == "hour":
            time_format = "%Y-%m-%dT%H:00:00"
            time_truncate = "strftime('%Y-%m-%dT%H:00:00', timestamp)"
        elif group_by == "day":
            time_format = "%Y-%m-%dT00:00:00"
            time_truncate = "strftime('%Y-%m-%dT00:00:00', timestamp)"
        elif group_by == "week":
            time_format = "%Y-%m-%dT00:00:00"
            time_truncate = "strftime('%Y-%m-%dT00:00:00', date(timestamp, 'weekday 0', '-6 days'))"
        else:
            raise ValueError("group_by must be 'hour', 'day', or 'week'")
        
        try:
            # Build WHERE clause with filters
            where_conditions = ["timestamp BETWEEN ? AND ?"]
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if team:
                where_conditions.append("team = ?")
                params.append(team)
            
            if product:
                where_conditions.append("product = ?")
                params.append(product)
            
            where_clause = " AND ".join(where_conditions)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        {time_truncate} as time_period,
                        sentiment_label,
                        team,
                        product,
                        COUNT(*) as count,
                        AVG(confidence_score) as avg_confidence
                    FROM sentiment_results
                    WHERE {where_clause}
                    GROUP BY time_period, sentiment_label, team, product
                    ORDER BY time_period
                """.format(time_truncate=time_truncate, where_clause=where_clause), params)
                
                # Group results by time period
                time_data = {}
                for row in cursor.fetchall():
                    time_period, sentiment, team_val, product_val, count, avg_confidence = row
                    
                    # Create unique key for time period + team + product combination
                    key = f"{time_period}_{team_val or 'all'}_{product_val or 'all'}"
                    
                    if key not in time_data:
                        time_data[key] = {
                            'time': time_period,
                            'positive': 0,
                            'neutral': 0,
                            'negative': 0,
                            'total': 0,
                            'avg_confidence': 0.0,
                            'team': team_val,
                            'product': product_val
                        }
                    
                    # Map sentiment labels to our standard format
                    sentiment_key = self._normalize_sentiment_label(sentiment)
                    time_data[key][sentiment_key] = count
                    time_data[key]['total'] += count
                    time_data[key]['avg_confidence'] = avg_confidence
                
                return list(time_data.values())
                
        except Exception as e:
            logger.error(f"Error getting aggregated sentiment: {e}")
            raise
    
    def _normalize_sentiment_label(self, label: str) -> str:
        """
        Normalize sentiment labels.
        For the emotion model, we keep the specific emotion label.
        For legacy compatibility, we might need mapping elsewhere, but here we store the truth.
        """
        return label.lower()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about stored sentiment data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_analyses,
                        COUNT(DISTINCT DATE(timestamp)) as days_analyzed,
                        AVG(confidence_score) as avg_confidence,
                        MIN(timestamp) as first_analysis,
                        MAX(timestamp) as last_analysis
                    FROM sentiment_results
                """)
                
                stats = cursor.fetchone()
                
                # Get sentiment distribution
                cursor = conn.execute("""
                    SELECT sentiment_label, COUNT(*) as count
                    FROM sentiment_results
                    GROUP BY sentiment_label
                """)
                
                sentiment_dist = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'total_analyses': stats[0],
                    'days_analyzed': stats[1],
                    'average_confidence': stats[2],
                    'first_analysis': stats[3],
                    'last_analysis': stats[4],
                    'sentiment_distribution': sentiment_dist
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise
    
    def get_products_list(self, limit: int = 100, offset: int = 0, 
                          min_reviews: int = 1) -> Dict[str, Any]:
        """
        Get list of products with pagination and filtering.
        
        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip
            min_reviews: Minimum number of reviews per product
            
        Returns:
            Dictionary with products list and pagination info
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get total count
                cursor = conn.execute("""
                    SELECT COUNT(*) as total
                    FROM (
                        SELECT product
                        FROM sentiment_results
                        WHERE product IS NOT NULL 
                        AND product != 'unknown'
                        GROUP BY product
                        HAVING COUNT(*) >= ?
                    )
                """, (min_reviews,))
                
                total_count = cursor.fetchone()[0]
                
                # Get products with review counts and sentiment distribution
                cursor = conn.execute("""
                    SELECT 
                        product,
                        COUNT(*) as total_reviews,
                        SUM(CASE WHEN sentiment_label IN ('joy', 'positive', 'label_2') THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN sentiment_label IN ('anger', 'disgust', 'fear', 'sadness', 'negative', 'label_0') THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN sentiment_label IN ('neutral', 'surprise', 'label_1') THEN 1 ELSE 0 END) as neutral_count,
                        AVG(confidence_score) as avg_confidence,
                        MIN(timestamp) as first_review,
                        MAX(timestamp) as last_review
                    FROM sentiment_results
                    WHERE product IS NOT NULL 
                    AND product != 'unknown'
                    GROUP BY product
                    HAVING COUNT(*) >= ?
                    ORDER BY total_reviews DESC
                    LIMIT ? OFFSET ?
                """, (min_reviews, limit, offset))
                
                products = []
                for row in cursor.fetchall():
                    product, total, pos, neg, neu, conf, first, last = row
                    products.append({
                        'product_id': product,
                        'total_reviews': total,
                        'positive': pos,
                        'negative': neg,
                        'neutral': neu,
                        'positive_percentage': (pos / total * 100) if total > 0 else 0,
                        'negative_percentage': (neg / total * 100) if total > 0 else 0,
                        'neutral_percentage': (neu / total * 100) if total > 0 else 0,
                        'avg_confidence': conf,
                        'first_review': first,
                        'last_review': last
                    })
                
                return {
                    'products': products,
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
                
        except Exception as e:
            logger.error(f"Error getting products list: {e}")
            raise
    
    def get_product_timeseries(self, product_id: str,
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              group_by: str = "day") -> List[Dict[str, Any]]:
        """
        Get time series data for a specific product.
        
        Args:
            product_id: Product identifier
            start_time: Start time for aggregation
            end_time: End time for aggregation
            group_by: Time grouping ("hour", "day", "week")
            
        Returns:
            List of time series data points for the product
        """
        return self.get_aggregated_sentiment(
            start_time=start_time,
            end_time=end_time,
            group_by=group_by,
            product=product_id
        )
    
    def get_products_timeseries(self, product_ids: Optional[List[str]] = None,
                                limit: int = 50,
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None,
                                group_by: str = "day") -> Dict[str, Any]:
        """
        Get time series data for multiple products, suitable for UI display.
        
        Args:
            product_ids: List of product IDs (None = get top products by review count)
            limit: Maximum number of products if product_ids is None
            start_time: Start time for aggregation
            end_time: End time for aggregation
            group_by: Time grouping ("hour", "day", "week")
            
        Returns:
            Dictionary with time series data organized by product
        """
        try:
            # If no product IDs specified, get top products
            if product_ids is None:
                products_data = self.get_products_list(limit=limit, min_reviews=1)
                product_ids = [p['product_id'] for p in products_data['products']]
            
            # Get time series for each product
            products_timeseries = {}
            for product_id in product_ids:
                timeseries = self.get_product_timeseries(
                    product_id=product_id,
                    start_time=start_time,
                    end_time=end_time,
                    group_by=group_by
                )
                products_timeseries[product_id] = timeseries
            
            return {
                'products': products_timeseries,
                'product_ids': product_ids,
                'group_by': group_by,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None
            }
            
        except Exception as e:
            logger.error(f"Error getting products timeseries: {e}")
            raise


# Global analyzer instance
analyzer = None

def get_analyzer() -> SentimentAnalyzer:
    """Get or create the global analyzer instance."""
    global analyzer
    if analyzer is None:
        analyzer = SentimentAnalyzer()
    return analyzer
