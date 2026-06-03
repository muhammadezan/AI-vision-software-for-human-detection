"""Camera streaming module for real-time video processing."""

import time
import cv2
import numpy as np
import logging
from typing import Generator, Optional, Tuple, Dict
from io import BytesIO

from camera.face_detector import FaceDetector
from camera.eye_tracker import EyeTracker
from camera.gaze_estimator import GazeEstimator
from config.settings import SystemConfig

logger = logging.getLogger(__name__)


class CameraStream:
    """Handles real-time camera streaming with face and gaze processing."""
    
    def __init__(self):
        """Initialize camera stream."""
        self.face_detector = FaceDetector()
        self.eye_tracker = EyeTracker()
        self.gaze_estimator = GazeEstimator()
        self.user_profile = 'default'
        self.calibration_enabled = True  # Whether to apply calibration to gaze
        
        self.is_running = False
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()
        self.processing_time = 0
        
        self.current_gaze = (0.5, 0.5)
        self.current_face_box = None
        self.is_face_detected = False
        self.blink_detected = False
        self.eye_openness = 1.0

    def start(self) -> bool:
        """Start camera stream."""
        try:
            logger.info("Starting camera stream...")
            if not self.face_detector.initialize_camera():
                logger.error("Failed to initialize camera in FaceDetector")
                return False
            
            # Test that we can actually read a frame
            logger.info("Testing camera frame capture...")
            test_ret, test_frame = self.face_detector.get_frame()
            if not test_ret or test_frame is None:
                logger.error("Failed to read test frame from camera")
                return False
            
            logger.info(f"Test frame shape: {test_frame.shape}")
            
            self.is_running = True
            
            # Start continuous frame processing thread
            from threading import Thread
            processing_thread = Thread(target=self._process_frames_continuously, daemon=True)
            processing_thread.start()
            logger.info("Frame processing thread started")
            
            logger.info("Camera stream started successfully")
            return True
        except Exception as e:
            logger.error(f"Camera start error: {e}", exc_info=True)
            return False

    def _process_frames_continuously(self):
        """Continuously process camera frames in background thread."""
        while self.is_running:
            try:
                ret, frame = self.face_detector.get_frame()
                if ret:
                    self.process_frame(frame)
                    self.frame_count += 1
                else:
                    time.sleep(0.01)
            except Exception as e:
                logger.error(f"Frame processing error: {e}", exc_info=True)
                time.sleep(0.1)

    def load_user_calibration(self, user_profile: str = 'default') -> bool:
        """
        Load calibration data for a user.
        
        Args:
            user_profile: User profile name
            
        Returns:
            True if calibration loaded successfully
        """
        try:
            from pathlib import Path
            from config.settings import SystemConfig
            
            self.user_profile = user_profile
            calibration_file = SystemConfig.CALIBRATION_DIR / f"{user_profile}_calibration.npz"
            
            if calibration_file.exists():
                success = self.gaze_estimator.load_calibration_data(str(calibration_file))
                if success:
                    logger.info(f"Loaded calibration for user: {user_profile}")
                    self.calibration_enabled = True
                return success
            else:
                logger.debug(f"No calibration file found for user: {user_profile}")
                return False
        except Exception as e:
            logger.error(f"Error loading user calibration: {e}")
            return False
    
    def disable_calibration(self):
        """
        Disable calibration application (used during new calibration).
        """
        self.calibration_enabled = False
        self.gaze_estimator.calibrated = False
        self.gaze_estimator.reset_smoothing_history()
        logger.info("Calibration disabled for sample collection")
    
    def enable_calibration(self):
        """
        Enable calibration application (used after calibration complete).
        """
        self.calibration_enabled = True
        if self.gaze_estimator:
            self.gaze_estimator.calibrated = True
        logger.info("Calibration enabled for gaze tracking")
    
    def get_calibration_info(self) -> dict:
        """
        Get current calibration status.
        """
        return {
            'enabled': self.calibration_enabled,
            'loaded': self.gaze_estimator.calibrated if self.gaze_estimator else False,
            'user_profile': self.user_profile,
            'running': self.is_running
        }

    def get_status(self) -> dict:
        """Get basic status of the camera stream."""
        return {
            'running': self.is_running,
            'fps': self.fps,
            'frame_count': self.frame_count,
            'camera_backend': self.face_detector.get_camera_backend() if self.face_detector.is_camera_initialized() else 'N/A'
        }

    def stop(self):
        """Stop camera stream."""
        self.is_running = False
        self.face_detector.release_camera()
        logger.info("Camera stream stopped")

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Process frame with face detection and gaze estimation.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Tuple of (processed_frame, analysis_data)
        """
        start_time = time.time()
        analysis_data = {
            'face_detected': False,
            'gaze_point': self.current_gaze,
            'blink_detected': False,
            'eye_openness': 1.0
        }
        
        # Detect face
        face_detected, landmarks_dict = self.face_detector.detect_face(frame)
        
        if not face_detected or landmarks_dict is None:
            self.is_face_detected = False
            self.processing_time = time.time() - start_time
            return frame, analysis_data
        
        self.is_face_detected = True
        face_landmarks = landmarks_dict['landmarks']

        # Optional: draw ALL 468 face landmarks for debugging
        if face_landmarks is not None:
            for idx, (x, y) in enumerate(face_landmarks):
                if idx % 2 == 0:  # Draw every 2nd point (reduce clutter)
                    cv2.circle(frame, (int(x), int(y)), 1, (0, 255, 255), -1)

        self.current_face_box = landmarks_dict['face_box']
        
        # Draw face bounding box
        face_box = self.current_face_box
        cv2.rectangle(
            frame,
            (face_box['x_min'], face_box['y_min']),
            (face_box['x_max'], face_box['y_max']),
            SystemConfig.FACE_BOX_COLOR,
            2
        )
        
        # Track eyes and estimate gaze
        try:
            eye_landmarks_dict = self.eye_tracker.extract_eye_landmarks(face_landmarks)
            
            if eye_landmarks_dict:
                # Calculate blink using eye aspect ratio
                left_ear = self.eye_tracker.calculate_eye_aspect_ratio(eye_landmarks_dict['left_eye'])
                right_ear = self.eye_tracker.calculate_eye_aspect_ratio(eye_landmarks_dict['right_eye'])
                
                # Get iris positions and eye corners
                left_iris = eye_landmarks_dict.get('left_iris')
                right_iris = eye_landmarks_dict.get('right_iris')
                left_corners = eye_landmarks_dict.get('left_corners')
                right_corners = eye_landmarks_dict.get('right_corners')
                
                # Estimate gaze using iris (primary) – head movement ignored
                raw_gaze = self.gaze_estimator.estimate_gaze_from_eyes(
                    left_iris, right_iris, left_corners, right_corners, frame.shape, face_landmarks
                )
                
                # ---- Blink detection with proper threshold ----
                avg_ear = (left_ear + right_ear) / 2.0
                BLINK_THRESHOLD = 0.22   # Adjust based on your camera (typical: 0.20 - 0.25)
                
                # Detect blink on the rising edge (eyes just closed)
                if avg_ear < BLINK_THRESHOLD and not self.blink_detected:
                    self.blink_detected = True
                    logger.info(f"🔴 BLINK DETECTED! EAR={avg_ear:.3f}")
                    try:
                        import pyautogui
                        pyautogui.click()
                        logger.info("   ✅ Click executed")
                    except Exception as e:
                        logger.error(f"Click failed: {e}")
                    # Small delay to avoid multiple clicks from the same blink
                    time.sleep(0.3)
                elif avg_ear > BLINK_THRESHOLD + 0.05:
                    # Reset when eyes are clearly open
                    self.blink_detected = False
                
                self.eye_openness = 1.0 - min(1.0, max(0.0, (BLINK_THRESHOLD - avg_ear) / BLINK_THRESHOLD))
                
                # ---- Cursor movement (only when not blinking) ----
                if not self.blink_detected:
                    # Apply smoothing and optional calibration
                    smoothed_gaze = self.gaze_estimator.apply_smoothing(raw_gaze)
                    
                    if self.calibration_enabled and self.gaze_estimator.calibrated:
                        calibrated_gaze = self.gaze_estimator.apply_calibration(smoothed_gaze)
                        final_gaze = calibrated_gaze
                    else:
                        final_gaze = smoothed_gaze
                    
                    # Simple stability filter (optional)
                    if not hasattr(self.gaze_estimator, '_stable_gaze'):
                        self.gaze_estimator._stable_gaze = final_gaze
                        self.gaze_estimator._stable_counter = 0
                    
                    dx = abs(final_gaze[0] - self.gaze_estimator._stable_gaze[0])
                    dy = abs(final_gaze[1] - self.gaze_estimator._stable_gaze[1])
                    movement = dx + dy
                    
                    if movement < 0.02:   # Very small movement -> keep previous stable position
                        self.current_gaze = self.gaze_estimator._stable_gaze
                    else:
                        self.gaze_estimator._stable_gaze = final_gaze
                        self.current_gaze = final_gaze
                
                # Draw gaze point on frame
                h, w, _ = frame.shape
                gaze_x = int(self.current_gaze[0] * w)
                gaze_y = int(self.current_gaze[1] * h)
                
                cv2.circle(
                    frame,
                    (gaze_x, gaze_y),
                    SystemConfig.GAZE_POINT_RADIUS,
                    SystemConfig.GAZE_POINT_COLOR,
                    -1
                )
        
        except Exception as e:
            logger.error(f"Error processing eyes: {e}")
        
        # Update analysis data
        analysis_data['face_detected'] = True
        analysis_data['gaze_point'] = self.current_gaze
        analysis_data['blink_detected'] = self.blink_detected
        analysis_data['eye_openness'] = self.eye_openness
        
        # Add FPS and status text
        self.processing_time = time.time() - start_time
        self._draw_stats(frame)
        
        return frame, analysis_data

    def _draw_stats(self, frame: np.ndarray):
        """Draw performance statistics on frame."""
        if SystemConfig.ENABLE_PERFORMANCE_MONITORING:
            # Calculate FPS
            current_time = time.time()
            delta = current_time - self.last_time
            if delta > 0:
                self.fps = 1.0 / delta
            self.last_time = current_time
            
            # Draw text
            h, w, _ = frame.shape
            y_offset = 30
            
            status_text = f"Face: {'✓' if self.is_face_detected else '✗'}"
            cv2.putText(frame, status_text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            fps_text = f"FPS: {self.fps:.1f}"
            cv2.putText(frame, fps_text, (10, y_offset + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            gaze_text = f"Gaze: ({self.current_gaze[0]:.2f}, {self.current_gaze[1]:.2f})"
            cv2.putText(frame, gaze_text, (10, y_offset + 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            blink_text = f"Blink: {'Yes' if self.blink_detected else 'No'}"
            cv2.putText(frame, blink_text, (w - 200, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def get_stream_generator(self) -> Generator:
        """
        Generate MJPEG stream for Flask.
        
        Yields:
            JPEG-encoded frame as bytes
        """
        frame_count = 0
        while self.is_running:
            try:
                if not self.face_detector.is_camera_initialized():
                    logger.error("Camera not initialized - cannot stream frames")
                    return
                
                ret, frame = self.face_detector.get_frame()
                
                if not ret:
                    if frame_count % 30 == 0:
                        logger.warning(f"Failed to read frame (count: {frame_count})")
                    continue
                
                if frame is None:
                    logger.warning("Frame is None")
                    continue
                
                # Process frame
                processed_frame, _ = self.process_frame(frame)
                
                if processed_frame is None:
                    logger.warning("Processed frame is None")
                    continue
                
                # Encode to JPEG
                ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    logger.warning("Failed to encode frame to JPEG")
                    continue
                
                frame_bytes = buffer.tobytes()
                
                # Yield in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                       frame_bytes + b'\r\n')
                
                frame_count += 1
                
                if frame_count == 1:
                    logger.info("First frame sent successfully")
                elif frame_count % 100 == 0:
                    logger.info(f"Frames sent: {frame_count}")
            
            except Exception as e:
                logger.error(f"Error in stream generator: {type(e).__name__}: {e}", exc_info=True)

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current processed frame."""
        ret, frame = self.face_detector.get_frame()
        if ret:
            processed_frame, _ = self.process_frame(frame)
            return processed_frame
        return None

    def get_analysis_data(self) -> Dict:
        """Get current analysis data."""
        return {
            'face_detected': self.is_face_detected,
            'gaze_point': self.current_gaze,
            'blink_detected': self.blink_detected,
            'eye_openness': self.eye_openness,
            'fps': self.fps,
            'processing_time': self.processing_time,
            'frame_count': self.frame_count
        }