"""
FastAPI application for RoBERTa Sentiment Analysis Service

This module provides REST API endpoints for:
1. Single and batch sentiment analysis
2. Aggregated sentiment data retrieval
3. Service health and statistics
"""

import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

import os
from pathlib import Path

from .sentiment_analyzer import get_analyzer, SentimentAnalyzer
from .visualization_api import router as viz_router

# Base directory (roberta folder, parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class TextAnalysisRequest(BaseModel):
    """Request model for single text analysis."""
    text: str = Field(..., description="Text to analyze for sentiment")
    team: Optional[str] = Field(default=None, description="Team name for categorization")
    product: Optional[str] = Field(default=None, description="Product name for categorization")
    timestamp: Optional[str] = Field(default=None, description="Timestamp of the feedback")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional optional metadata")


class FeedbackItem(BaseModel):
    """Individual feedback item with team and product context."""
    text: str = Field(..., description="Text to analyze for sentiment")
    team: Optional[str] = Field(default=None, description="Team name for categorization")
    product: Optional[str] = Field(default=None, description="Product name for categorization")
    timestamp: Optional[str] = Field(default=None, description="Timestamp of the feedback")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional optional metadata")


class AmazonReviewItem(BaseModel):
    """Amazon dataset format review item."""
    Id: Optional[str] = Field(default=None, description="Review ID")
    ProductId: Optional[str] = Field(default=None, description="Product identifier (ASIN)")
    UserId: Optional[str] = Field(default=None, description="User identifier")
    ProfileName: Optional[str] = Field(default=None, description="Profile name")
    HelpfulnessNumerator: Optional[int] = Field(default=None, description="Helpfulness numerator")
    HelpfulnessDenominator: Optional[int] = Field(default=None, description="Helpfulness denominator")
    Score: Optional[float] = Field(default=None, description="Rating score (1-5)")
    Time: Optional[str] = Field(default=None, description="Review timestamp")
    Summary: Optional[str] = Field(default=None, description="Review summary")
    ProductName: Optional[str] = Field(default=None, description="Product Name")
    ProductDescription: Optional[str] = Field(default=None, description="Product Description")
    Text: str = Field(..., description="Review text (required)")
    Customer_Type: Optional[str] = Field(default=None, description="Customer type (Premium/Normal/Trial)")
    Suggestions: Optional[str] = Field(default=None, description="AI-generated suggestion for this review")


class AmazonBatchRequest(BaseModel):
    """Batch request in Amazon dataset format."""
    reviews: List[AmazonReviewItem] = Field(..., description="List of Amazon format reviews")


class BulkImportRequest(BaseModel):
    """Bulk import request for Amazon format reviews."""
    reviews: List[AmazonReviewItem] = Field(..., description="List of Amazon format reviews to import")
    group_by_product: bool = Field(default=True, description="Group results by product")
    include_top_comments: bool = Field(default=True, description="Include top comments per category")
    top_comments_per_category: int = Field(default=10, description="Number of top comments per category")


class ProductSentimentSummary(BaseModel):
    """Sentiment summary for a product."""
    product_id: str
    total_reviews: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    avg_confidence: float
    # New field for detailed emotion breakdown
    emotion_counts: Dict[str, int] = Field(default_factory=dict, description="Counts for each specific emotion")
    product_name: Optional[str] = Field(default=None, description="Name of the product")
    product_description: Optional[str] = Field(default=None, description="Concise description/summary of the product")
    top_positive_comments: List[Dict[str, Any]]
    top_negative_comments: List[Dict[str, Any]]
    top_neutral_comments: List[Dict[str, Any]]
    positive_keywords: List[str] = Field(default_factory=list, description="Top keywords from positive reviews")
    negative_keywords: List[str] = Field(default_factory=list, description="Top keywords from negative reviews")
    neutral_keywords: List[str] = Field(default_factory=list, description="Top keywords from neutral reviews")


class BulkImportResponse(BaseModel):
    """Response for bulk import."""
    total_reviews: int
    processed_reviews: int
    products: Dict[str, ProductSentimentSummary]
    processing_time_seconds: float
    timestamp: str


class ProductComparisonRequest(BaseModel):
    """Request model for product comparison."""
    product_1: ProductSentimentSummary = Field(..., description="First product data to compare")
    product_2: ProductSentimentSummary = Field(..., description="Second product data to compare")


class ProductComparisonResponse(BaseModel):
    """Response model for product comparison."""
    product_1: ProductSentimentSummary
    product_2: ProductSentimentSummary
    comparison: Dict[str, Any] = Field(..., description="Comparison metrics")
    timestamp: str


class BatchAnalysisRequest(BaseModel):
    """Request model for batch text analysis with team/product context."""
    feedback_items: List[FeedbackItem] = Field(..., description="List of feedback items to analyze")


class SentimentResult(BaseModel):
    """Response model for sentiment analysis result."""
    text: str
    sentiment: str
    confidence: float
    all_scores: Dict[str, float]
    timestamp: str
    team: Optional[str] = None
    product: Optional[str] = None
    metadata: Dict[str, Any]


class AggregatedSentimentData(BaseModel):
    """Response model for aggregated sentiment data."""
    time: str
    positive: int
    neutral: int
    negative: int
    total: int
    avg_confidence: float
    team: Optional[str] = None
    product: Optional[str] = None


class ServiceStats(BaseModel):
    """Response model for service statistics."""
    total_analyses: int
    days_analyzed: int
    average_confidence: float
    first_analysis: Optional[str]
    last_analysis: Optional[str]
    sentiment_distribution: Dict[str, int]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    model_loaded: bool
    device: str


