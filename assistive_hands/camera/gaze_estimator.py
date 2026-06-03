"""
Gaze estimator using iris position (primary) + optional head movement.
Original working version – eyes control cursor.
"""

import numpy as np
import logging
from collections import deque
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class GazeEstimator:
    def __init__(self):
        # Eye gaze (iris) tracking
        self.gaze_history = deque(maxlen=5)
        self.calibrated = False
        self.calibration_matrix = None
        
        # Head tracking (optional, disabled by default)
        self.head_ref = None
        self.head_weight = 0.0   # 0 = no head, 1 = full head
        
        # Screen
        self.screen_w, self.screen_h = 1920, 1080
        
        # Current gaze
        self.current_gaze = (0.5, 0.5)
        
        logger.info("GazeEstimator: Using EYE IRIS tracking (primary)")
    
    def estimate_gaze_from_eyes(self, left_iris, right_iris, left_corners, right_corners,
                                frame_shape, face_landmarks=None):
        """
        Estimate gaze from iris positions. Head movement is IGNORED unless enabled.
        """
        try:
            h, w = frame_shape[:2]
            
            if left_iris is None or right_iris is None:
                return self.current_gaze
            
            # Left iris position relative to left eye corners
            if left_corners is not None:
                lx0, ly0 = left_corners[0]  # inner corner
                lx1, ly1 = left_corners[1]  # outer corner
                eye_width = abs(lx1 - lx0)
                if eye_width > 0:
                    gaze_x_left = (left_iris[0] - lx0) / eye_width
                    gaze_y_left = (left_iris[1] - ly0) / (abs(left_corners[2][1] - ly0) + 1e-6)
                else:
                    gaze_x_left, gaze_y_left = 0.5, 0.5
            else:
                gaze_x_left, gaze_y_left = 0.5, 0.5
            
            # Right iris
            if right_corners is not None:
                rx0, ry0 = right_corners[0]
                rx1, ry1 = right_corners[1]
                eye_width = abs(rx1 - rx0)
                if eye_width > 0:
                    gaze_x_right = (right_iris[0] - rx0) / eye_width
                    gaze_y_right = (right_iris[1] - ry0) / (abs(right_corners[2][1] - ry0) + 1e-6)
                else:
                    gaze_x_right, gaze_y_right = 0.5, 0.5
            else:
                gaze_x_right, gaze_y_right = 0.5, 0.5
            
            # Average both eyes
            raw_gaze_x = (gaze_x_left + gaze_x_right) / 2.0
            raw_gaze_y = (gaze_y_left + gaze_y_right) / 2.0
            
            # Clamp and mirror (natural mapping)
            raw_gaze_x = max(0.0, min(1.0, raw_gaze_x))
            raw_gaze_y = max(0.0, min(1.0, raw_gaze_y))
            
            # Mirror X for intuitive movement (looking left -> cursor left)
            gaze_x = 1.0 - raw_gaze_x
            gaze_y = raw_gaze_y   # Y is fine
            
            # Apply calibration if available
            if self.calibrated and self.calibration_matrix is not None:
                gaze_x, gaze_y = self.apply_calibration((gaze_x, gaze_y))
            
            # Smooth
            self.gaze_history.append((gaze_x, gaze_y))
            smooth_x = np.mean([g[0] for g in self.gaze_history])
            smooth_y = np.mean([g[1] for g in self.gaze_history])
            
            self.current_gaze = (smooth_x, smooth_y)
            return smooth_x, smooth_y
            
        except Exception as e:
            logger.debug(f"Gaze estimation error: {e}")
            return self.current_gaze
    
    def apply_calibration(self, gaze_point):
        """Apply polynomial regression mapping if available."""
        if not self.calibrated or self.calibration_matrix is None:
            return gaze_point
        try:
            # Simple linear scaling – replace with your polynomial if needed
            x = gaze_point[0] * self.calibration_matrix[0] + self.calibration_matrix[1]
            y = gaze_point[1] * self.calibration_matrix[2] + self.calibration_matrix[3]
            return max(0.0, min(1.0, x)), max(0.0, min(1.0, y))
        except:
            return gaze_point
    
    def load_calibration_data(self, filepath):
        """Load calibration matrix from npz file."""
        try:
            import numpy as np
            data = np.load(filepath)
            self.calibration_matrix = data['matrix']
            self.calibrated = True
            logger.info(f"Calibration loaded from {filepath}")
            return True
        except Exception as e:
            logger.warning(f"No calibration found: {e}")
            return False
    
    def reset_smoothing_history(self):
        self.gaze_history.clear()
    
    def apply_smoothing(self, gaze_point):
        """Simple moving average (kept for compatibility)."""
        self.gaze_history.append(gaze_point)
        smooth_x = np.mean([g[0] for g in self.gaze_history])
        smooth_y = np.mean([g[1] for g in self.gaze_history])
        return (smooth_x, smooth_y)
    
    # Dummy methods for compatibility
    def detect_facial_expressions(self, *args, **kwargs):
        return {}
    
    def detect_double_blink(self, *args, **kwargs):
        return False
    
    def reset_calibration(self):
        self.calibrated = False
        self.calibration_matrix = None