# assistive_hands/config/__pycache__/settings.py

"""System configuration settings for AssistiveHands."""

import os
from pathlib import Path


class SystemConfig:
    """Central configuration class for all system parameters."""

    # ========== Camera Settings ==========
    # CAMERA_RESOLUTION = (1280, 720)
    CAMERA_RESOLUTION = (640, 480)
    CAMERA_FPS = 30
    # ---- IP Webcam (Android app) ----
    # Replace the IP below with what the IP Webcam app shows on your phone
    # Format: 'http://<YOUR_PHONE_IP>:8080/video'
    CAMERA_DEVICE_INDEX = 0
    CAMERA_BRIGHTNESS = 0
    CAMERA_CONTRAST = 0

    # ========== Face Detection Settings ==========
    FACE_DETECTION_CONFIDENCE = 0.7
    FACE_TRACKING_CONFIDENCE = 0.7
    FACE_MODEL_COMPLEXITY = 1  # 0: light, 1: full
    MIN_FACE_SIZE = (50, 50)
    MAX_FACE_ATTEMPTS = 3

    # ========== Eye Tracking Settings ==========
    EYE_ASPECT_RATIO_THRESHOLD = 0.35  # Blink detection threshold
    EYE_SMOOTHING_WINDOW = 5
    EYE_DETECTION_CONFIDENCE = 0.8
    BLINK_DEBOUNCE_TIME = 0.2  # seconds

    # ========== Gaze Estimation Settings ==========
    GAZE_FILTER_TYPE = 'kalman'  # 'moving_average' or 'kalman'
    GAZE_SMOOTHING_WINDOW = 5
    GAZE_KALMAN_PROCESS_VARIANCE = 0.01
    GAZE_KALMAN_MEASUREMENT_VARIANCE = 4.0
    GAZE_OUTLIER_THRESHOLD = 2.0  # Standard deviations

    # ========== Calibration Settings ==========
    CALIBRATION_GRID_SIZE = 3  # 3x3 grid = 9 points
    CALIBRATION_POINT_DURATION = 2.0  # seconds
    CALIBRATION_SAMPLE_RATE = 30  # Hz
    CALIBRATION_VALIDATION_THRESHOLD = 1.5  # degrees of visual angle
    CALIBRATION_MIN_SAMPLES = 15  # Lowered from 30 - reasonable for 2-second dwell time
    CALIBRATION_MAX_SAMPLES = 100

    # ========== UI Settings ==========
    DWELL_TIME = 1.0  # seconds to activate a button
    DWELL_TIME_MIN = 0.3
    DWELL_TIME_MAX = 3.0
    BUTTON_SIZE = (60, 60)  # pixels
    BUTTON_HOVER_THRESHOLD = 30  # pixels
    KEYBOARD_ROWS = 3
    KEYBOARD_COLS = 10

    # ========== Display Settings ==========
    SCREEN_RESOLUTION = (1920, 1080)
    UI_SCALE_FACTOR = 1.0
    OVERLAY_COLOR = (0, 255, 255)  # BGR
    FACE_BOX_COLOR = (0, 255, 0)
    GAZE_POINT_COLOR = (0, 0, 255)
    GAZE_POINT_RADIUS = 5

    # ========== Performance Settings ==========
    MAX_FPS = 30
    FRAME_BUFFER_SIZE = 30
    ENABLE_PERFORMANCE_MONITORING = True
    LOG_PERFORMANCE_STATS = True

    # ========== File Paths ==========
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    CALIBRATION_DIR = DATA_DIR / 'calibration'
    PROFILE_DIR = DATA_DIR / 'profiles'
    LOG_DIR = BASE_DIR / 'logs'
    MODELS_DIR = BASE_DIR / 'models'

    # ========== Logging Settings ==========
    LOG_LEVEL = 'INFO'
    LOG_FILE = LOG_DIR / 'assistive_hands.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # ========== Flask Settings ==========
    FLASK_DEBUG = False
    FLASK_HOST = '127.0.0.1'
    FLASK_PORT = 5000
    SECRET_KEY = 'your-secret-key-change-in-production'

    # ========== Gesture Detection Settings ==========
    SMILE_THRESHOLD = 0.3
    HEAD_TURN_THRESHOLD = 15  # degrees
    EYEBROW_RAISE_THRESHOLD = 0.2

    # ========== Accessibility Settings ==========
    TEXT_SIZE = 18
    TEXT_SIZE_HEADING = 24
    HIGH_CONTRAST_MODE = False
    SOUND_FEEDBACK_ENABLED = True
    VIBRATION_FEEDBACK_ENABLED = False

    @classmethod
    def setup_directories(cls):
        """Create necessary directories if they don't exist."""
        dirs = [cls.DATA_DIR, cls.CALIBRATION_DIR, cls.PROFILE_DIR, cls.LOG_DIR, cls.MODELS_DIR]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def to_dict(cls):
        """Convert configuration to dictionary."""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('_') and key.isupper()
        }


# Create directories on module import
SystemConfig.setup_directories()
