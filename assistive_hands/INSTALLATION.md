# AssistiveHands - Installation & Troubleshooting

## Complete Installation Guide

### System Requirements

**Hardware:**
- Processor: Dual-core 2GHz or higher
- RAM: 4GB minimum (8GB recommended)
- Webcam: USB webcam with 640x480+ resolution
- Display: 1920x1080 recommended

**Software:**
- Python 3.11.2 or higher
- pip package manager
- Modern web browser

### Step-by-Step Installation

#### 1. Verify Python Installation

```bash
python --version
# Should show: Python 3.11.2 or higher
```

If not installed, download from [python.org](https://www.python.org)

#### 2. Create Project Directory

```bash
mkdir assistive_hands
cd assistive_hands
```

#### 3. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Installation time:** 5-10 minutes depending on internet speed

#### 5. Verify Installation

```bash
python -c "import cv2, mediapipe, flask; print('✓ All dependencies installed')"
```

#### 6. Run Application

```bash
python app.py
```

#### 7. Access Web Interface

Open browser: `http://127.0.0.1:5000`

## Configuration After Installation

### Camera Setup

1. Allow camera permissions in OS settings
2. Test camera access: Navigate to Dashboard
3. Verify camera feed appears
4. Position webcam for optimal view

### Initial Calibration

1. Go to Calibration page
2. Position face clearly in frame
3. Follow on-screen instructions
4. Complete 9-point calibration
5. Check accuracy (target: <2px error)

### Network Setup (Optional)

To access from another device:

Edit `app.py`:
```python
app.run(
    host='0.0.0.0',  # Changed from '127.0.0.1'
    port=5000,
    debug=False
)
```

Then access from another machine:
```
http://<your-ip>:5000
```

## Troubleshooting

### Installation Issues

#### Issue: Python not found
```bash
# Windows: Add Python to PATH
# macOS/Linux: Use python3 instead of python
python3 --version
```

#### Issue: pip command not found
```bash
python -m pip install --upgrade pip
```

#### Issue: Virtual environment activation fails
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
# Then activate it
```

#### Issue: Dependency installation fails
```bash
# Try installing packages individually
pip install flask==3.0.0
pip install opencv-python==4.8.1.78
# etc...
```

### Runtime Issues

#### Camera Not Detected
**Symptoms:** Camera feed shows black screen

**Solutions:**
1. Check camera permissions:
   - Windows: Settings → Privacy → Camera
   - macOS: System Preferences → Security & Privacy → Camera
   - Linux: `sudo usermod -a -G video $USER`

2. Try different camera device:
   - Edit `config/settings.py`
   - Change `CAMERA_DEVICE_INDEX` from 0 to 1, 2, etc.

3. Test camera separately:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   print(cap.isOpened())
   cap.release()
   ```

#### Face Not Detected
**Symptoms:** Face landmarks not visible in Dashboard

**Solutions:**
1. Improve lighting
   - Use diffuse, front-facing light
   - Avoid backlit conditions
   - Ensure 300+ lux lighting

2. Adjust camera position
   - Position at eye level
   - Distance: 2-3 feet from face
   - Face should occupy 20-80% of frame

3. Increase detection confidence:
   ```python
   # In config/settings.py
   FACE_DETECTION_CONFIDENCE = 0.5  # Lower = more sensitive
   ```

#### Inaccurate Gaze Tracking
**Symptoms:** Gaze cursor doesn't follow eyes

**Solutions:**
1. Recalibrate:
   - Go to Calibration page
   - Keep head still during calibration
   - Focus directly on each point

2. Adjust smoothing:
   ```python
   GAZE_SMOOTHING_WINDOW = 3  # Lower = more responsive
   ```

3. Check eye openness:
   - Ensure eyes are clearly visible
   - Avoid heavy makeup/glasses
   - Maximize contrast around eyes

#### Slow Performance
**Symptoms:** Low FPS, laggy interface

**Solutions:**
1. Reduce resolution:
   ```python
   CAMERA_RESOLUTION = (640, 480)  # From 1280x720
   ```

2. Enable performance mode:
   - Settings → System Settings → Performance Mode

3. Close background applications
4. Disable unnecessary overlays:
   ```python
   ENABLE_PERFORMANCE_MONITORING = False
   ```

#### Flask Server Won't Start
**Symptoms:** "Address already in use" error

**Solutions:**
1. Change port:
   ```python
   # In app.py
   app.run(port=5001)
   ```

2. Kill existing process:
   **Windows:**
   ```bash
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```
   
   **macOS/Linux:**
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

#### Browser Connection Issues
**Symptoms:** Cannot access http://127.0.0.1:5000

**Solutions:**
1. Verify server is running (check console)
2. Clear browser cache: Ctrl+Shift+Delete
3. Try different browser
4. Check firewall settings

### Performance Tuning

#### Low FPS
```python
# config/settings.py
CAMERA_FPS = 20  # Reduce from 30
FRAME_BUFFER_SIZE = 15  # Reduce from 30
```

#### High Latency
```python
# Reduce smoothing
GAZE_SMOOTHING_WINDOW = 3  # From 5
# Increase sensitivity
GAZE_KALMAN_PROCESS_VARIANCE = 0.05  # Higher = more responsive
```

#### Better Accuracy
```python
# More aggressive filtering
GAZE_KALMAN_MEASUREMENT_VARIANCE = 2.0  # Lower = trust measurements more
# Longer calibration
CALIBRATION_POINT_DURATION = 3.0  # From 2.0
```

## Optimization Guide

### System Performance

1. **CPU Usage**
   - Monitor: Task Manager / Activity Monitor
   - Reduce: Camera resolution, FPS, disable overlays

2. **Memory Usage**
   - Typical: 200-400MB
   - If high: Close other applications, reduce buffer size

3. **Network (if remote)**
   - Local: No issues expected
   - Over network: Reduce resolution, disable visual overlays

### Gaze Tracking Quality

| Factor | Impact | Optimization |
|--------|--------|--------------|
| Lighting | Critical | Diffuse, front-facing light |
| Camera Position | Critical | Eye level, 2-3 feet distance |
| Head Movement | High | Keep relatively still |
| Calibration | High | Careful calibration, many points |
| Smoothing | Medium | Balance responsiveness vs stability |

## Testing After Installation

### 1. System Test
```python
# test_system.py
import sys
import cv2
import mediapipe as mp
import flask
import numpy as np

print("✓ Python version:", sys.version)
print("✓ OpenCV version:", cv2.__version__)
print("✓ MediaPipe version:", mp.__version__)
print("✓ Flask version:", flask.__version__)
print("✓ NumPy version:", np.__version__)
```

### 2. Camera Test
1. Go to Dashboard
2. Verify camera feed displays
3. Check for face detection (green box)
4. Confirm gaze point indicator moves

### 3. Calibration Test
1. Go to Calibration page
2. Complete 9-point calibration
3. Check accuracy metric (target: <2px)
4. System should show "Calibration Complete"

### 4. Interface Test
1. Go to Communication page
2. Focus on keyboard buttons
3. Dwell on letter, should appear in text output
4. Test quick phrases

## Getting Help

1. **Check Logs:**
   ```bash
   tail -f logs/assistive_hands.log
   ```

2. **Enable Debug Mode:**
   ```python
   # app.py
   app.run(debug=True)
   ```

3. **Test Specific Component:**
   ```python
   from camera.face_detector import FaceDetector
   fd = FaceDetector()
   fd.initialize_camera()
   # Test...
   ```

## Uninstalling

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows
```

## Advanced Configuration

See [README.md](README.md) and [config/settings.py](config/settings.py) for advanced options.

---

**Still having issues?** Check the troubleshooting section or review application logs.
