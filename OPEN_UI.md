# How to Open and Use the UI

## Step 1: Start the Service

Make sure the service is running:
```powershell
.\run_service.ps1
```

Wait until you see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Open the UI

### Option A: Direct File Open (Easiest)
1. Open File Explorer
2. Navigate to: `C:\Users\svijapur\OneDrive\IdeaProjects\roberta-sentiment-service`
3. Double-click on `bulk_import_ui.html`
4. It will open in your default browser

### Option B: From Browser
1. Open your browser (Chrome, Edge, Firefox, etc.)
2. Press `Ctrl + O` (or File → Open)
3. Navigate to: `C:\Users\svijapur\OneDrive\IdeaProjects\roberta-sentiment-service`
4. Select `bulk_import_ui.html`
5. Click Open

### Option C: Drag and Drop
1. Open File Explorer
2. Navigate to the project folder
3. Drag `bulk_import_ui.html` into an open browser window

### Option D: Using File Path
1. Open your browser
2. In the address bar, type:
   ```
   file:///C:/Users/svijapur/OneDrive/IdeaProjects/roberta-sentiment-service/bulk_import_ui.html
   ```
3. Press Enter

## Step 3: Verify Service Connection

When the UI opens, check the top of the page:
- **Green indicator** = Service is online ✅
- **Red indicator** = Service is offline ❌

If it's red:
- Make sure the service is running
- Check that it's on port 8000
- Wait a few seconds and refresh the page

## Step 4: Use the UI

1. **Upload Data**: Drag and drop `demo_sample_data.json` or click to browse
2. **Process**: Click "Process Reviews" button
3. **View Results**: See product analysis, keywords, top comments
4. **Compare Products**: Select two products and click "Compare Products"

## Alternative UIs

### Dashboard UI
- Open `dashboard.html` in the same way
- Shows timeseries visualizations
- Filter by date, team, product

### API Documentation
- Open in browser: `http://localhost:8000/docs`
- Interactive API testing interface

## Troubleshooting

**UI shows "Service is offline":**
- Check if service is running: Look for "Application startup complete" in terminal
- Check port: Service should be on `http://localhost:8000`
- Try refreshing the page (F5)

**CORS errors:**
- The service has CORS enabled, so this shouldn't happen
- If it does, make sure you're opening the HTML file directly (file://) not through a web server

**File upload not working:**
- Make sure you're using `demo_sample_data.json` or a valid JSON file
- Check browser console (F12) for errors

