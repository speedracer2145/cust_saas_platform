"""
Visualization API for Sentiment Analysis Service

This module provides API endpoints for visualizing sentiment data with time series plots
and filtering capabilities by team and product.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd

from .sentiment_analyzer import get_analyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/viz", tags=["visualization"])

@router.get("/sentiment-timeseries")
async def get_sentiment_timeseries(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    product: Optional[str] = Query(None, description="Filter by product name"),
    group_by: str = Query("hour", description="Time grouping: hour, day, week"),
    chart_type: str = Query("line", description="Chart type: line, bar, area")
):
    """
    Get sentiment time series data with filtering options.
    
    Returns:
        JSON data for plotting sentiment trends over time
    """
    try:
        analyzer = get_analyzer()
        
        # Parse dates
        start_time = None
        end_time = None
        
        if start_date:
            start_time = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_time = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get aggregated data
        data = analyzer.get_aggregated_sentiment(
            start_time=start_time,
            end_time=end_time,
            group_by=group_by,
            team=team,
            product=product
        )
        
        if not data:
            return {
                "message": "No data found for the specified filters",
                "data": [],
                "chart_config": {}
            }
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)
        
        # Create time series chart
        fig = create_timeseries_chart(df, chart_type, group_by)
        
        # Convert to JSON
        chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        
        return {
            "message": "Time series data retrieved successfully",
            "data": data,
            "chart_config": json.loads(chart_json),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "team": team,
                "product": product,
                "group_by": group_by,
                "chart_type": chart_type
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment timeseries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment-dashboard")
async def get_sentiment_dashboard(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    product: Optional[str] = Query(None, description="Filter by product name")
):
    """
    Get comprehensive sentiment dashboard with multiple visualizations.
    
    Returns:
        HTML dashboard with multiple charts
    """
    try:
        analyzer = get_analyzer()
        
        # Parse dates
        start_time = None
        end_time = None
        
        if start_date:
            start_time = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_time = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get data for different time groupings
        hourly_data = analyzer.get_aggregated_sentiment(
            start_time=start_time,
            end_time=end_time,
            group_by="hour",
            team=team,
            product=product
        )
        
        daily_data = analyzer.get_aggregated_sentiment(
            start_time=start_time,
            end_time=end_time,
            group_by="day",
            team=team,
            product=product
        )
        
        # Get overall statistics
        stats = analyzer.get_statistics()
        
        # Create dashboard HTML
        dashboard_html = create_dashboard_html(
            hourly_data, daily_data, stats, 
            start_date, end_date, team, product
        )
        
        return HTMLResponse(content=dashboard_html)
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment-summary")
async def get_sentiment_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    product: Optional[str] = Query(None, description="Filter by product name")
):
    """
    Get sentiment summary statistics.
    
    Returns:
        Summary statistics for sentiment data
    """
    try:
        analyzer = get_analyzer()
        
        # Parse dates
        start_time = None
        end_time = None
        
        if start_date:
            start_time = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_time = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get aggregated data
        data = analyzer.get_aggregated_sentiment(
            start_time=start_time,
            end_time=end_time,
            group_by="day",
            team=team,
            product=product
        )
        
        if not data:
            return {
                "message": "No data found for the specified filters",
                "summary": {}
            }
        
        # Calculate summary statistics
        df = pd.DataFrame(data)
        
        total_feedback = df['total'].sum()
        positive_count = df['positive'].sum()
        negative_count = df['negative'].sum()
        neutral_count = df['neutral'].sum()
        
        positive_percentage = (positive_count / total_feedback * 100) if total_feedback > 0 else 0
        negative_percentage = (negative_count / total_feedback * 100) if total_feedback > 0 else 0
        neutral_percentage = (neutral_count / total_feedback * 100) if total_feedback > 0 else 0
        
        avg_confidence = df['avg_confidence'].mean()
        
        return {
            "message": "Summary statistics retrieved successfully",
            "summary": {
                "total_feedback": int(total_feedback),
                "positive_count": int(positive_count),
                "negative_count": int(negative_count),
                "neutral_count": int(neutral_count),
                "positive_percentage": round(positive_percentage, 2),
                "negative_percentage": round(negative_percentage, 2),
                "neutral_percentage": round(neutral_percentage, 2),
                "average_confidence": round(avg_confidence, 3),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "filters": {
                    "team": team,
                    "product": product
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_timeseries_chart(df: pd.DataFrame, chart_type: str, group_by: str) -> go.Figure:
    """Create time series chart from DataFrame."""
    
    # Convert time column to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    if chart_type == "line":
        fig = go.Figure()
        
        # Add traces for each sentiment
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['positive'],
            mode='lines+markers',
            name='Positive',
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['negative'],
            mode='lines+markers',
            name='Negative',
            line=dict(color='red', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['neutral'],
            mode='lines+markers',
            name='Neutral',
            line=dict(color='blue', width=2)
        ))
        
    elif chart_type == "bar":
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['time'], y=df['positive'],
            name='Positive',
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            x=df['time'], y=df['negative'],
            name='Negative',
            marker_color='red'
        ))
        
        fig.add_trace(go.Bar(
            x=df['time'], y=df['neutral'],
            name='Neutral',
            marker_color='blue'
        ))
        
    elif chart_type == "area":
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['positive'],
            mode='lines',
            fill='tonexty',
            name='Positive',
            line=dict(color='green')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['negative'],
            mode='lines',
            fill='tonexty',
            name='Negative',
            line=dict(color='red')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['neutral'],
            mode='lines',
            fill='tozeroy',
            name='Neutral',
            line=dict(color='blue')
        ))
    
    # Update layout
    fig.update_layout(
        title=f'Sentiment Analysis Over Time (Grouped by {group_by})',
        xaxis_title='Time',
        yaxis_title='Number of Feedback',
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_dashboard_html(hourly_data: List[Dict], daily_data: List[Dict], 
                         stats: Dict, start_date: str, end_date: str, 
                         team: str, product: str) -> str:
    """Create HTML dashboard with multiple charts."""
    
    # Create charts
    hourly_fig = create_timeseries_chart(pd.DataFrame(hourly_data), "line", "hour")
    daily_fig = create_timeseries_chart(pd.DataFrame(daily_data), "bar", "day")
    
    # Convert to HTML
    hourly_html = hourly_fig.to_html(include_plotlyjs='cdn', div_id="hourly-chart")
    daily_html = daily_fig.to_html(include_plotlyjs=False, div_id="daily-chart")
    
    # Create dashboard HTML
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sentiment Analysis Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .chart-container {{ margin: 20px 0; }}
            .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .stat-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
            .filters {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Sentiment Analysis Dashboard</h1>
            <p>Real-time sentiment analysis visualization</p>
        </div>
        
        <div class="filters">
            <h3>Active Filters:</h3>
            <p><strong>Date Range:</strong> {start_date or 'All time'} to {end_date or 'Now'}</p>
            <p><strong>Team:</strong> {team or 'All teams'}</p>
            <p><strong>Product:</strong> {product or 'All products'}</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>{stats.get('total_analyses', 0)}</h3>
                <p>Total Analyses</p>
            </div>
            <div class="stat-box">
                <h3>{stats.get('days_analyzed', 0)}</h3>
                <p>Days Analyzed</p>
            </div>
            <div class="stat-box">
                <h3>{stats.get('average_confidence', 0):.3f}</h3>
                <p>Avg Confidence</p>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Hourly Sentiment Trends</h2>
            {hourly_html}
        </div>
        
        <div class="chart-container">
            <h2>Daily Sentiment Trends</h2>
            {daily_html}
        </div>
        
        <div class="chart-container">
            <h2>Sentiment Distribution</h2>
            <div id="distribution-chart"></div>
        </div>
        
        <script>
            // Create sentiment distribution pie chart
            var distributionData = {json.dumps(stats.get('sentiment_distribution', {}))};
            var pieData = Object.entries(distributionData).map(([label, value]) => ({{
                labels: label,
                values: value
            }}));
            
            var pieLayout = {{
                title: "Overall Sentiment Distribution",
                height: 400
            }};
            
            Plotly.newPlot('distribution-chart', pieData, pieLayout);
        </script>
    </body>
    </html>
    """
    
    return dashboard_html
