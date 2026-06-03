import cv2
import mediapipe as mp
import numpy as np
import logging
import os
import time

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_camera_debug():
    """
    A standalone script to debug camera and MediaPipe face detection.
    """
    logging.info("Starting camera debug script...")

    # --- 1. Initialize MediaPipe Face Landmarker ---
    model_path = 'models/face_landmarker.task'
    landmarker = None
    try:
        if not os.path.exists(model_path):
            logging.error(f"Model file not found at '{model_path}'.")
            logging.error("Please ensure the model is downloaded and in the correct directory.")
            return

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        landmarker = vision.FaceLandmarker.create_from_options(options)
        logging.info("MediaPipe Face Landmarker initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize MediaPipe Landmarker: {e}", exc_info=True)
        return

    # --- 2. Initialize Camera ---
    cap = None
    camera_index = 0
    backends = {
        'DSHOW': cv2.CAP_DSHOW,
        'MSMF': cv2.CAP_MSMF,
        'ANY': cv2.CAP_ANY,
    }

    for backend_name, backend_id in backends.items():
        try:
            logging.info(f"--- Trying backend: {backend_name} ({backend_id}) ---")
            cap = cv2.VideoCapture(camera_index, backend_id)
            if not cap or not cap.isOpened():
                logging.error(f"Cannot open camera with {backend_name} backend.")
                continue
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logging.info(f"Camera opened with {backend_name}. Reading frames for 3 seconds to allow auto-exposure to adjust...")
            
            frame = None
            start_time = time.time()
            while time.time() - start_time < 3:
                ret, current_frame = cap.read()
                if ret:
                    frame = current_frame # Keep the latest valid frame
                time.sleep(0.03) # ~30 fps

            if frame is None:
                logging.error(f"Failed to grab any valid frame within 3 seconds with {backend_name} backend.")
                cap.release()
                continue

            logging.info(f"Frame grabbed successfully with {backend_name} after warm-up. Shape: {frame.shape}")

            # Save the frame for inspection
            debug_image_path = f'debug_frame_{backend_name}.jpg'
            cv2.imwrite(debug_image_path, frame)
            logging.info(f"Frame saved for debugging to: {os.path.abspath(debug_image_path)}")

            # If we got a good frame, we can stop trying backends
            logging.info(f"Successfully captured image with {backend_name}. Proceeding to detection.")
            break # Exit the loop

        except Exception as e:
            logging.error(f"An error occurred with {backend_name} backend: {e}", exc_info=True)
            if cap:
                cap.release()
            continue
    
    if frame is None:
        logging.error("Could not capture a frame with any available backend. Exiting.")
        return

    # Release the final capture object if it's still open
    if cap and cap.isOpened():
        cap.release()
        logging.info("Final camera object released.")

    logging.info(f"Frame grabbed successfully. Shape: {frame.shape}, Dtype: {frame.dtype}")

    # --- SAVE THE FRAME FOR VISUAL INSPECTION ---
    try:
        debug_image_path = 'debug_frame.jpg'
        cv2.imwrite(debug_image_path, frame)
        logging.info(f"Frame saved for debugging to: {os.path.abspath(debug_image_path)}")
    except Exception as e:
        logging.error(f"Could not save debug frame: {e}")

    # --- 4. Run Face Detection ---
    try:
        logging.info("Converting frame to MediaPipe Image format...")
        # The frame from OpenCV is in BGR format. Convert it to RGB.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create a MediaPipe Image object.
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        logging.info("Running detection...")
        detection_result = landmarker.detect(mp_image)

        # --- 5. Report Results ---
        if detection_result and detection_result.face_landmarks:
            logging.info("SUCCESS: Face detected!")
            logging.info(f"Number of faces found: {len(detection_result.face_landmarks)}")
            # You can add more details here if needed, e.g., landmark coordinates
        else:
            logging.warning("FAILURE: No face detected in the frame.")

    except Exception as e:
        logging.error(f"An error occurred during face detection: {e}", exc_info=True)

if __name__ == '__main__':
    run_camera_debug()
