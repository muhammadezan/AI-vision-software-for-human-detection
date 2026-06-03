"""Script to detect available cameras and DroidCam."""

import cv2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_available_cameras():
    """Detect all available camera devices."""
    available_cameras = []
    
    # Try device indices 0-10
    for device_index in range(10):
        cap = cv2.VideoCapture(device_index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                available_cameras.append({
                    'index': device_index,
                    'resolution': f"{width}x{height}",
                    'working': True
                })
                logger.info(f"✓ Camera {device_index}: {width}x{height}")
            cap.release()
    
    return available_cameras


def identify_droidcam(cameras):
    """Try to identify which camera is DroidCam."""
    if not cameras:
        return None
    
    # DroidCam is usually the last camera (highest index)
    # or one of the higher indices
    for cam in reversed(cameras):
        logger.info(f"\nTrying camera index {cam['index']}...")
        cap = cv2.VideoCapture(cam['index'])
        if cap.isOpened():
            # Try to read a frame
            for _ in range(10):
                ret, frame = cap.read()
                if ret:
                    logger.info(f"  → Camera {cam['index']} frame read successfully")
                    cap.release()
                    return cam['index']
            cap.release()
    
    return cameras[-1]['index'] if cameras else None


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Detecting available cameras...")
    logger.info("=" * 50)
    
    cameras = detect_available_cameras()
    
    if not cameras:
        logger.error("No cameras detected!")
        exit(1)
    
    logger.info(f"\n✓ Found {len(cameras)} camera(s)")
    
    logger.info("\n" + "=" * 50)
    logger.info("Identifying DroidCam...")
    logger.info("=" * 50)
    
    droidcam_index = identify_droidcam(cameras)
    
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Available cameras: {len(cameras)}")
    for cam in cameras:
        is_droid = " (LIKELY DROIDCAM)" if cam['index'] == droidcam_index else ""
        logger.info(f"  Index {cam['index']}: {cam['resolution']}{is_droid}")
    
    logger.info("\n🎯 RECOMMENDATION:")
    logger.info(f"  Update CAMERA_DEVICE_INDEX to: {droidcam_index}")
    logger.info(f"  File: config/settings.py")
    logger.info(f"  Change: CAMERA_DEVICE_INDEX = {droidcam_index}")
