# Android Camera - Quick Integration & Usage Guide

## ✅ Files Complete & Ready

All 4 core files have been created and enhanced:

### 1. **`camera/android_camera.py`** ✓
Core camera streaming module with device management
- `AndroidCameraStream` - Single device handler
- `AndroidCameraManager` - Multi-device controller  
- `AndroidUSBCamera` - USB/ADB utilities

### 2. **`camera/android_integration.py`** ✓
Flask REST API integration
- 10 endpoints for device control
- MJPEG streaming support
- Real-time device monitoring

### 3. **`ui/templates/dashboard.html`** ✓ (Enhanced)
Updated with Android camera UI
- Tab-based camera switching (Desktop ↔ Android)
- Device connection controls
- Connected devices list
- Keyboard shortcuts for all actions
- Integrated gaze cursor overlay

### 4. **`ui/static/js/android_camera.js`** ✓ (Enhanced)
Complete dashboard controller with:
- **Keyboard Shortcuts** (SPACE, ESC, A, D, R, C, M)
- **Gaze Cursor** - Red circular overlay with real-time tracking
- Device management (connect, disconnect, set primary)
- Stream display and status polling
- Connection dialog with IP input
- Toast notifications

---

## 🚀 Setup Instructions

### Step 1: Install IP-Webcam on Android
**This is REQUIRED for WiFi mode**

1. Open **Google Play Store** on your Android device
2. Search for **"IP Webcam"** (by Pavel Khlebovich)
3. Install the FREE version
4. Open app → Grant camera permissions → Tap "Start server"
5. Note the IP address displayed (e.g., `http://192.168.1.100:8888`)

### Step 2: Add Android Integration to Flask App

Update your `app.py`:

```python
from flask import Flask
from camera.android_integration import init_android_camera

app = Flask(__name__)

# Initialize Android camera support
android_camera = init_android_camera(app)

# Rest of your app configuration...
```

### Step 3: Start the Application

```bash
python app.py
```

Open browser: `http://localhost:5000`

---

## 💻 How to Use

### Via Dashboard UI

1. **Navigate to Android Camera tab**
   - Click "Android Camera" tab in dashboard
   
2. **Connect a Device**
   - Click "Connect Device" button
   - Select mode: WiFi or USB
   - For WiFi: Enter device IP (from IP-Webcam app)
   - Click "Connect"

3. **View Stream**
   - Stream appears automatically
   - Device listed under "Connected Devices"

### Via Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `A` | Switch to Android camera tab |
| `D` | Switch to Desktop camera tab |
| `R` | Refresh device list |
| `C` | Open connect dialog |
| `SPACE` | Toggle gaze cursor on/off |
| `ESC` | Emergency stop (disconnect all) |
| `M` | Toggle between gaze/mouse control |

### Via REST API

```bash
# List available devices
curl http://localhost:5000/api/android/devices

# Connect device
curl -X POST http://localhost:5000/api/android/connect \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "phone1",
    "device_ip": "192.168.1.100",
    "port": 8888,
    "mode": "network",
    "use_as_primary": true
  }'

# Get stream
curl http://localhost:5000/api/android/primary-stream

# Get device status
curl http://localhost:5000/api/android/status

# Disconnect device
curl -X POST http://localhost:5000/api/android/disconnect/phone1
```

---

## 🎮 Gaze Cursor Features

### Activation
- Automatically shows when gaze tracking is enabled
- Red circular cursor with glow effect
- Follows mouse movement (for testing)
- Position tracked in real-time

### Controls
- **SPACE** - Toggle on/off
- **ESC** - Hide and emergency stop
- **M** - Switch to mouse mode (hide cursor)

### Visual Features
- Red (#ff0000) with semi-transparent fill
- Outer glow for visibility
- 20px diameter
- Smooth transitions
- Z-index: 9999 (always on top)

---

## 🔧 Configuration Options

### Resolution & FPS
```python
# Via Python API
camera = AndroidCameraStream(
    device_ip="192.168.1.100",
    port=8888,
    mode='network'
)
camera.frame_width = 1280
camera.frame_height = 720
camera.fps = 30
camera.start()
```

### Via Dashboard
1. Connect device
2. Select device → Configure
3. Adjust: Resolution, FPS
4. Apply changes

---

## 📱 Connection Methods

### WiFi (Recommended)
✓ No cables  
✓ Multiple devices  
✓ Easy setup  
✗ Slightly higher latency (50-200ms)

**Setup:**
1. Install IP-Webcam app
2. Enter IP from app in dashboard
3. Port: 8888

### USB (USB Debugging)
✓ Low latency (<50ms)  
✓ Direct connection  
✗ Single device  
✗ Requires adb setup

**Setup:**
1. Enable USB Debugging on device
2. Connect via USB cable
3. Run: `adb devices`
4. Select USB mode in dashboard

---

## 🐛 Troubleshooting

### Stream Not Showing
- **Check:** Is IP-Webcam running on phone?
- **Check:** Both devices on same WiFi?
- **Try:** Press R to refresh, then reconnect

### Can't Find Devices
```bash
# Test ADB connection
adb devices

# Check network connection
ping 192.168.1.100
```

### High Latency
- Reduce resolution: 640x480 instead of 1280x720
- Reduce FPS: 15 instead of 30
- Use USB connection instead of WiFi
- Move closer to WiFi router

### Connection Timeout
- Make sure IP-Webcam app is started
- Check firewall isn't blocking port 8888
- Try USB mode with ADB forward

---

## 📊 API Endpoints Reference

```
GET  /api/android/devices                  → List devices
GET  /api/android/device-info/<id>         → Device info
POST /api/android/connect                  → Connect device
POST /api/android/disconnect/<id>          → Disconnect
GET  /api/android/stream/<id>              → Stream video
GET  /api/android/primary-stream           → Primary stream
GET  /api/android/status                   → All device status
POST /api/android/set-primary/<id>         → Set primary
POST /api/android/configure                → Configure settings
POST /api/android/shutdown                 → Stop all
```

---

## 🎯 Next Steps

1. **Install IP-Webcam** on your Android device
2. **Start IP-Webcam** app and note the IP
3. **Start Flask app**: `python app.py`
4. **Open Dashboard**: `http://localhost:5000`
5. **Click Android Camera tab** → Connect Device
6. **Enter IP address** from IP-Webcam app
7. **Click Connect** - stream should appear!

---

## 📝 Notes

- Dashboard auto-refreshes device status every 2 seconds
- Gaze cursor works with any tracking system
- Supports unlimited Android devices simultaneously
- Keyboard shortcuts work on any page
- Notifications appear as toasts (top-right)

**Enjoy enhanced gaze tracking with Android cameras!** 📱👁️