# Global analyzer instance
analyzer: Optional[SentimentAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global analyzer
    logger.info("Starting RoBERTa Sentiment Analysis Service...")
    
    try:
        analyzer = get_analyzer()
        logger.info("Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    
    yield
    
    logger.info("Shutting down service...")


# Create FastAPI app
app = FastAPI(
    title="RoBERTa Sentiment Analysis Service",
    description="A REST API service for sentiment analysis using RoBERTa models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include visualization router
app.include_router(viz_router)


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the bulk import UI"""
    with open(BASE_DIR / "bulk_import_ui.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        model_loaded=True,
        device=analyzer.device
    )


@app.post("/analyze", response_model=SentimentResult)
async def analyze_single_text(request: TextAnalysisRequest):
    """
    Analyze sentiment for a single text with team and product context.
    
    Args:
        request: Text analysis request containing text, team, product, timestamp and optional metadata
        
    Returns:
        Sentiment analysis result
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        result = analyzer.analyze_single(
            text=request.text,
            team=request.team,
            product=request.product,
            timestamp=request.timestamp,
            metadata=request.metadata
        )
        return SentimentResult(**result)
    except Exception as e:
        logger.error(f"Error in single text analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/batch", response_model=List[SentimentResult])
async def analyze_batch_texts(request: BatchAnalysisRequest):
    """
    Analyze sentiment for a batch of feedback items with team and product context.
    
    Args:
        request: Batch analysis request containing list of feedback items
        
    Returns:
        List of sentiment analysis results
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if len(request.feedback_items) == 0:
        raise HTTPException(status_code=400, detail="No feedback items provided")
    
    if len(request.feedback_items) > 1000:
        raise HTTPException(status_code=400, detail="Batch size too large (max 1000)")
    
    try:
        # Convert Pydantic models to dictionaries
        feedback_items = [item.dict() for item in request.feedback_items]
        results = analyzer.analyze_batch(feedback_items)
        return [SentimentResult(**result) for result in results]
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@app.post("/analyze/bulk-import", response_model=BulkImportResponse)
async def bulk_import_reviews(request: BulkImportRequest):
    """
    Bulk import reviews in Amazon dataset format and get classified output grouped by product.
    
    This endpoint:
    1. Processes reviews through sentiment analysis
    2. Groups results by product
    3. Calculates sentiment statistics per product
    4. Returns top comments for each category (positive, negative, neutral) per product
    
    Args:
        request: Bulk import request with reviews in Amazon format
        
    Returns:
        Bulk import response with product-grouped results and top comments
    """
    global analyzer
    import time
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if len(request.reviews) == 0:
        raise HTTPException(status_code=400, detail="No reviews provided")
    
    if len(request.reviews) > 10000:
        raise HTTPException(status_code=400, detail="Batch size too large (max 10000)")
    
    start_time = time.time()
    
    try:
        # Convert Amazon format to internal format
        feedback_items = []
        for review in request.reviews:
            text = review.Text
            product = review.ProductId or 'unknown'
            
            # Parse timestamp (Amazon dataset uses Unix timestamps)
            timestamp = datetime.now().isoformat()
            if review.Time:
                try:
                    # Try Unix timestamp (integer or string)
                    if isinstance(review.Time, (int, float)):
                        timestamp = datetime.fromtimestamp(review.Time).isoformat()
                    elif isinstance(review.Time, str):
                        # Try Unix timestamp as string
                        try:
                            unix_ts = float(review.Time)
                            timestamp = datetime.fromtimestamp(unix_ts).isoformat()
                        except ValueError:
                            # Try ISO format
                            timestamp = datetime.fromisoformat(review.Time.replace('Z', '+00:00')).isoformat()
                except Exception as e:
                    logger.debug(f"Could not parse timestamp '{review.Time}': {e}")
                    timestamp = datetime.now().isoformat()
            
            # Build metadata
            metadata = {}
            if review.Score is not None:
                metadata['rating'] = float(review.Score)
                if review.Score >= 4:
                    metadata['expected_sentiment'] = 'positive'
                elif review.Score <= 2:
                    metadata['expected_sentiment'] = 'negative'
                else:
                    metadata['expected_sentiment'] = 'neutral'
            
            if review.Id:
                metadata['review_id'] = review.Id
            if review.UserId:
                metadata['user_id'] = review.UserId
            if review.ProfileName:
                metadata['profile_name'] = review.ProfileName
            if review.Summary:
                metadata['summary'] = review.Summary
            if review.HelpfulnessNumerator is not None:
                metadata['helpfulness_numerator'] = review.HelpfulnessNumerator
            if review.HelpfulnessDenominator is not None:
                metadata['helpfulness_denominator'] = review.HelpfulnessDenominator
            
            feedback_items.append({
                'text': text,
                'team': review.Customer_Type if hasattr(review, 'Customer_Type') and review.Customer_Type else None,
                'product': product,
                'metadata': metadata if metadata else {}
            })

            # Store suggestion from CSV if available
            if hasattr(review, 'Suggestions') and review.Suggestions:
                feedback_items[-1]['metadata']['suggestion'] = review.Suggestions

            # Store potential product name mapping in metadata so it survives analysis
            if review.ProductName:
                feedback_items[-1]['metadata']['product_name'] = review.ProductName

            if review.ProductDescription:
                feedback_items[-1]['metadata']['product_description'] = review.ProductDescription
        
        # Process through analyzer
        results = analyzer.analyze_batch(
            feedback_items,
            batch_size=128,
            store_results=True
        )
        
        # Group by product
        products_data = {}
        for result in results:
            product_id = result.get('product', 'unknown')
            
            if product_id not in products_data:
                products_data[product_id] = {
                    'reviews': [],
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'total_confidence': 0.0,
                    'total_confidence': 0.0,
                    'product_names': Counter(),
                    'product_descriptions': Counter()
                }
            
            products_data[product_id]['reviews'].append(result)
            products_data[product_id]['total_confidence'] += result.get('confidence', 0.0)
            
            # Track product names from metadata
            meta = result.get('metadata', {})
            if meta and 'product_name' in meta:
                products_data[product_id]['product_names'][meta['product_name']] += 1
            
            if meta and 'product_description' in meta:
                products_data[product_id]['product_descriptions'][meta['product_description']] += 1

            
            # Count sentiments
            sentiment = result.get('sentiment', '').lower()
            
            # Initialize emotion counts if not present
            if 'emotion_counts' not in products_data[product_id]:
                products_data[product_id]['emotion_counts'] = Counter()
            
            # Update specific emotion count
            products_data[product_id]['emotion_counts'][sentiment] += 1
            
            # Aggregation for legacy 3-way sentiment (Positive/Negative/Neutral)
            # Map specific emotions to broad categories
            is_positive = sentiment in ['joy', 'positive', 'label_2']
            is_negative = sentiment in ['anger', 'disgust', 'fear', 'sadness', 'negative', 'label_0']
            
            if is_positive:
                products_data[product_id]['positive'] += 1
            elif is_negative:
                products_data[product_id]['negative'] += 1
            else:
                # Neutral, Surprise, and everything else fall here
                products_data[product_id]['neutral'] += 1
        
        # Build response with top comments
        products_summary = {}
        for product_id, data in products_data.items():
            total = len(data['reviews'])
            avg_confidence = data['total_confidence'] / total if total > 0 else 0.0
            
            # Get top comments for each category
            top_positive = get_top_comments(
                data['reviews'],
                'positive',
                request.top_comments_per_category if request.include_top_comments else 0
            )
            top_negative = get_top_comments(
                data['reviews'],
                'negative',
                request.top_comments_per_category if request.include_top_comments else 0
            )
            top_neutral = get_top_comments(
                data['reviews'],
                'neutral',
                request.top_comments_per_category if request.include_top_comments else 0
            )
            
            # Extract keywords for each sentiment category
            positive_keywords = extract_keywords(data['reviews'], 'positive', top_n=10)
            negative_keywords = extract_keywords(data['reviews'], 'negative', top_n=10)
            neutral_keywords = extract_keywords(data['reviews'], 'neutral', top_n=10)
            
            # Determine Product Name (most common if available)
            product_name = data['product_names'].most_common(1)[0][0] if data['product_names'] else None
            
            # Determine Product Description (most common if available)
            product_description_from_csv = data['product_descriptions'].most_common(1)[0][0] if data['product_descriptions'] else None
            
            # Generate Description from top keywords (Concise summary)
            all_keywords = []
            seen_keywords = set()
            for k in positive_keywords + negative_keywords:
                if k not in seen_keywords:
                    all_keywords.append(k)
                    seen_keywords.add(k)
            
            # Use CSV description if available, otherwise fallback to keywords
            product_description = product_description_from_csv if product_description_from_csv else ("Key themes: " + ", ".join(all_keywords[:5]) if all_keywords else "No key themes detected.")

            products_summary[product_id] = ProductSentimentSummary(
                product_id=product_id,
                total_reviews=total,
                positive_count=data['positive'],
                negative_count=data['negative'],
                neutral_count=data['neutral'],
                positive_percentage=(data['positive'] / total * 100) if total > 0 else 0.0,
                negative_percentage=(data['negative'] / total * 100) if total > 0 else 0.0,
                neutral_percentage=(data['neutral'] / total * 100) if total > 0 else 0.0,
                avg_confidence=avg_confidence,
                emotion_counts=dict(data.get('emotion_counts', {})),
                product_name=product_name,
                product_description=product_description,
                top_positive_comments=top_positive,
                top_negative_comments=top_negative,
                top_neutral_comments=top_neutral,
                positive_keywords=positive_keywords,
                negative_keywords=negative_keywords,
                neutral_keywords=neutral_keywords
            )
        
        processing_time = time.time() - start_time
        
        return BulkImportResponse(
            total_reviews=len(request.reviews),
            processed_reviews=len(results),
            products=products_summary,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk import: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")


@app.post("/products/compare", response_model=ProductComparisonResponse)
async def compare_products(request: ProductComparisonRequest):
    """
    Compare two products based on their sentiment analysis results.
    
    This endpoint:
    1. Compares metrics (sentiment percentages, confidence, keywords)
    2. Returns side-by-side comparison with differences
    
    Args:
        request: Product comparison request with two product summaries
        
    Returns:
        Product comparison response with both products' data and comparison metrics
    """
    try:
        product_1 = request.product_1
        product_2 = request.product_2
        
        # Calculate comparison metrics
        comparison = {
            'positive_percentage_diff': product_1.positive_percentage - product_2.positive_percentage,
            'negative_percentage_diff': product_1.negative_percentage - product_2.negative_percentage,
            'neutral_percentage_diff': product_1.neutral_percentage - product_2.neutral_percentage,
            'confidence_diff': product_1.avg_confidence - product_2.avg_confidence,
            'total_reviews_diff': product_1.total_reviews - product_2.total_reviews,
            'better_product': (
                product_1.product_id if product_1.positive_percentage > product_2.positive_percentage
                else product_2.product_id
            ),
            'common_positive_keywords': list(set(product_1.positive_keywords) & set(product_2.positive_keywords)),
            'common_negative_keywords': list(set(product_1.negative_keywords) & set(product_2.negative_keywords)),
            'unique_positive_keywords_p1': list(set(product_1.positive_keywords) - set(product_2.positive_keywords)),
            'unique_positive_keywords_p2': list(set(product_2.positive_keywords) - set(product_1.positive_keywords)),
            'unique_negative_keywords_p1': list(set(product_1.negative_keywords) - set(product_2.negative_keywords)),
            'unique_negative_keywords_p2': list(set(product_2.negative_keywords) - set(product_1.negative_keywords))
        }
        
        return ProductComparisonResponse(
            product_1=product_1,
            product_2=product_2,
            comparison=comparison,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in product comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Product comparison failed: {str(e)}")


def extract_keywords(reviews: List[Dict[str, Any]], sentiment: str, top_n: int = 10) -> List[str]:
    """
    Extract top keywords from reviews of a specific sentiment category.
    
    Uses word frequency analysis for fast, reliable keyword extraction
    without requiring external model downloads.
    
    Args:
        reviews: List of review results
        sentiment: Sentiment category ('positive', 'negative', 'neutral')
        top_n: Number of top keywords to return
        
    Returns:
        List of top keywords
    """
    if top_n == 0:
        return []
    
    # Filter by sentiment
    sentiment_lower = sentiment.lower()
    filtered_reviews = []
    
    for review in reviews:
        review_sentiment = review.get('sentiment', '').lower()
        is_match = False
        
        if sentiment_lower == 'positive':
            is_match = review_sentiment in ['joy', 'positive', 'label_2']
        elif sentiment_lower == 'negative':
            is_match = review_sentiment in ['anger', 'disgust', 'fear', 'sadness', 'negative', 'label_0']
        else:  # neutral
            is_match = review_sentiment in ['neutral', 'surprise', 'label_1']
        
        if is_match:
            filtered_reviews.append(review)
    
    if not filtered_reviews:
        return []
    
    # Combine all review texts into a single document
    combined_text = ' '.join([review.get('text', '') for review in filtered_reviews])
    
    # Skip if text is too short
    if len(combined_text.strip()) < 50:
        return []
    
    # Use simple keyword extraction (KeyBERT disabled to avoid SSL/network issues)
    # This uses word frequency analysis which is fast and doesn't require model downloads
    return _extract_keywords_simple(filtered_reviews, top_n)


def _extract_keywords_simple(reviews: List[Dict[str, Any]], top_n: int = 10) -> List[str]:
    """
    Fallback simple keyword extraction using word frequency.
    
    Args:
        reviews: List of review results
        top_n: Number of top keywords to return
        
    Returns:
        List of top keywords
    """
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 'all',
        'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'just'
    }
    
    # Extract words from all reviews
    all_words = []
    for review in reviews:
        text = review.get('text', '').lower()
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-z]{3,}\b', text)  # Words with 3+ letters
        # Filter out stop words
        words = [w for w in words if w not in stop_words and len(w) > 2]
        all_words.extend(words)
    
    # Count word frequencies
    word_counts = Counter(all_words)
    
    # Get top N keywords
    top_keywords = [word for word, count in word_counts.most_common(top_n)]
    
    return top_keywords


def get_top_comments(reviews: List[Dict[str, Any]], sentiment: str, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Get top N comments for a specific sentiment category.
    
    Ranking logic:
    1. Confidence score (higher is better)
    2. Helpfulness score (if available)
    3. Recency (newer is better)
    4. Text length (longer, more detailed reviews)
    
    Args:
        reviews: List of review results
        sentiment: Sentiment category ('positive', 'negative', 'neutral')
        top_n: Number of top comments to return
        
    Returns:
        List of top comments with ranking scores
    """
    if top_n == 0:
        return []
    
    # Filter by sentiment
    sentiment_lower = sentiment.lower()
    filtered_reviews = []
    
    for review in reviews:
        review_sentiment = review.get('sentiment', '').lower()
        is_match = False
        
        if sentiment_lower == 'positive':
            is_match = review_sentiment in ['joy', 'positive', 'label_2']
        elif sentiment_lower == 'negative':
            is_match = review_sentiment in ['anger', 'disgust', 'fear', 'sadness', 'negative', 'label_0']
        else:  # neutral
            is_match = review_sentiment in ['neutral', 'surprise', 'label_1']
        
        if is_match:
            filtered_reviews.append(review)
    
    if not filtered_reviews:
        return []
    
    # Calculate ranking score for each review
    scored_reviews = []
    for review in filtered_reviews:
        # Base score: confidence (0-1, weighted 40%)
        confidence = review.get('confidence', 0.0)
        confidence_score = confidence * 0.4
        
        # Helpfulness score (if available, weighted 30%)
        helpfulness_score = 0.0
        metadata = review.get('metadata', {})
        if metadata:
            num = metadata.get('helpfulness_numerator', 0)
            den = metadata.get('helpfulness_denominator', 0)
            if den > 0:
                helpfulness_ratio = num / den
                helpfulness_score = helpfulness_ratio * 0.3
        
        # Recency score (weighted 20%)
        # Newer reviews get higher score (normalized to 0-1)
        try:
            timestamp = review.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp, str):
                # Try ISO format first
                try:
                    review_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    # Try Unix timestamp
                    try:
                        unix_ts = float(timestamp)
                        review_date = datetime.fromtimestamp(unix_ts)
                    except (ValueError, TypeError):
                        review_date = datetime.now()
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                review_date = datetime.fromtimestamp(timestamp)
            else:
                review_date = timestamp if isinstance(timestamp, datetime) else datetime.now()
            
            # Days since review (more recent = higher score)
            if isinstance(review_date, datetime):
                if review_date.tzinfo:
                    review_date = review_date.replace(tzinfo=None)
                days_ago = (datetime.now() - review_date).days
            else:
                days_ago = 0
            
            # Normalize: 0 days = 1.0, 365 days = 0.0
            recency_score = max(0.0, 1.0 - (days_ago / 365.0)) * 0.2
        except Exception as e:
            logger.debug(f"Could not calculate recency score: {e}")
            recency_score = 0.1  # Default if can't parse
        
        # Text quality score (weighted 10%)
        # Longer, more detailed reviews get higher score
        text = review.get('text', '')
        text_length = len(text)
        # Normalize: 0-1000 chars = 0-1.0
        text_score = min(1.0, text_length / 1000.0) * 0.1
        
        # Total score
        total_score = confidence_score + helpfulness_score + recency_score + text_score
        
        scored_reviews.append({
            'text': text,
            'sentiment': review.get('sentiment', ''),
            'confidence': confidence,
            'product': review.get('product', 'unknown'),
            'timestamp': review.get('timestamp', ''),
            'metadata': metadata,
            'ranking_score': total_score,
            'confidence_score': confidence_score,
            'helpfulness_score': helpfulness_score,
            'recency_score': recency_score,
            'text_score': text_score
        })
    
    # Sort by ranking score (descending)
    scored_reviews.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    # Return top N
    return scored_reviews[:top_n]


@app.post("/analyze/amazon-format", response_model=List[SentimentResult])
async def analyze_amazon_format(request: AmazonBatchRequest):
    """
    Analyze sentiment for reviews in Amazon dataset format.
    
    Accepts reviews in Amazon dataset format with columns:
    - Text: Review text (required)
    - ProductId: Product identifier
    - Score: Rating (1-5)
    - Time: Review timestamp
    - Other fields: Id, UserId, ProfileName, Summary, etc.
    
    Args:
        request: Batch request containing list of Amazon format reviews
        
    Returns:
        List of sentiment analysis results with product and metadata
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if len(request.reviews) == 0:
        raise HTTPException(status_code=400, detail="No reviews provided")
    
    if len(request.reviews) > 1000:
        raise HTTPException(status_code=400, detail="Batch size too large (max 1000)")
    
    try:
        # Convert Amazon format to internal format
        feedback_items = []
        for review in request.reviews:
            # Extract text (required)
            text = review.Text
            
            # Extract product ID
            product = review.ProductId or 'unknown'
            
            # Extract timestamp
            timestamp = review.Time or datetime.now().isoformat()
            
            # Build metadata from all fields
            metadata = {}
            if review.Score is not None:
                metadata['rating'] = float(review.Score)
                # Map rating to expected sentiment
                if review.Score >= 4:
                    metadata['expected_sentiment'] = 'positive'
                elif review.Score <= 2:
                    metadata['expected_sentiment'] = 'negative'
                else:
                    metadata['expected_sentiment'] = 'neutral'
            
            # Store all other fields in metadata
            if review.Id:
                metadata['review_id'] = review.Id
            if review.UserId:
                metadata['user_id'] = review.UserId
            if review.ProfileName:
                metadata['profile_name'] = review.ProfileName
            if review.Summary:
                metadata['summary'] = review.Summary
            if review.HelpfulnessNumerator is not None:
                metadata['helpfulness_numerator'] = review.HelpfulnessNumerator
            if review.HelpfulnessDenominator is not None:
                metadata['helpfulness_denominator'] = review.HelpfulnessDenominator
            
            feedback_items.append({
                'text': text,
                'product': product,
                'timestamp': timestamp,
                'team': None,
                'metadata': metadata if metadata else None
            })
        
        # Process through analyzer
        results = analyzer.analyze_batch(feedback_items, batch_size=128, store_results=True)
        return [SentimentResult(**result) for result in results]
        
    except Exception as e:
        logger.error(f"Error in Amazon format analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/sentiment/timeseries", response_model=List[AggregatedSentimentData])
async def get_sentiment_timeseries(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    group_by: str = "hour",
    team: Optional[str] = None,
    product: Optional[str] = None
):
    """
    Get aggregated sentiment data over time with optional team/product filtering.
    
    Args:
        start_time: Start time in ISO format (default: 24 hours ago)
        end_time: End time in ISO format (default: now)
        group_by: Time grouping - "hour", "day", or "week" (default: "hour")
        team: Filter by team name (optional)
        product: Filter by product name (optional)
        
    Returns:
        List of aggregated sentiment data points
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if group_by not in ["hour", "day", "week"]:
        raise HTTPException(status_code=400, detail="group_by must be 'hour', 'day', or 'week'")
    
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        results = analyzer.get_aggregated_sentiment(start_dt, end_dt, group_by, team, product)
        return [AggregatedSentimentData(**result) for result in results]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting timeseries data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get timeseries data: {str(e)}")


@app.get("/sentiment/statistics", response_model=ServiceStats)
async def get_service_statistics():
    """
    Get overall statistics about the sentiment analysis service.
    
    Returns:
        Service statistics including total analyses, confidence scores, etc.
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        stats = analyzer.get_statistics()
        return ServiceStats(**stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/products")
async def get_products_list(
    limit: int = 100,
    offset: int = 0,
    min_reviews: int = 1
):
    """
    Get list of products with pagination and sentiment statistics.
    
    Args:
        limit: Maximum number of products to return (default: 100)
        offset: Number of products to skip (default: 0)
        min_reviews: Minimum number of reviews per product (default: 1)
        
    Returns:
        Dictionary with products list and pagination info
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")
    
    try:
        result = analyzer.get_products_list(limit=limit, offset=offset, min_reviews=min_reviews)
        return result
    except Exception as e:
        logger.error(f"Error getting products list: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get products list: {str(e)}")


@app.get("/products/{product_id}/timeseries", response_model=List[AggregatedSentimentData])
async def get_product_timeseries(
    product_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    group_by: str = "day"
):
    """
    Get time series data for a specific product.
    
    Args:
        product_id: Product identifier
        start_time: Start time in ISO format (default: 30 days ago)
        end_time: End time in ISO format (default: now)
        group_by: Time grouping - "hour", "day", or "week" (default: "day")
        
    Returns:
        List of aggregated sentiment data points for the product
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if group_by not in ["hour", "day", "week"]:
        raise HTTPException(status_code=400, detail="group_by must be 'hour', 'day', or 'week'")
    
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            # Default to 30 days ago
            start_dt = datetime.now() - timedelta(days=30)
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now()
        
        results = analyzer.get_product_timeseries(
            product_id=product_id,
            start_time=start_dt,
            end_time=end_dt,
            group_by=group_by
        )
        return [AggregatedSentimentData(**result) for result in results]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting product timeseries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get product timeseries: {str(e)}")


@app.get("/products/timeseries/all")
async def get_all_products_timeseries(
    limit: int = 50,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    group_by: str = "day",
    product_ids: Optional[str] = None
):
    """
    Get time series data for multiple products, suitable for UI display.
    
    Args:
        limit: Maximum number of products if product_ids not specified (default: 50)
        start_time: Start time in ISO format (default: 30 days ago)
        end_time: End time in ISO format (default: now)
        group_by: Time grouping - "hour", "day", or "week" (default: "day")
        product_ids: Comma-separated list of product IDs (optional, if not provided uses top products)
        
    Returns:
        Dictionary with time series data organized by product ID
    """
    global analyzer
    
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if group_by not in ["hour", "day", "week"]:
        raise HTTPException(status_code=400, detail="group_by must be 'hour', 'day', or 'week'")
    
    if limit > 200:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 200")
    
    try:
        # Parse product IDs if provided
        product_ids_list = None
        if product_ids:
            product_ids_list = [pid.strip() for pid in product_ids.split(',')]
        
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            # Default to 30 days ago
            start_dt = datetime.now() - timedelta(days=30)
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now()
        
        results = analyzer.get_products_timeseries(
            product_ids=product_ids_list,
            limit=limit,
            start_time=start_dt,
            end_time=end_dt,
            group_by=group_by
        )
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting products timeseries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get products timeseries: {str(e)}")


@app.get("/api/analytics/insights")
async def get_analytics_insights():
    """Get comprehensive analytics insights for the dashboard."""
    try:
        analyzer = get_analyzer()
        
        # Get basic statistics
        stats = analyzer.get_statistics()
        
        # Get top performing products (by positive sentiment ratio)
        products = analyzer.get_products_list(limit=100)
        top_products = []
        attention_products = []
        
        for product in products.get('products', []):
            total_reviews = product['total_reviews']
            if total_reviews >= 3:  # Only consider products with at least 3 reviews
                positive_ratio = product['positive_percentage'] / 100
                negative_ratio = product['negative_percentage'] / 100
                
                if positive_ratio >= 0.7:  # 70% or more positive
                    top_products.append({
                        'product_id': product['product_id'],
                        'positive_ratio': positive_ratio,
                        'total_reviews': total_reviews,
                        'score': positive_ratio * 100
                    })
                
                if negative_ratio >= 0.3:  # 30% or more negative
                    attention_products.append({
                        'product_id': product['product_id'],
                        'negative_ratio': negative_ratio,
                        'total_reviews': total_reviews,
                        'score': negative_ratio * 100
                    })
        
        # Sort by score
        top_products.sort(key=lambda x: x['score'], reverse=True)
        attention_products.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "statistics": stats,
            "top_products": top_products[:5],
            "attention_products": attention_products[:5],
            "insights": {
                "total_products_analyzed": len(products.get('products', [])),
                "high_performing_products": len(top_products),
                "products_needing_attention": len(attention_products)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics insights: {str(e)}")


@app.get("/api/suggestions/generate")
async def generate_suggestions(
    sentiment_filter: Optional[str] = None,
    customer_type_filter: Optional[str] = None,
    product_id: Optional[str] = None
):
    """Generate smart suggestions based on sentiment analysis data."""
    try:
        analyzer = get_analyzer()
        
        # Build query conditions
        conditions = []
        params = []
        
        if sentiment_filter and sentiment_filter != 'all':
            conditions.append("sentiment_label = ?")
            params.append(sentiment_filter)
        
        if customer_type_filter and customer_type_filter != 'all':
            conditions.append("team = ?")  # Assuming team field is used for customer type
            params.append(customer_type_filter)
        
        if product_id:
            conditions.append("product = ?")
            params.append(product_id)
        
        # Get filtered data
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        import sqlite3
        with sqlite3.connect(analyzer.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT sentiment_label, product, team, confidence_score, timestamp, text
                FROM sentiment_results
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT 1000
            """, params)
            
            results = cursor.fetchall()
        
        # Analyze data and generate suggestions
        suggestions = []
        
        if results:
            # Count sentiments
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            product_sentiment = {}
            customer_type_sentiment = {}
            
            for row in results:
                sentiment, product, team, confidence, timestamp, text = row
                
                # Normalize sentiment labels
                sentiment_normalized = sentiment.lower()
                if sentiment_normalized in ['positive', 'joy']:
                    sentiment_key = 'positive'
                elif sentiment_normalized in ['negative', 'sadness', 'disgust']:
                    sentiment_key = 'negative'
                else:
                    sentiment_key = 'neutral'
                
                sentiment_counts[sentiment_key] += 1
                
                # Track by product
                if product not in product_sentiment:
                    product_sentiment[product] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}
                product_sentiment[product][sentiment_key] += 1
                product_sentiment[product]['total'] += 1
                
                # Track by customer type
                if team and team not in customer_type_sentiment:
                    customer_type_sentiment[team] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}
                if team:
                    customer_type_sentiment[team][sentiment_key] += 1
                    customer_type_sentiment[team]['total'] += 1
            
            total_reviews = len(results)
            
            # Generate suggestions based on analysis
            
            # 1. Overall sentiment suggestions
            negative_ratio = sentiment_counts['negative'] / total_reviews
            positive_ratio = sentiment_counts['positive'] / total_reviews
            
            if negative_ratio > 0.4:
                suggestions.append({
                    'category': 'Quality Improvement',
                    'priority': 'high',
                    'title': 'Address Quality Concerns',
                    'description': f'High negative sentiment detected ({negative_ratio:.1%}). Consider reviewing product quality and customer service processes.',
                    'data_points': sentiment_counts['negative'],
                    'action_items': [
                        'Review recent negative feedback for common issues',
                        'Implement quality control measures',
                        'Improve customer service response time'
                    ]
                })
            
            if positive_ratio > 0.7:
                suggestions.append({
                    'category': 'Marketing Opportunity',
                    'priority': 'medium',
                    'title': 'Leverage Positive Feedback',
                    'description': f'High positive sentiment ({positive_ratio:.1%}) presents marketing opportunities.',
                    'data_points': sentiment_counts['positive'],
                    'action_items': [
                        'Feature positive reviews in marketing materials',
                        'Encourage satisfied customers to leave reviews',
                        'Create case studies from positive feedback'
                    ]
                })
            
            # 2. Product-specific suggestions
            for product, data in product_sentiment.items():
                if data['total'] >= 5:  # Only for products with sufficient data
                    negative_ratio = data['negative'] / data['total']
                    positive_ratio = data['positive'] / data['total']
                    
                    if negative_ratio > 0.5:
                        suggestions.append({
                            'category': 'Product Improvement',
                            'priority': 'high',
                            'title': f'Improve {product}',
                            'description': f'{product} shows high negative sentiment ({negative_ratio:.1%}). Immediate attention required.',
                            'data_points': data['negative'],
                            'action_items': [
                                f'Investigate specific issues with {product}',
                                'Consider product redesign or discontinuation',
                                'Implement targeted customer support for this product'
                            ]
                        })
                    elif positive_ratio > 0.8:
                        suggestions.append({
                            'category': 'Success Story',
                            'priority': 'low',
                            'title': f'Promote {product}',
                            'description': f'{product} shows excellent sentiment ({positive_ratio:.1%}). Consider featuring prominently.',
                            'data_points': data['positive'],
                            'action_items': [
                                f'Feature {product} in marketing campaigns',
                                'Analyze what makes this product successful',
                                'Apply learnings to other products'
                            ]
                        })
            
            # 3. Customer type suggestions
            for customer_type, data in customer_type_sentiment.items():
                if data['total'] >= 10:  # Only for customer types with sufficient data
                    negative_ratio = data['negative'] / data['total']
                    
                    if negative_ratio > 0.4:
                        suggestions.append({
                            'category': 'Customer Retention',
                            'priority': 'medium',
                            'title': f'Improve {customer_type} Customer Experience',
                            'description': f'{customer_type} customers show higher negative sentiment ({negative_ratio:.1%}).',
                            'data_points': data['negative'],
                            'action_items': [
                                f'Create targeted support program for {customer_type} customers',
                                'Survey this customer segment for specific pain points',
                                'Develop specialized offerings for this segment'
                            ]
                        })
        
        # Default suggestion if no specific issues found
        if not suggestions:
            suggestions.append({
                'category': 'General',
                'priority': 'low',
                'title': 'Continue Monitoring',
                'description': 'Current sentiment levels are stable. Continue monitoring for trends.',
                'data_points': len(results),
                'action_items': [
                    'Maintain current quality standards',
                    'Regular sentiment analysis reviews',
                    'Proactive customer feedback collection'
                ]
            })
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        suggestions.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return {
            'suggestions': suggestions,
            'analysis_summary': {
                'total_reviews_analyzed': len(results),
                'sentiment_distribution': sentiment_counts,
                'filters_applied': {
                    'sentiment': sentiment_filter,
                    'customer_type': customer_type_filter,
                    'product_id': product_id
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for the main dashboard."""
    try:
        analyzer = get_analyzer()
        
        # Get basic statistics
        stats = analyzer.get_statistics()
        
        # Get recent sentiment trends (last 30 days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        timeseries_data = analyzer.get_aggregated_sentiment(
            start_time=start_time,
            end_time=end_time,
            group_by='day'
        )
        
        # Get product performance
        products = analyzer.get_products_list(limit=20)
        
        return {
            'statistics': stats,
            'recent_trends': timeseries_data,
            'top_products': products,
            'summary': {
                'total_analyzed': stats.get('total_analyses', 0),
                'average_confidence': stats.get('average_confidence', 0),
                'days_of_data': stats.get('days_analyzed', 0),
                'last_updated': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {str(e)}")


@app.get("/api/model-metrics")
async def get_model_metrics():
    """Get model evaluation metrics including confusion matrix and per-class metrics."""
    try:
        analyzer = get_analyzer()
        import sqlite3

        with sqlite3.connect(analyzer.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sentiment_label, confidence_score, text,
                       json_extract(metadata, '$.expected_sentiment') as expected_sentiment,
                       json_extract(metadata, '$.rating') as rating
                FROM sentiment_results
                ORDER BY timestamp DESC
                LIMIT 5000
            """)
            results = cursor.fetchall()

        if not results:
            return {
                "model_info": {
                    "model_name": "j-hartmann/emotion-english-distilroberta-base",
                    "device": analyzer.device,
                    "samples_evaluated": 0
                },
                "confusion_matrix": {},
                "per_class_metrics": {},
                "class_distribution": {"actual": {}, "predicted": {}},
                "confidence_by_class": {},
                "overall_metrics": {"accuracy": 0, "weighted_precision": 0, "weighted_recall": 0, "weighted_f1": 0}
            }

        # Map predicted sentiments to 3-class
        def map_to_3class(sentiment):
            s = sentiment.lower() if sentiment else 'neutral'
            if s in ['joy', 'positive', 'label_2']:
                return 'Positive'
            elif s in ['anger', 'disgust', 'fear', 'sadness', 'negative', 'label_0']:
                return 'Negative'
            return 'Neutral'

        # Map rating to expected sentiment
        def rating_to_sentiment(rating):
            if rating is None:
                return None
            r = float(rating)
            if r >= 4:
                return 'Positive'
            elif r <= 2:
                return 'Negative'
            return 'Neutral'

        classes = ['Positive', 'Negative', 'Neutral']
        confusion = {actual: {predicted: 0 for predicted in classes} for actual in classes}
        class_confidence = {c: [] for c in classes}
        actual_counts = {c: 0 for c in classes}
        predicted_counts = {c: 0 for c in classes}
        correct = 0
        total_with_expected = 0

        for sentiment_label, confidence, text, expected, rating in results:
            predicted = map_to_3class(sentiment_label)
            predicted_counts[predicted] = predicted_counts.get(predicted, 0) + 1
            class_confidence[predicted].append(confidence or 0)

            actual = expected.capitalize() if expected else rating_to_sentiment(rating)
            if actual and actual in classes:
                actual_counts[actual] = actual_counts.get(actual, 0) + 1
                confusion[actual][predicted] += 1
                total_with_expected += 1
                if actual == predicted:
                    correct += 1

        # Per-class precision, recall, F1
        per_class = {}
        for c in classes:
            tp = confusion[c][c]
            fp = sum(confusion[r][c] for r in classes) - tp
            fn = sum(confusion[c][p] for p in classes) - tp
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            support = sum(confusion[c][p] for p in classes)
            per_class[c] = {
                "precision": round(precision * 100, 1),
                "recall": round(recall * 100, 1),
                "f1_score": round(f1 * 100, 1),
                "support": support
            }

        accuracy = correct / total_with_expected if total_with_expected > 0 else 0
        total_support = sum(per_class[c]["support"] for c in classes)
        w_precision = sum(per_class[c]["precision"] * per_class[c]["support"] for c in classes) / total_support if total_support > 0 else 0
        w_recall = sum(per_class[c]["recall"] * per_class[c]["support"] for c in classes) / total_support if total_support > 0 else 0
        w_f1 = sum(per_class[c]["f1_score"] * per_class[c]["support"] for c in classes) / total_support if total_support > 0 else 0

        conf_by_class = {}
        for c in classes:
            vals = class_confidence[c]
            conf_by_class[c] = round(sum(vals) / len(vals), 3) if vals else 0

        return {
            "model_info": {
                "model_name": "j-hartmann/emotion-english-distilroberta-base",
                "device": analyzer.device,
                "samples_evaluated": len(results)
            },
            "confusion_matrix": {actual: {pred: confusion[actual][pred] for pred in classes} for actual in classes},
            "per_class_metrics": per_class,
            "class_distribution": {"actual": actual_counts, "predicted": predicted_counts},
            "confidence_by_class": conf_by_class,
            "overall_metrics": {
                "accuracy": round(accuracy * 100, 1),
                "weighted_precision": round(w_precision, 1),
                "weighted_recall": round(w_recall, 1),
                "weighted_f1": round(w_f1, 1)
            }
        }

    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model metrics: {str(e)}")


@app.get("/api/alerts")
async def get_alerts(
    negative_threshold: float = 40.0,
    spike_window_days: int = 7
):
    """Get proactive alerts based on sentiment analysis data."""
    try:
        analyzer = get_analyzer()
        import sqlite3

        with sqlite3.connect(analyzer.db_path) as conn:
            cursor = conn.cursor()
            # Get product-level sentiment stats
            cursor.execute("""
                SELECT product,
                       COUNT(*) as total,
                       SUM(CASE WHEN sentiment_label IN ('anger','disgust','fear','sadness','negative','label_0') THEN 1 ELSE 0 END) as negative_count,
                       AVG(confidence_score) as avg_confidence,
                       MIN(confidence_score) as min_confidence
                FROM sentiment_results
                WHERE product IS NOT NULL AND product != ''
                GROUP BY product
                HAVING total >= 3
            """)
            product_stats = cursor.fetchall()

            # Get recent spike data
            spike_start = (datetime.now() - timedelta(days=spike_window_days)).isoformat()
            cursor.execute("""
                SELECT product,
                       COUNT(*) as total,
                       SUM(CASE WHEN sentiment_label IN ('anger','disgust','fear','sadness','negative','label_0') THEN 1 ELSE 0 END) as negative_count
                FROM sentiment_results
                WHERE timestamp >= ? AND product IS NOT NULL AND product != ''
                GROUP BY product
                HAVING total >= 2
            """, [spike_start])
            recent_stats = cursor.fetchall()

        alerts = []
        critical_count = 0
        warning_count = 0
        info_count = 0

        for product, total, neg_count, avg_conf, min_conf in product_stats:
            neg_pct = (neg_count / total * 100) if total > 0 else 0

            if neg_pct >= 60:
                alerts.append({
                    "type": "critical",
                    "title": f"High Negative Sentiment: {product}",
                    "description": f"{product} has {neg_pct:.1f}% negative sentiment ({neg_count}/{total} reviews)",
                    "product": product,
                    "timestamp": datetime.now().isoformat(),
                    "metric": neg_pct
                })
                critical_count += 1
            elif neg_pct >= negative_threshold:
                alerts.append({
                    "type": "warning",
                    "title": f"High Negative Sentiment: {product}",
                    "description": f"{product} has {neg_pct:.1f}% negative sentiment ({neg_count}/{total} reviews)",
                    "product": product,
                    "timestamp": datetime.now().isoformat(),
                    "metric": neg_pct
                })
                warning_count += 1

            if min_conf is not None and min_conf < 0.5:
                alerts.append({
                    "type": "info",
                    "title": f"Low Confidence Reviews: {product}",
                    "description": f"{product} has reviews with confidence as low as {min_conf:.1%}. Manual review recommended.",
                    "product": product,
                    "timestamp": datetime.now().isoformat(),
                    "metric": min_conf
                })
                info_count += 1

        # Check for recent spikes
        for product, total, neg_count in recent_stats:
            neg_pct = (neg_count / total * 100) if total > 0 else 0
            if neg_pct >= 70 and total >= 3:
                already_exists = any(a["product"] == product and a["type"] == "critical" for a in alerts)
                if not already_exists:
                    alerts.append({
                        "type": "critical",
                        "title": f"Escalation Spike: {product}",
                        "description": f"{product} has {neg_pct:.1f}% negative sentiment in the last {spike_window_days} days ({neg_count}/{total} reviews)",
                        "product": product,
                        "timestamp": datetime.now().isoformat(),
                        "metric": neg_pct
                    })
                    critical_count += 1

        alerts.sort(key=lambda a: {"critical": 3, "warning": 2, "info": 1}.get(a["type"], 0), reverse=True)

        return {
            "alerts": alerts,
            "summary": {
                "critical": critical_count,
                "warnings": warning_count,
                "info": info_count,
                "total": len(alerts)
            },
            "config": {
                "negative_threshold": negative_threshold,
                "spike_window_days": spike_window_days
            }
        }

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@app.get("/api/business-data")
async def get_business_data():
    """Get business integration data: product releases, escalations, and feature tracking."""
    try:
        analyzer = get_analyzer()
        import sqlite3

        # Get product IDs from database
        with sqlite3.connect(analyzer.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product,
                       COUNT(*) as total,
                       SUM(CASE WHEN sentiment_label IN ('joy','positive','label_2') THEN 1 ELSE 0 END) as positive_count,
                       SUM(CASE WHEN sentiment_label IN ('anger','disgust','fear','sadness','negative','label_0') THEN 1 ELSE 0 END) as negative_count
                FROM sentiment_results
                WHERE product IS NOT NULL AND product != ''
                GROUP BY product
                HAVING total >= 3
                ORDER BY total DESC
                LIMIT 20
            """)
            products = cursor.fetchall()

        # Generate product release dates based on actual products
        release_types = ["MAJOR", "MINOR", "PATCH"]
        release_names = ["v2.1 Refresh", "v3.0 Launch", "Quality Update", "New Formula", "Packaging Redesign",
                         "Performance Fix", "Feature Update", "Bug Fix Release"]
        product_releases = []
        base_date = datetime(2026, 1, 15)
        for i, (product, total, pos, neg) in enumerate(products[:5]):
            release_date = base_date + timedelta(days=i * 20)
            product_releases.append({
                "product": product,
                "release": release_names[i % len(release_names)],
                "date": release_date.strftime("%m/%d/%Y"),
                "type": release_types[i % len(release_types)]
            })

        # Generate escalation tickets based on products with high negative sentiment
        escalation_statuses = ["Open", "In Progress", "Resolved", "Closed"]
        escalation_severities = ["Critical", "High", "Medium", "Low"]
        escalation_teams = ["Support Team", "Product Team", "QA Team", "Engineering"]
        escalation_titles = [
            "Product quality complaints spike",
            "Delivery packaging damage reports",
            "Formula change customer backlash",
            "Pricing complaints from premium segment",
            "Taste/flavor inconsistency reports",
            "Allergic reaction reports",
            "Missing items in orders",
            "Product recall notification needed"
        ]
        escalations = []
        for i, (product, total, pos, neg) in enumerate(products[:6]):
            neg_pct = (neg / total * 100) if total > 0 else 0
            severity_idx = 0 if neg_pct >= 60 else (1 if neg_pct >= 40 else (2 if neg_pct >= 20 else 3))
            escalations.append({
                "ticket": f"ESC-{1001 + i}",
                "title": escalation_titles[i % len(escalation_titles)],
                "product": product,
                "severity": escalation_severities[severity_idx],
                "status": escalation_statuses[i % len(escalation_statuses)],
                "team": escalation_teams[i % len(escalation_teams)]
            })

        # Generate feature feedback tracking
        feature_names = ["New packaging design", "Subscription model", "Bundle offers",
                         "Natural ingredients switch", "Mobile app integration"]
        feature_statuses = ["Planned", "In Development", "Beta", "Released", "GA"]
        features = []
        for i, (product, total, pos, neg) in enumerate(products[:5]):
            sentiment_pct = round((pos / total * 100) if total > 0 else 50)
            features.append({
                "id": f"FEAT-{201 + i}",
                "feature": feature_names[i % len(feature_names)],
                "status": feature_statuses[i % len(feature_statuses)],
                "positive": pos,
                "negative": neg,
                "sentiment": sentiment_pct
            })

        return {
            "product_releases": product_releases,
            "escalations": escalations,
            "features": features,
            "summary": {
                "total_releases": len(product_releases),
                "open_escalations": sum(1 for e in escalations if e["status"] in ["Open", "In Progress"]),
                "features_tracked": len(features)
            }
        }

    except Exception as e:
        logger.error(f"Error getting business data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get business data: {str(e)}")


@app.get("/professional_dashboard.html", response_class=HTMLResponse)
async def get_professional_dashboard():
    """Serve the professional dashboard HTML file."""
    try:
        with open(BASE_DIR / "professional_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Professional dashboard not found")


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_redirect():
    """Redirect to professional dashboard."""
    return await get_professional_dashboard()


@app.get("/debug", response_class=HTMLResponse)
async def get_debug_dashboard():
    """Serve the debug dashboard HTML file."""
    try:
        with open(BASE_DIR / "debug_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Debug dashboard not found")


@app.get("/working_dashboard.html", response_class=HTMLResponse)
async def get_working_dashboard():
    """Serve the working dashboard HTML file."""
    try:
        with open(BASE_DIR / "working_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Working dashboard not found")


@app.get("/fixed_dashboard.html", response_class=HTMLResponse)
async def get_fixed_dashboard():
    """Serve the fixed dashboard HTML file."""
    try:
        with open(BASE_DIR / "fixed_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fixed dashboard not found")


@app.get("/fixed_complete_dashboard.html", response_class=HTMLResponse)
async def get_fixed_complete_dashboard():
    """Serve the fixed complete dashboard HTML file."""
    try:
        with open(BASE_DIR / "fixed_complete_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fixed complete dashboard not found")


@app.get("/test_professional.html", response_class=HTMLResponse)
async def get_test_professional():
    """Serve the test professional dashboard HTML file."""
    try:
        with open(BASE_DIR / "test_professional.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Test professional dashboard not found")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RoBERTa Sentiment Analysis Service",
        "version": "2.0.0",
        "dashboard": "http://localhost:8000/professional_dashboard.html",
        "endpoints": {
            "health": "/health",
            "analyze_single": "/analyze",
            "analyze_batch": "/analyze/batch",
            "timeseries": "/sentiment/timeseries",
            "statistics": "/sentiment/statistics",
            "products_list": "/products",
            "product_timeseries": "/products/{product_id}/timeseries",
            "all_products_timeseries": "/products/timeseries/all",
            "amazon_format": "/analyze/amazon-format",
            "bulk_import": "/analyze/bulk-import",
            "analytics": {
                "insights": "/api/analytics/insights",
                "suggestions": "/api/suggestions/generate",
                "dashboard_summary": "/api/dashboard/summary"
            },
            "visualization": {
                "timeseries_chart": "/api/viz/sentiment-timeseries",
                "dashboard": "/api/viz/sentiment-dashboard",
                "summary": "/api/viz/sentiment-summary"
            },
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
