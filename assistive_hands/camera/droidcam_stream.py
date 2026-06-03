"""Camera stream module - supports IP Webcam (network URL) and local cameras."""

import cv2
import numpy as np
import logging
import time
import threading

logger = logging.getLogger(__name__)


class SimpleCameraStream:
    """Camera stream that supports both IP Webcam (URL) and local cameras."""

    def __init__(self):
        self.cap = None
        self.camera_source = None   # Will be set from SystemConfig
        self.camera_index = 0       # Legacy attribute (kept for app.py references)
        self.is_running = False
        self._lock = threading.Lock()
        self._last_frame = None

    def _get_source(self):
        """Read camera source from SystemConfig at runtime."""
        try:
            from config.settings import SystemConfig
            return SystemConfig.CAMERA_DEVICE_INDEX
        except Exception:
            return 0  # fallback to default local cam

    def start(self):
        """Open camera or IP stream."""
        try:
            source = self._get_source()
            self.camera_source = source

            # Update legacy integer attribute for status reporting
            if isinstance(source, int):
                self.camera_index = source
            else:
                self.camera_index = -1   # -1 signals "network stream"

            logger.info(f"Opening camera source: {source}")

            # Release previous capture if any
            if self.cap:
                self.cap.release()
                time.sleep(0.3)

            # Choose backend based on source type
            if isinstance(source, str):
                # Network stream (IP Webcam / RTSP / HTTP)
                backends = [
                    ('FFMPEG', cv2.CAP_FFMPEG),
                    ('ANY', cv2.CAP_ANY),
                ]
            else:
                # Local webcam — try Windows backends first
                backends = [
                    ('DSHOW', cv2.CAP_DSHOW),
                    ('MSMF', cv2.CAP_MSMF),
                    ('ANY', cv2.CAP_ANY),
                ]

            for backend_name, backend_id in backends:
                try:
                    logger.info(f"Trying backend {backend_name} for source: {source}")
                    cap = cv2.VideoCapture(source, backend_id)

                    if not cap or not cap.isOpened():
                        logger.warning(f"Backend {backend_name}: could not open source.")
                        continue

                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FPS, 30)

                    # Warm-up: read a few frames to confirm stream is live
                    ok = False
                    for _ in range(8):
                        ret, frm = cap.read()
                        if ret and frm is not None and frm.size > 0:
                            ok = True
                            break
                        time.sleep(0.1)

                    if not ok:
                        logger.warning(f"Backend {backend_name}: frames not readable after warm-up.")
                        cap.release()
                        continue

                    self.cap = cap
                    self.is_running = True
                    logger.info(f"Camera started with backend {backend_name}, source: {source}")
                    return True

                except Exception as e:
                    logger.error(f"Backend {backend_name} error: {e}", exc_info=True)
                    continue

            logger.error("All backends failed. Camera could not be opened.")
            self.is_running = False
            return False

        except Exception as e:
            logger.error(f"Camera start error: {e}", exc_info=True)
            self.is_running = False
            return False

    def get_frame(self):
        """Return JPEG-encoded frame bytes. Auto-reconnects on stream failure."""
        with self._lock:
            if self.cap is None or not self.cap.isOpened():
                logger.warning("Camera not open – attempting restart...")
                self.start()

            frame = None
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    self._fail_count = 0          # reset on success
                    self._last_frame = frame
                else:
                    self._fail_count = getattr(self, '_fail_count', 0) + 1
                    # After 10 consecutive failures (~0.33s), force reconnect
                    if self._fail_count >= 10:
                        logger.warning(f"Stream lost after {self._fail_count} failures – reconnecting...")
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                        self.cap = None
                        self.is_running = False
                        self._fail_count = 0
                        self.start()
                    # Use last good frame while reconnecting
                    frame = self._last_frame

            if frame is None:
                frame = self._error_frame(
                    "No frame received",
                    "Check IP Webcam stream",
                    "Both devices on same WiFi?"
                )

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                return buffer.tobytes()
            else:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                _, buf = cv2.imencode('.jpg', blank)
                return buf.tobytes()

    def _error_frame(self, line1, line2="", line3=""):
        """Generate a dark error frame with helpful text."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (30, 30, 50)  # Dark blue-ish background

        # Red warning icon area
        cv2.rectangle(frame, (250, 80), (390, 140), (0, 0, 180), -1)
        cv2.putText(frame, "! CAMERA ERROR", (258, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Error lines
        y = 180
        for line in [line1, line2, line3]:
            if line:
                cv2.putText(frame, line, (60, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 1)
                y += 40
        return frame

    def generate_mjpeg(self):
        """Yield MJPEG frames for Flask Response."""
        while True:
            try:
                frame_bytes = self.get_frame()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                       + frame_bytes + b'\r\n')
                time.sleep(0.033)   # ~30 fps
            except Exception as e:
                logger.error(f"MJPEG generation error: {e}")
                time.sleep(0.1)

    def stop(self):
        """Release camera."""
        self.is_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        logger.info("Camera stream stopped.")


# Singleton used by app.py: from camera.droidcam_stream import droidcam
droidcam = SimpleCameraStream()
