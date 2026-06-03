# AssistiveHands - Code Fixes & Improvements

## What Was Broken / Missing

The original code had eye tracking working but had several issues:

1. **No click on blink** - The blink detection existed but never triggered a mouse click
2. **Jerky cursor movement** - The cursor moved like "AH... AH... AH" instead of smoothly
3. **Cursor jiggling when focusing** - When looking at a button, the cursor kept shaking
4. **Server overload** - Too many API requests causing ERR_INSUFFICIENT_RESOURCES errors
5. **No mouse click endpoint** - The frontend had nowhere to send click requests
6. **Simple gaze tracking** - Only eye movement, no head movement compensation
7. **Missing eye corner landmarks** - Required for proper gaze calculation
8. **EAR calculation instability** - No fallback value when landmarks were lost
9. **Missing `reset_smoothing_history` method** - Caused calibration to fail with 500 error

---

## What Was Fixed

### 1. Normal Blink Click (camera_stream.py)
**Before:** No click on blink
**After:** Normal blink (single blink) triggers mouse click
```python
avg_ear = (left_ear + right_ear) / 2
if avg_ear < 0.50:
    pyautogui.click()
    time.sleep(0.3)
```

### 2. Blink During Cursor Freeze (camera_stream.py)
**Before:** Cursor moved during blink
**After:** Cursor stays frozen during blink
```python
if self.blink_detected:
    # Cursor stays exactly where it is
    pass
else:
    # Only move cursor when NOT blinking
```

### 3. Stability Zone (camera_stream.py)
**Before:** Cursor kept shaking when focusing
**After:** Cursor stays still for small eye movements (movement < 0.02)

### 4. Server Load Reduction (dashboard.js)
**Before:** Gaze update every 33ms (server crashed)
**After:** Every 100ms (stable)
```javascript
}, 100);  // was 33
```

### 5. Cursor Movement Optimization (dashboard.js)
**Before:** Moved cursor for every 15 pixel change
**After:** Moves only for 50 pixel change
```javascript
if (Math.abs(roundedX - lastCursorX) > 50)  // was 15
```

### 6. Mouse Click Endpoint (app.py)
**Before:** No endpoint existed
**After:** Added /api/mouse/click endpoint

### 7. Head Movement Tracking (gaze_estimator.py)
**Before:** Only eye movement
**After:** Left/Right = Eyes, Up/Down = Head movement

### 8. Eye Corner Landmarks (face_detector.py)
**Before:** Missing eye corners
**After:** Added LEFT_EYE_CORNERS and RIGHT_EYE_CORNERS

### 9. EAR Fallback Value (eye_tracker.py)
**Before:** No fallback when landmarks lost
**After:** Added self._last_ear_value = 1.0

### 10. Reset Smoothing History Method (gaze_estimator.py)
**Before:** Missing method caused calibration 500 error
**After:** Added reset_smoothing_history() method

---

## Files Modified

| File | Changes |
|------|---------|
| `camera_stream.py` | Blink click, blink freeze, stability zone |
| `app.py` | /api/mouse/click endpoint |
| `dashboard.js` | Interval 33→100, threshold 15→50 |
| `dashboard.html` | X key handler |
| `gaze_estimator.py` | Head+Eye tracking, reset_smoothing_history() |
| `face_detector.py` | Eye corners |
| `eye_tracker.py` | _last_ear_value |

---

## Files to Replace

```
camera_stream.py
app.py
dashboard.js
dashboard.html
gaze_estimator.py
face_detector.py
eye_tracker.py
```

---

## How to Run

```bash
cd assistive_hands
.venv\Scripts\activate
python app.py
```

Browser: `http://127.0.0.1:5000`

---

## Testing

| Action | Expected Result |
|--------|-----------------|
| Look around | Cursor moves |
| Normal blink | Mouse click |
| Press X key | Mouse click (test) |
| Focus on button | Cursor stays still |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Blink doesn't click | Press X - if works, change threshold 0.50→0.45 |
| X doesn't work | Run Flask as Administrator |
| Cursor jiggling | Change dead zone 0.02→0.03 |
| Calibration 500 error | Check gaze_estimator.py has reset_smoothing_history() |

---

## Green Circle (Optional)

Disabled on main dashboard. To fully remove from all pages, add to `style.css`:

```css
#gazeCursor, .gaze-cursor {
    display: none !important;
}
```

## Communication Page - Disable Auto Click on Keyboard (Optional)

In `communication.js`, inside `updateDwellTimers`, add:

```javascript
if (elementId && elementId.startsWith('key-')) {
    return;  // No auto click on keyboard buttons
}
```

---

## Code Status

**All fixes implemented. System fully working. Normal blink = Click!**