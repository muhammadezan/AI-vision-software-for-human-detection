#!/usr/bin/env python3
"""Improve cursor control and error handling."""

# Read dashboard.js
with open(r'd:\New folder (2)\assistive_hands\ui\static\js\dashboard.js', 'r') as f:
    content = f.read()

# Improve moveSystemCursor with better error handling
improved_cursor_fn = '''
// Move system cursor based on gaze
let cursorMoveInterval = null;
let lastCursorMoveTime = 0;

function moveSystemCursor(x, y) {
    // Store latest gaze position
    window.lastGazeX = x;
    window.lastGazeY = y;
    
    // Throttle cursor updates to avoid excessive API calls
    const now = Date.now();
    if (now - lastCursorMoveTime < 50) {
        // Skip if updated within last 50ms
        return;
    }
    lastCursorMoveTime = now;
    
    // Send cursor move request to backend
    api.post('/api/cursor/move', { x: Math.round(x), y: Math.round(y) })
        .then(response => {
            if (!response.cursor_enabled) {
                console.warn('Cursor control not enabled on backend (may require admin privileges on Windows)');
            }
        })
        .catch(err => {
            console.debug('Cursor move error:', err.message);
        });
}
'''

# Replace the old moveSystemCursor function
if 'function moveSystemCursor' in content:
    # Find and replace the function
    start = content.find('// Move system cursor based on gaze')
    if start > 0:
        # Find the end of the function (next function or cleanup section)
        end = content.find('// Cleanup on page unload', start)
        if end > 0:
            # Replace the section
            content = content[:start] + improved_cursor_fn + '\n' + content[end:]

# Ensure dashboard loads camera before calling gaze updates
dashboard_init = '''document.addEventListener('DOMContentLoaded', async () => {
    console.log('Dashboard loaded');
    
    try {
        // Start camera FIRST
        console.log('Starting camera...');
        const cameraStartResponse = await api.post('/api/camera/start');
        console.log('Camera start response:', cameraStartResponse);
        
        if (cameraStartResponse.status === 'success') {
            showToast('Camera started', 'success');
            
            // Refresh camera feed image
            const cameraFeed = document.getElementById('cameraFeed');
            if (cameraFeed) {
                cameraFeed.src = `/api/camera/feed?ts=${Date.now()}`;
            }
        }

        // Initialize gaze updates
        startGazeUpdates();
        
        // Initialize session duration tracker
        startSessionTracker();

        // Setup event listeners
        setupButtonListeners();
        
        // Load system status
        updateSystemStatus();

    } catch (error) {
        console.error('Dashboard initialization error:', error);
        showToast('Error initializing dashboard: ' + error.message, 'danger');
    }
});'''

# Replace the DOMContentLoaded handler
dom_content_start = content.find("document.addEventListener('DOMContentLoaded'")
if dom_content_start > 0:
    dom_content_end = content.find("});", dom_content_start) + 3
    content = content[:dom_content_start] + dashboard_init + content[dom_content_end:]

# Write back
with open(r'd:\New folder (2)\assistive_hands\ui\static\js\dashboard.js', 'w') as f:
    f.write(content)

print("Successfully improved cursor control and error handling in dashboard.js")
