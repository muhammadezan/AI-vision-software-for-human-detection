# MY CODE VERSION FIX OF THE PROJECT ASSISTIVE HANDS

# assistive_hands/camera/__pycache__/face_detector.py

"""Face detection and landmark extraction using MediaPipe Face Mesh."""

import cv2
import numpy as np
import logging
import time
from typing import Tuple, Optional, Dict

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

from config.settings import SystemConfig

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects faces and extracts face mesh landmarks using the new MediaPipe Tasks API."""

    # MediaPipe Face Mesh landmark indices for eyes
    LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    LEFT_IRIS_INDICES = [469, 470, 471, 472]
    RIGHT_IRIS_INDICES = [474, 475, 476, 477]


        # 👇 ADDED THESE TWO LINES HERE 👇
    LEFT_EYE_CORNERS = [33, 133]    # Outer corner, inner corner
    RIGHT_EYE_CORNERS = [362, 263]  # Outer corner, inner corner

    # Face outline for quality checks
    FACE_OUTLINE = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

    def __init__(self, model_path='models/face_landmarker.task'):
        """Initialize face detection using MediaPipe Face Landmarker."""
        self.landmarker = None
        self.model_path = model_path
        self.cap = None
        self.frame_width = SystemConfig.CAMERA_RESOLUTION[0]
        self.frame_height = SystemConfig.CAMERA_RESOLUTION[1]
        self.detection_quality = 0.0
        self.is_face_detected = False
        self._initialize_landmarker()

    def _initialize_landmarker(self):
        """Initialize MediaPipe Face Landmarker."""
        try:
            if not MEDIAPIPE_AVAILABLE:
                logger.error("MediaPipe library is not installed. Cannot perform face detection.")
                return

            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            import os

            model_file = os.path.abspath(self.model_path)
            
            if not os.path.exists(model_file):
                logger.error(f"Face landmarker model not found at {model_file}.")
                logger.error("Please download the model from: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
                return

            base_options = python.BaseOptions(model_asset_path=model_file)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False, # We don't need blendshapes
                output_facial_transformation_matrixes=False, # We don't need the matrix
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.landmarker = vision.FaceLandmarker.create_from_options(options)
            logger.info("MediaPipe Face Landmarker initialized successfully.")

        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to initialize MediaPipe Face Landmarker: {e}", exc_info=True)
            self.landmarker = None
    
    def initialize_camera(self) -> bool:
        """Initialize webcam or IP stream, trying multiple backends and warm-up strategies."""
        source = SystemConfig.CAMERA_DEVICE_INDEX
        logger.info(f"Initializing camera with source: {source}")

        # If source is a URL (IP Webcam / network stream), use CAP_FFMPEG or CAP_ANY directly
        if isinstance(source, str):
            backends = {'FFMPEG': cv2.CAP_FFMPEG, 'ANY': cv2.CAP_ANY}
        else:
            backends = {'DSHOW': cv2.CAP_DSHOW, 'MSMF': cv2.CAP_MSMF, 'ANY': cv2.CAP_ANY}

        for backend_name, backend_id in backends.items():
            try:
                logger.info(f"--- Trying backend: {backend_name} ---")
                self.cap = cv2.VideoCapture(source, backend_id)
                
                if not self.cap or not self.cap.isOpened():
                    logger.warning(f"Could not open camera with {backend_name} backend.")
                    continue

                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Orientation fix for IP Webcam (phone camera)
                if isinstance(source, str) and 'http' in source:
                    logger.info("IP Webcam detected - using phone camera stream")
                
                logger.info(f"Camera opened with {backend_name}. Reading frames for 2 seconds to stabilize...")
                
                frame = None
                start_time = time.time()
                while time.time() - start_time < 2:
                    ret, current_frame = self.cap.read()
                    if ret:
                        frame = current_frame
                    time.sleep(0.03)

                if frame is None:
                    logger.warning(f"Failed to get a valid frame from {backend_name} after warm-up.")
                    self.cap.release()
                    continue
                
                logger.info(f"Successfully initialized camera with {backend_name} backend.")
                return True

            except Exception as e:
                logger.error(f"Error during camera initialization with {backend_name}: {e}", exc_info=True)
                if self.cap:
                    self.cap.release()
                continue
        
        logger.error("Failed to initialize camera with any available backend.")
        return False

    def detect_face(self, frame: np.ndarray) -> Tuple[bool, Optional[Dict]]:
        """
        Detect face and extract landmarks using MediaPipe Face Landmarker.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Tuple of (face_detected, landmarks_dict)
        """
        if self.landmarker is None:
            return False, None

        try:
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create MediaPipe Image object using the correct API
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Detect face landmarks from the input image.
            detection_result = self.landmarker.detect(mp_image)

            if not detection_result or not detection_result.face_landmarks:
                self.is_face_detected = False
                self.detection_quality = 0.0
                return False, None

            # Get the first (primary) face
            face_landmarks_proto = detection_result.face_landmarks[0]
            
            # Convert landmarks to a numpy array
            h, w, _ = frame.shape
            landmarks = np.array(
                [(lm.x * w, lm.y * h) for lm in face_landmarks_proto], 
                dtype=np.float32
            )

            # Calculate face bounding box from landmarks
            face_outline = landmarks[self.FACE_OUTLINE]
            x_min, y_min = face_outline.min(axis=0)
            x_max, y_max = face_outline.max(axis=0)
            
            face_box = {
                'x_min': int(x_min), 'y_min': int(y_min),
                'x_max': int(x_max), 'y_max': int(y_max),
                'width': int(x_max - x_min), 'height': int(y_max - y_min),
                'center': (int((x_min + x_max) / 2), int((y_min + y_max) / 2))
            }
            
            # 👇 THIS ENTIRE BLOCK MUST BE INDENTED INSIDE THE if block
            landmarks_dict = {
                'landmarks': landmarks,
                'face_box': face_box,
                'left_eye': landmarks[self.LEFT_EYE_INDICES],
                'right_eye': landmarks[self.RIGHT_EYE_INDICES],
                'left_iris': landmarks[self.LEFT_IRIS_INDICES],
                'right_iris': landmarks[self.RIGHT_IRIS_INDICES],
                'left_eye_corners': landmarks[self.LEFT_EYE_CORNERS],
                'right_eye_corners': landmarks[self.RIGHT_EYE_CORNERS],
            }
            
            self.is_face_detected = True
            self.detection_quality = 0.9
            return True, landmarks_dict
            
        except Exception as e:
            logger.error(f"MediaPipe face landmarker error: {e}", exc_info=True)
            return False, None

    def get_face_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Get face landmarks."""
        detected, landmarks_dict = self.detect_face(frame)
        if detected and landmarks_dict:
            return landmarks_dict['landmarks']
        return None

    def is_face_properly_positioned(self, frame: np.ndarray) -> bool:
        """Check if face is properly positioned."""
        detected, landmarks_dict = self.detect_face(frame)
        if not detected:
            return False
        
        face_box = landmarks_dict['face_box']
        h, w, _ = frame.shape
        
        face_area_ratio = (face_box['width'] * face_box['height']) / (w * h)
        if not (0.2 <= face_area_ratio <= 0.8):
            return False
        
        center_x, center_y = face_box['center']
        if abs(center_x - w/2) > w/4 or abs(center_y - h/2) > h/4:
            return False
        
        return True

    def get_detection_quality(self) -> float:
        """Get detection quality score (0.0 to 1.0)."""
        if not self.is_face_detected:
            return 0.0
        return min(1.0, self.detection_quality)

    def release_camera(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            logger.info("Camera released")

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Get a frame from camera."""
        if self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame

    def get_camera_backend(self) -> str:
        """Get the backend API name of the camera."""
        if self.cap is not None and self.cap.isOpened():
            return self.cap.getBackendName()
        return "N/A"

    def is_camera_initialized(self) -> bool:
        """Check if the camera is initialized and opened."""
        return self.cap is not None and self.cap.isOpened()

    def __del__(self):
        """Cleanup on object deletion."""
        self.release_camera()

        