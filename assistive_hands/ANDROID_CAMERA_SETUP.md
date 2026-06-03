# Android Camera Integration Guide

## Overview
This guide explains how to connect Android devices (phones, tablets, or specialized cameras) to AssistiveHands for gaze tracking and eye detection.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Connection Methods](#connection-methods)
3. [Network Setup](#network-setup)
4. [USB Setup](#usb-setup)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: WiFi Connection (Recommended)
1. Install **IP-Webcam** or **DroidCam** app on your Android device
2. Launch the app and note the IP address and port
3. In AssistiveHands Dashboard → Android Cameras → Connect
4. Enter: `192.168.x.x:8888` (replace with your device IP)
5. Click "Connect as Primary"

### Option 2: USB Connection
1. Enable USB Debugging on Android device (Settings → Developer Options → USB Debugging)
2. Connect device via USB cable
3. In Dashboard → Android Cameras → Refresh Devices
4. Select your device and click "Connect"

---

## Connection Methods

### Method 1: IP-Webcam (WiFi/Network)
**Best for:** Stability, no cables, multiple devices

**Install:**
```bash
# Android app: IP-Webcam
# Available on Google Play Store
# Free version or Pro version
```

**Setup:**
1. Install app on Android device
2. Grant camera and audio permissions
3. Tap "Start server"
4. Note the URL: `http://192.168.x.x:8888`
5. Use this IP in AssistiveHands

**Configuration in AssistiveHands:**
```python
from camera.android_camera import AndroidCameraStream

camera = AndroidCameraStream(
    device_ip="192.168.x.x",
    port=8888,
    mode='network'
)
camera.start()
```

### Method 2: DroidCam (WiFi/USB)
**Best for:** Low latency, good video quality

**Install:**
```bash
# Android app: DroidCam Wireless Webcam
# Available on Google Play Store
# Free version with ads or Pro version
```

**Setup:**
1. Install app on Android device
2. Install DroidCam client on computer (if needed)
3. Grant permissions
4. Note IP address from app

**Configuration in AssistiveHands:**
```python
camera = AndroidCameraStream(
    device_ip="192.168.x.x",
    port=4747,
    mode='network'
)
camera.start()
```

### Method 3: ADB USB Connection
**Best for:** Direct USB connection without WiFi

**Prerequisites:**
```bash
# Windows
pip install adb-sync

# macOS
brew install android-platform-tools

# Linux
sudo apt install android-tools-adb
```

**Enable on Device:**
1. Settings → Developer Options → Enable USB Debugging
2. Connect via USB cable
3. Accept USB debugging prompt

**Configuration in AssistiveHands:**
```python
from camera.android_integration import AndroidUSBCamera

# List devices
devices = AndroidUSBCamera.get_adb_devices()
print(devices)  # ['emulator-5554', 'FA7AT1A00821']

# Enable TCP/IP mode for wireless fallback
AndroidUSBCamera.enable_tcpip_mode('FA7AT1A00821')

# Connect using USB forwarding
camera = AndroidCameraStream(
    device_ip=None,
    port=5555,
    mode='usb'
)
camera.start()
```

---

## Network Setup

### Check Device IP Address
**On Android:**
1. Settings → About Phone → IP Address
2. OR: WiFi Settings → Connected Network → IP Address

### Enable IP-Webcam Server
**Steps:**
1. Open IP-Webcam app
2. Scroll to "IP Address" section
3. Note format: `http://192.168.x.x:8888`
4. Ensure device and computer are on same WiFi network

### Test Connection
```bash
# From computer terminal
curl http://192.168.x.x:8888/video

# Or in Python
import cv2
cap = cv2.VideoCapture('http://192.168.x.x:8888/video')
ret, frame = cap.read()
```

### Network Requirements
- Both devices on same WiFi network
- Minimum 2 Mbps bandwidth per device
- Low latency for real-time tracking (< 100ms)
- 2.4 GHz WiFi recommended for stability

---

## USB Setup

### Windows Setup
```bash
# 1. Install ADB
choco install adb  # Using Chocolatey
# OR download from: https://developer.android.com/tools/adb

# 2. Connect device via USB
# 3. Run command
adb devices

# Expected output:
# List of attached devices
# FA7AT1A00821          device

# 4. Forward port (optional)
adb forward tcp:5555 tcp:5555
```

### macOS Setup
```bash
# 1. Install ADB
brew install android-platform-tools

# 2. Connect device
# 3. List devices
adb devices

# 4. Forward port
adb forward tcp:5555 tcp:5555
```

### Linux Setup
```bash
# 1. Install ADB
sudo apt update
sudo apt install android-tools-adb

# 2. Connect device
# 3. List devices
adb devices

# 4. Forward port
adb forward tcp:5555 tcp:5555
```

### Get Device Info via ADB
```bash
# Get device model
adb shell getprop ro.product.model

# Get Android version
adb shell getprop ro.build.version.release

# Get screen resolution
adb shell wm size

# Get camera capabilities
adb shell getprop ro.hardware.keystore
```

---

## Configuration

### Connect Multiple Devices
```python
from camera.android_integration import AndroidCameraManager

manager = AndroidCameraManager()

# Add first device
manager.add_device(
    device_id="phone1",
    device_ip="192.168.1.100",
    port=8888,
    mode='network'
)

# Add second device
manager.add_device(
    device_id="phone2",
    device_ip="192.168.1.101",
    port=8888,
    mode='network'
)

# Get frame from specific device
frame = manager.get_frame("phone1")
```

### Adjust Resolution and FPS
```python
from camera.android_camera import AndroidCameraStream

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

### In Flask Application
```python
from flask import Flask
from camera.android_integration import init_android_camera

app = Flask(__name__)

# Initialize Android camera support
android_camera = init_android_camera(app)

# Connect device via API
# POST /api/android/connect
# {
#     "device_id": "phone1",
#     "device_ip": "192.168.1.100",
#     "port": 8888,
#     "mode": "network",
#     "use_as_primary": true
# }
```

### Dashboard Integration
```html
<!-- Add to dashboard.html -->
<script src="{{ url_for('send_static', path='js/android_camera.js') }}"></script>

<!-- Android Camera Section -->
<div class="card mb-4">
    <div class="card-header">
        <h5>Android Cameras</h5>
    </div>
    <div class="card-body">
        <button class="btn btn-primary" id="androidConnectBtn">Connect Device</button>
        <button class="btn btn-secondary" id="refreshDevicesBtn">Refresh</button>
        <div id="androidDevicesList" class="mt-3"></div>
    </div>
</div>

<!-- Video Stream -->
<img id="androidVideoFeed" src="/api/android/primary-stream" alt="Android Camera Feed">

<script>
    const androidManager = new AndroidCameraManager();
</script>
```

---

## Troubleshooting

### Can't Find Devices
```bash
# Check ADB connection
adb devices

# Reconnect device
adb kill-server
adb start-server
adb devices

# On Windows, ensure driver is installed
# Download: https://developer.android.com/studio/run/win-usb
```

### WiFi Connection Issues
- **Device not on same network:** Check WiFi SSID and password
- **Firewall blocking:** Disable firewall temporarily or add exception
- **Port already in use:** Change port in IP-Webcam settings
- **Latency too high:** Move closer to WiFi router or reduce resolution

### Video Feed Not Displaying
```python
# Test connection in Python
import cv2

url = "http://192.168.1.100:8888/video"
cap = cv2.VideoCapture(url)

if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print("Connection successful!")
        print(f"Frame shape: {frame.shape}")
    else:
        print("Cannot read frames")
else:
    print("Cannot open stream")
```

### High Latency
- Reduce resolution: 640x480 instead of 1280x720
- Reduce FPS: 15 instead of 30
- Use USB connection instead of WiFi
- Move closer to WiFi router

### Gaze Tracking Not Accurate
1. Run calibration on new device
2. Ensure face is clearly visible
3. Adjust camera angle to eye level
4. Improve lighting
5. Reduce motion blur (increase FPS)

### Camera Freezes
```python
# Restart camera stream
camera.stop()
time.sleep(1)
camera.start()
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/android/devices` | GET | List connected devices |
| `/api/android/device-info/<id>` | GET | Get device information |
| `/api/android/connect` | POST | Connect Android device |
| `/api/android/disconnect/<id>` | POST | Disconnect device |
| `/api/android/stream/<id>` | GET | Stream from device |
| `/api/android/primary-stream` | GET | Stream from primary device |
| `/api/android/status` | GET | Get all device status |
| `/api/android/set-primary/<id>` | POST | Set primary device |
| `/api/android/configure` | POST | Configure device settings |
| `/api/android/shutdown` | POST | Stop all streams |

---

## Performance Tips

1. **Use 640x480 resolution** for lower latency
2. **Set FPS to 15-20** for tracking accuracy
3. **USB connection** for best latency (< 50ms)
4. **WiFi on 5GHz** band for better stability
5. **Keep device close** to reduce WiFi latency
6. **Disable automatic focus** to reduce latency
7. **Use high-quality device** (at least HD camera)

---

## Supported Devices

- **Phones:** All modern Android phones (5.0+)
- **Tablets:** iPad, Samsung Tab, etc.
- **Specialized Cameras:** FLIR thermal, intel RealSense, etc.
- **Drones:** Android-based drone cameras with streaming

---

## Next Steps

1. Configure your Android device
2. Test connection through API
3. Run calibration with new camera
4. Monitor latency and accuracy
5. Adjust settings if needed

For issues, check logs:
```bash
# Check application logs
tail -f logs/app.log
```
