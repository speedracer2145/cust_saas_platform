// Debug script to test dashboard functionality
async function debugDashboard() {
    const API_BASE = 'http://localhost:8000';
    
    console.log('=== Dashboard Debug ===');
    
    // Test statistics API
    try {
        const statsResponse = await fetch(`${API_BASE}/sentiment/statistics`);
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            console.log('✅ Statistics API Response:', stats);
            
            const distribution = stats.sentiment_distribution || {};
            console.log('📊 Distribution:', distribution);
            
            const processedStats = {
                positive: (distribution.positive || 0) + (distribution.POSITIVE || 0) + (distribution.joy || 0),
                negative: (distribution.negative || 0) + (distribution.NEGATIVE || 0) + (distribution.sadness || 0) + (distribution.disgust || 0),
                neutral: (distribution.neutral || 0) + (distribution.surprise || 0),
                total: stats.total_analyses || 0,
                emotions: distribution
            };
            
            console.log('🔄 Processed Stats:', processedStats);
            
            // Try to update UI elements if they exist
            const elements = {
                'positive-count': processedStats.positive,
                'negative-count': processedStats.negative,
                'neutral-count': processedStats.neutral,
                'total-count': processedStats.total
            };
            
            console.log('🎯 Updating UI elements:');
            for (const [id, value] of Object.entries(elements)) {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = value.toLocaleString();
                    console.log(`  ✅ Updated ${id}: ${value}`);
                } else {
                    console.log(`  ❌ Element not found: ${id}`);
                }
            }
        } else {
            console.error('❌ Statistics API failed:', statsResponse.status);
        }
    } catch (error) {
        console.error('❌ Error fetching statistics:', error);
    }
    
    // Test timeseries API
    try {
        const endTime = new Date().toISOString();
        const startTime = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
        const timeseriesResponse = await fetch(`${API_BASE}/sentiment/timeseries?group_by=day&limit=30&start_time=${startTime}&end_time=${endTime}`);
        
        if (timeseriesResponse.ok) {
            const timeseriesData = await timeseriesResponse.json();
            console.log('✅ Timeseries API Response:', timeseriesData.length, 'data points');
            console.log('📅 Sample data:', timeseriesData.slice(0, 3));
        } else {
            console.error('❌ Timeseries API failed:', timeseriesResponse.status);
        }
    } catch (error) {
        console.error('❌ Error fetching timeseries:', error);
    }
}

// Run debug when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', debugDashboard);
} else {
    debugDashboard();
}