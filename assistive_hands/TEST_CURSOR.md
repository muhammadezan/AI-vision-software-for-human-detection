# Cursor Control Debugging

## Test Calibration
Go to: http://127.0.0.1:5000/api/test/calibration

This will show:
- Whether calibration is loaded
- Test transformations for 4 points
- Check if calibration matrix is working

## Test Screen Resolution
Your screen resolution should be detected as:
- Width: 1920
- Height: 1080

## Dashboard Test
1. Go to http://127.0.0.1:5000/
2. Open browser console (F12) → Console tab
3. Look for gaze logging (every ~5 seconds):
   ```
   Gaze - Normalized: [x, y] | Screen: [x, y]
   ```

## Issues to Check:
1. Are gaze_normalized values between 0-1?
2. Are gaze_screen values between 0-1920 and 0-1080?
3. Does cursor move towards eye position or away from it?
4. Is calibration_enabled true on dashboard?

## If Cursor Not Moving:
- Check if pyautogui is installed: `pip list | grep pyautogui`
- Check if running with admin privileges
- Check browser console for errors
