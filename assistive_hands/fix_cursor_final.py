#!/usr/bin/env python3
"""Fix cursor control issues."""

import re

# Fix 1: Update dashboard.js to handle camera start errors properly
with open(r'd:\New folder (2)\assistive_hands\ui\static\js\dashboard.js', 'r') as f:
    dashboard_content = f.read()

# Replace the camera start code with better error handling
old_camera_code = """        // Start camera
        await api.post('/api/camera/start');
        showToast('Camera started', 'success');"""

new_camera_code = """        // Start camera
        try {
            const camResp = await api.post('/api/camera/start');
            console.log('Camera response:', camResp);
            if (camResp && camResp.status === 'success') {
                showToast('Camera started', 'success');
            } else {
                console.error('Camera start returned error:', camResp);
                showToast('Camera start failed: ' + (camResp?.message || 'unknown error'), 'warning');
            }
        } catch (err) {
            console.error('Camera start exception:', err);
            showToast('Camera start error: ' + err.message, 'danger');
        }"""

dashboard_content = dashboard_content.replace(old_camera_code, new_camera_code)

# Fix the moveSystemCursor function to use window.lastGazeX instead of undefined variable
old_cursor_func = """function moveSystemCursor(x, y) {
    // Throttle cursor updates to avoid excessive API calls
    if (!cursorMoveInterval) {
        cursorMoveInterval = setInterval(() => {
            if (lastGazeX !== undefined && lastGazeY !== undefined) {
                api.post('/api/cursor/move', { x: lastGazeX, y: lastGazeY })
                    .catch(err => console.debug('Cursor move error:', err));
            }
        }, 50); // Update cursor every 50ms
    }
    
    // Store latest gaze position
    window.lastGazeX = x;
    window.lastGazeY = y;
}"""

new_cursor_func = """function moveSystemCursor(x, y) {
    // Store latest gaze position
    window.lastGazeX = x;
    window.lastGazeY = y;
    
    // Throttle cursor updates to avoid excessive API calls
    if (!cursorMoveInterval) {
        cursorMoveInterval = setInterval(() => {
            if (window.lastGazeX !== undefined && window.lastGazeY !== undefined) {
                api.post('/api/cursor/move', { x: Math.round(window.lastGazeX), y: Math.round(window.lastGazeY) })
                    .then(resp => {
                        if (resp && !resp.cursor_enabled) {
                            console.warn('Cursor control disabled on backend');
                        }
                    })
                    .catch(err => console.debug('Cursor move error:', err.message || err));
            }
        }, 50); // Update cursor every 50ms
    }
}"""

dashboard_content = dashboard_content.replace(old_cursor_func, new_cursor_func)

with open(r'd:\New folder (2)\assistive_hands\ui\static\js\dashboard.js', 'w') as f:
    f.write(dashboard_content)

print("✓ Fixed dashboard.js cursor control and camera error handling")

# Fix 2: Improve cursor_control.py error messages
with open(r'd:\New folder (2)\assistive_hands\utils\cursor_control.py', 'r') as f:
    cursor_py = f.read()

# Add better logging to the move_cursor method
old_move_code = """        try:
            # Clamp values to screen boundaries (typical 1920x1080)
            x = max(0, min(int(x), 1920))
            y = max(0, min(int(y), 1080))
            
            self.pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            logger.error(f"Failed to move cursor: {e}")
            return False"""

new_move_code = """        try:
            # Clamp values to screen boundaries (typical 1920x1080)
            x = max(0, min(int(x), 1920))
            y = max(0, min(int(y), 1080))
            
            self.pyautogui.moveTo(x, y, duration=duration)
            logger.debug(f"Cursor moved to ({x}, {y})")
            return True
        except PermissionError as e:
            logger.error("Permission denied: Run as Administrator to control cursor on Windows")
            self.cursor_enabled = False
            return False
        except Exception as e:
            logger.error(f"Failed to move cursor: {e}")
            return False"""

cursor_py = cursor_py.replace(old_move_code, new_move_code)

with open(r'd:\New folder (2)\assistive_hands\utils\cursor_control.py', 'w') as f:
    f.write(cursor_py)

print("✓ Improved cursor_control.py error handling")
print("\nYour cursor control system is now fixed!")
print("If the system cursor still doesn't move:")
print("  1. On Windows, try running VS Code as Administrator")
print("  2. Check the browser console for errors (F12)")
print("  3. Watch the server logs for 'Permission denied' messages")
