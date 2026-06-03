# AssistiveHands - Project File Structure

```
assistive_hands/
│
├── 📄 README.md                          # Main documentation
├── 📄 START_HERE.md                      # Getting started guide
├── 📄 QUICKSTART.md                      # Quick start guide
├── 📄 INDEX.md                           # Project index
├── 📄 PROJECT_SUMMARY.md                 # Project summary
├── 📄 NEWREADME.md                       # Updated documentation
├── 📄 INSTALLATION.md                    # Installation guide
├── 📄 DEPLOYMENT.md                      # Deployment guide
│
├── 📱 ANDROID Integration
│   ├── 📄 ANDROID_QUICKSTART.md
│   ├── 📄 ANDROID_CAMERA_SETUP.md
│   ├── 📄 DROIDCAM_FIX.md
│
├── 📊 Testing & Debugging
│   ├── 📄 TEST_CURSOR.md
│   ├── 📄 test_cursor.py                 # Cursor testing script
│   ├── 📄 test_cursor_diagnostic.py      # Cursor diagnostics
│   ├── 📄 test_eye_detection.py          # Eye detection testing
│   ├── 📄 test_minimal.py                # Minimal test
│   ├── 📄 debug_camera.py                # Camera debugging
│   ├── 📄 debug_gaze.py                  # Gaze debugging
│   ├── 📄 quick_cam_test.py              # Quick camera test
│   ├── 📄 detect_cameras.py              # Camera detection
│
├── 🔧 Patch & Utility Scripts
│   ├── 📄 patch_app.py                   # App patcher
│   ├── 📄 patch_dashboard.py             # Dashboard patcher
│   ├── 📄 fix_cursor_final.py            # Final cursor fix
│   ├── 📄 improve_cursor.py              # Cursor improvement
│
├── 📄 app.py                             # Main Flask application
├── 📄 camera_stream.py                   # Camera streaming
├── 📄 requirements.txt                   # Python dependencies
│
├── 📁 calibration/                       # Calibration module
│   ├── __init__.py
│   └── calibrator.py                     # Calibration logic
│
├── 📁 camera/                            # Camera module
│   ├── __init__.py
│   ├── android_camera.py                 # Android camera
│   ├── android_integration.py            # Android integration
│   ├── droidcam_stream.py                # DroidCam streaming
│   ├── eye_tracker.py                    # Eye tracking
│   ├── face_detector.py                  # Face detection
│   ├── gaze_estimator.py                 # Gaze estimation
│   └── test_droidcam.py                  # DroidCam testing
│
├── 📁 config/                            # Configuration module
│   ├── __init__.py
│   └── settings.py                       # System settings
│
├── 📁 data/                              # Data directory
│   ├── calibration/
│   │   ├── default_calibration.npz       # Default calibration data
│   │   └── default_metadata.json         # Calibration metadata
│   └── profiles/                         # User profiles
│
├── 📁 docs/                              # Documentation
│
├── 📁 logs/                              # Log files
│
├── 📁 models/                            # ML models
│   └── face_landmarker.task              # MediaPipe face landmark model
│
├── 📁 tests/                             # Test directory
│
├── 📁 ui/                                # UI/Frontend
│   ├── 📁 static/                        # Static assets
│   │   ├── css/
│   │   │   └── style.css                 # Main stylesheet
│   │   └── js/                           # JavaScript files
│   │       ├── utils.js                  # Utility functions
│   │       ├── dashboard.js              # Dashboard logic
│   │       ├── android_camera.js         # Android camera JS
│   │       ├── calibration.js            # Calibration UI
│   │       ├── communication.js          # Communication UI
│   │       ├── settings.js               # Settings UI
│   │       └── setup.js                  # Setup UI
│   │
│   └── 📁 templates/                     # HTML templates
│       ├── dashboard.html                # Main dashboard (NEW)
│       ├── dashboard_old.html            # Old dashboard
│       ├── calibration.html              # Calibration page
│       ├── communication.html            # Communication page
│       ├── settings.html                 # Settings page
│       ├── setup.html                    # Setup page
│       └── debug.html                    # Debug page
│
└── 📁 utils/                             # Utility modules
    ├── __init__.py
    ├── cursor_control.py                 # Cursor control logic
    ├── event_handler.py                  # Event handling
    ├── keyboard_control.py               # Keyboard control
    └── signal_processing.py              # Signal processing
```

## 📊 File Count Summary

| Category | Count |
|----------|-------|
| Python Files (.py) | 30+ |
| Documentation (.md) | 11 |
| HTML Templates | 7 |
| JavaScript Files | 7 |
| CSS Files | 1 |
| Config Files | 2 |
| Data Files | 2 |
| ML Models | 1 |
| **Total** | **60+** |

## 🎯 Key Directories

### Core Application
- **`app.py`** - Flask server with gaze tracking and blink detection
- **`requirements.txt`** - Python dependencies

### Face & Eye Tracking
- **`camera/`** - Camera handling and tracking algorithms
  - Face detection, eye tracking, gaze estimation
  - Android and DroidCam integration

### UI Frontend
- **`ui/templates/`** - HTML pages (dashboard, calibration, communication)
- **`ui/static/js/`** - JavaScript for interactivity
- **`ui/static/css/`** - Styling

### Utilities
- **`utils/`** - Core utilities (cursor, keyboard, events, signals)
- **`config/`** - Configuration and settings
- **`calibration/`** - Calibration system

### Data & Models
- **`data/`** - Calibration data and user profiles
- **`models/`** - MediaPipe face landmark model

### Documentation & Testing
- **`README.md`, `QUICKSTART.md`** - User guides
- **`test_*.py`** - Testing scripts
- **`debug_*.py`** - Debug utilities
