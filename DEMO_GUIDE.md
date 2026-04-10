# Demo Presentation Guide - UI-Based Demo

This guide shows you how to demonstrate all features using the web UI.

## Files You Need

1. **bulk_import_ui.html** - Main UI for bulk import and product analysis
2. **dashboard.html** - Dashboard for timeseries visualization
3. **demo_sample_data.json** - Sample data for bulk import demo

## Step-by-Step Demo Flow

### Part 1: Bulk Import & Product Analysis (bulk_import_ui.html)

#### 1. Open the UI
- Open `bulk_import_ui.html` in your browser
- Point to: `file:///C:/Users/svijapur/OneDrive/IdeaProjects/roberta-sentiment-service/bulk_import_ui.html`
- **Show**: Service status indicator (should be green if server is running)

#### 2. Upload Sample Data
- Drag and drop `demo_sample_data.json` into the upload area
- Or click to browse and select the file
- **Show**: File validation, file info display
- **Mention**: "The UI validates the JSON format and shows file details"

#### 3. Process Reviews
- Click "Process Reviews" button
- **Show**: Loading indicator
- **Mention**: "The system is now processing reviews through RoBERTa sentiment analysis model"

#### 4. Results Summary
**Show these features:**
- **Total Reviews**: Total number processed
- **Processed**: Successfully analyzed count
- **Products**: Number of unique products found
- **Processing Time**: Performance metric
- **Mention**: "Batch processing with configurable batch sizes for efficiency"

#### 5. Product Analysis Cards
For each product, **show and explain**:

**Statistics:**
- Total Reviews count
- Positive count and percentage
- Negative count and percentage  
- Neutral count and percentage
- Average Confidence score
- **Mention**: "Multi-dimensional sentiment analysis with confidence scores"

**Keywords Section:**
- Positive Keywords (green tags)
- Negative Keywords (red tags)
- Neutral Keywords (blue tags)
- **Mention**: "KeyBERT-based keyword extraction using BERT embeddings for semantic relevance"

**Top Comments:**
- Top Positive Comments (with ranking scores)
- Top Negative Comments (with ranking scores)
- Top Neutral Comments (with ranking scores)
- **Mention**: "Intelligent ranking based on confidence, helpfulness, recency, and text length"

#### 6. Product Comparison
- Select two products from dropdowns
- Click "Compare Products"
- **Show**:
  - Side-by-side product comparison
  - Comparison metrics:
    - Better product identification
    - Positive/Negative percentage differences
    - Confidence difference
    - Total reviews difference
    - Common keywords (positive/negative)
    - Unique keywords per product
- **Mention**: "Advanced product comparison for competitive analysis"

#### 7. Raw JSON Response
- Scroll to bottom
- **Show**: Complete JSON response
- **Mention**: "Full API response available for integration with other systems"

### Part 2: Dashboard & Timeseries (dashboard.html)

#### 1. Open Dashboard
- Open `dashboard.html` in browser
- **Show**: Interactive dashboard interface

#### 2. Timeseries Visualization
**Show and explain:**
- Time-based sentiment trends
- Filtering by:
  - Date range (start/end dates)
  - Team name
  - Product name
  - Time grouping (hour/day/week)
- Chart types (line/bar/area)
- **Mention**: "SQLite database with optimized indexes for fast time-series queries"

#### 3. Aggregated Data
- **Show**: Aggregated sentiment counts over time
- **Mention**: "Efficient SQL aggregation with GROUP BY and date functions"

### Part 3: API Documentation (Optional)

#### 1. Open API Docs
- Navigate to: `http://localhost:8000/docs`
- **Show**: Interactive Swagger UI
- **Mention**: "Auto-generated API documentation with try-it-out functionality"

## Key Features to Highlight

### 1. **Sentiment Analysis**
- RoBERTa model for accurate sentiment classification
- Three-class classification (Positive/Negative/Neutral)
- Confidence scores for each prediction

### 2. **Batch Processing**
- Efficient batch processing (128 items per batch)
- GPU acceleration support
- Optimized inference with torch.no_grad()

### 3. **Product Grouping**
- Automatic grouping by product ID
- Per-product sentiment statistics
- Percentage calculations

### 4. **Top Comments Ranking**
- Multi-factor ranking algorithm:
  - Confidence score
  - Helpfulness ratio
  - Recency
  - Text length
- Configurable number of top comments

### 5. **Keyword Extraction**
- KeyBERT for semantic keyword extraction
- BERT embeddings for relevance
- N-gram extraction (1-2 words)
- Maximal Marginal Relevance for diversity

### 6. **Product Comparison**
- Side-by-side comparison
- Difference metrics
- Common and unique keywords
- Better product identification

### 7. **Database Storage**
- SQLite database with optimized indexes
- Persistent storage of all results
- Fast query performance

### 8. **Timeseries Aggregation**
- Time-based grouping (hour/day/week)
- Multi-dimensional filtering (team/product/time)
- SQL aggregation for performance

### 9. **REST API**
- Clean RESTful endpoints
- JSON request/response format
- Error handling
- CORS support

### 10. **UI Features**
- Drag-and-drop file upload
- Real-time status indicators
- Interactive visualizations
- Responsive design

## Sample Talking Points

1. **Introduction**: "This is a production-ready sentiment analysis service built with RoBERTa, a state-of-the-art transformer model."

2. **Bulk Import**: "The bulk import feature processes Amazon-format reviews, groups them by product, and provides comprehensive sentiment analysis."

3. **Keyword Extraction**: "We use KeyBERT, which leverages BERT embeddings to extract semantically relevant keywords, not just frequent words."

4. **Top Comments**: "Our ranking algorithm considers multiple factors to surface the most valuable feedback for product managers."

5. **Performance**: "The system is optimized for both CPU and GPU, with batch processing and database indexing for scalability."

6. **Integration**: "The REST API makes it easy to integrate with existing systems, and the UI provides a user-friendly interface for non-technical users."

## Troubleshooting During Demo

- **If service is offline**: Show the red status indicator and explain it checks service health
- **If processing is slow**: Mention that first-time model loading takes time, subsequent requests are faster
- **If no data**: Use the sample data file provided

## Files Location

- UI Files: Root directory
- Sample Data: `demo_sample_data.json`
- Service: Must be running on `http://localhost:8000`

