# MY CODE VERSION FIX OF THE PROJECT ASSISTIVE HANDS

# assistive_hands/camera/__pycache__/eye_tracker.py

"""Eye tracking module for blink detection and eye position tracking."""

import numpy as np
import cv2
import logging
import time
from typing import Tuple, Optional, Dict, List

from config.settings import SystemConfig

logger = logging.getLogger(__name__)


class EyeTracker:
    """Tracks eye position and detects blinks."""

    # MediaPipe face mesh eye landmark indices
    RIGHT_EYE_INDICES = [33, 133]
    LEFT_EYE_INDICES = [362, 263]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_IRIS = [474, 475, 476, 477]
    LEFT_IRIS = [469, 470, 471, 472]

    def __init__(self):
        """Initialize eye tracker."""
        self.ear_history = []
        self.max_history_length = 10
        self.blink_threshold = SystemConfig.EYE_ASPECT_RATIO_THRESHOLD
        self.is_blinking = False
        self.blink_count = 0
        self._last_ear_value = 1.0

    def extract_eye_landmarks(self, face_landmarks: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract eye landmarks from face landmarks."""
        try:
            left_eye = face_landmarks[self.LEFT_EYE]
            right_eye = face_landmarks[self.RIGHT_EYE]
            
            left_iris = face_landmarks[self.LEFT_IRIS]
            right_iris = face_landmarks[self.RIGHT_IRIS]
            
            return {
                'left_eye': left_eye,
                'right_eye': right_eye,
                'left_iris': left_iris,
                'right_iris': right_iris
            }
        except Exception as e:
            logger.error(f"Error extracting eye landmarks: {e}")
            return None

    def calculate_eye_aspect_ratio(self, eye_landmarks: np.ndarray) -> float:
        """Calculate eye aspect ratio (EAR) for blink detection."""
        try:
            if eye_landmarks is None or len(eye_landmarks) < 4:
                return self._last_ear_value
            
            pts = eye_landmarks.astype(np.float32)
            
            vertical_1 = np.linalg.norm(pts[1] - pts[3])
            vertical_2 = np.linalg.norm(pts[2] - pts[4]) if len(pts) > 4 else vertical_1
            horizontal = np.linalg.norm(pts[0] - pts[2]) if len(pts) > 2 else 1.0
            
            if horizontal == 0:
                horizontal = 1.0
            
            ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
            ear = max(0.0, min(0.5, ear))  # Clamp to reasonable range
            self._last_ear_value = ear
            return ear
        except Exception as e:
            logger.error(f"Error calculating EAR: {e}")
            return self._last_ear_value

    def detect_blink(self, ear_value: float, threshold: Optional[float] = None) -> bool:
        """Detect if eyes are blinked based on EAR."""
        if threshold is None:
            threshold = self.blink_threshold
        
        self.ear_history.append(ear_value)
        if len(self.ear_history) > self.max_history_length:
            self.ear_history.pop(0)
        
        was_blink_detected = ear_value < threshold
        
        if was_blink_detected and not self.is_blinking:
            self.is_blinking = True
            self.blink_count += 1
            return True
        elif not was_blink_detected:
            self.is_blinking = False
        
        return False

    def get_pupil_position(self, eye_landmarks: np.ndarray, iris_landmarks: Optional[np.ndarray] = None) -> np.ndarray:
        """Get pupil/iris position."""
        try:
            if iris_landmarks is not None and len(iris_landmarks) >= 4:
                iris_center = iris_landmarks.mean(axis=0)
                return iris_center
            elif eye_landmarks is not None and len(eye_landmarks) > 0:
                return eye_landmarks.mean(axis=0)
            else:
                return np.array([0.5, 0.5])
        except Exception as e:
            logger.error(f"Error getting pupil position: {e}")
            return np.array([0.5, 0.5])

    def normalize_coordinates(self, eye_position: np.ndarray, frame_size: Tuple[int, int]) -> np.ndarray:
        """Normalize eye coordinates to screen space."""
        try:
            normalized = eye_position.copy()
            normalized[0] = np.clip(normalized[0], 0, 1)
            normalized[1] = np.clip(normalized[1], 0, 1)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing coordinates: {e}")
            return np.array([0.5, 0.5])

    def get_eye_openness(self, left_ear: float, right_ear: float) -> float:
        """Get average eye openness (0.0 to 1.0)."""
        avg_ear = (left_ear + right_ear) / 2.0
        openness = min(1.0, max(0.0, avg_ear / 0.5))
        return openness

    def get_blink_count(self) -> int:
        """Get total blink count."""
        return self.blink_count

    def reset_blink_count(self):
        """Reset blink counter."""
        self.blink_count = 0

        