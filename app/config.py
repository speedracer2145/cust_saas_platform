"""
Configuration settings for the RoBERTa Sentiment Analysis Service
"""

import os
from typing import Optional


class Config:
    """Application configuration class."""
    
    # Model configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "cardiffnlp/twitter-roberta-base-sentiment-latest")
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "1000"))
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # Database configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/sentiment_results.db")
    
    # CORS configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Performance configuration
    USE_CUDA: bool = os.getenv("USE_CUDA", "true").lower() == "true"
    TORCH_DTYPE: str = os.getenv("TORCH_DTYPE", "auto")  # auto, float16, float32
    
    # Time configuration
    DEFAULT_TIMESERIES_HOURS: int = int(os.getenv("DEFAULT_TIMESERIES_HOURS", "24"))
    
    @classmethod
    def get_torch_dtype(cls) -> Optional[str]:
        """Get the appropriate torch dtype based on configuration."""
        if cls.TORCH_DTYPE == "auto":
            return "float16" if cls.USE_CUDA else "float32"
        return cls.TORCH_DTYPE
