"""Debug gaze coordinates before sending to cursor"""

import sys
import time
import cv2
import mediapipe as mp
import numpy as np
import pyautogui

print("=" * 60)
print("GAZE COORDINATE DEBUGGER")
print("=" * 60)

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Screen dimensions
screen_w, screen_h = pyautogui.size()
print(f"Screen: {screen_w} x {screen_h}")

# Tracking variables
reference_face_center = None
sensitivity_x = 18.0
sensitivity_y = 15.0
frame_count = 0

print("\n🎯 Tracking started...")
print("Move your head to see coordinates")
print("Press 'q' to quit\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    
    if results.multi_face_landmarks:
        # Get landmarks
        face_landmarks = results.multi_face_landmarks[0]
        landmarks = []
        for lm in face_landmarks.landmark:
            landmarks.append([lm.x * w, lm.y * h])
        landmarks = np.array(landmarks)
        
        # Face bounding box
        face_min_x = np.min(landmarks[:, 0])
        face_max_x = np.max(landmarks[:, 0])
        face_min_y = np.min(landmarks[:, 1])
        face_max_y = np.max(landmarks[:, 1])
        
        face_center_x = (face_min_x + face_max_x) / 2
        face_center_y = (face_min_y + face_max_y) / 2
        
        # Set reference
        if reference_face_center is None:
            reference_face_center = (face_center_x, face_center_y)
            print("\n✓ REFERENCE SET! Now move your head\n")
        
        # Calculate head movement
        head_delta_x = (face_center_x - reference_face_center[0]) / w
        head_delta_y = (face_center_y - reference_face_center[1]) / h
        
        # Calculate gaze (0-1 range)
        gaze_x = 0.5 + (head_delta_x * sensitivity_x)
        gaze_y = 0.5 + (head_delta_y * sensitivity_y)
        
        # Clamp
        gaze_x = max(0.0, min(1.0, gaze_x))
        gaze_y = max(0.0, min(1.0, gaze_y))
        
        # Screen coordinates
        screen_x = int(gaze_x * screen_w)
        screen_y = int(gaze_y * screen_h)
        
        # MOVE CURSOR
        try:
            pyautogui.moveTo(screen_x, screen_y, duration=0)
            
            # Print every 30 frames
            if frame_count % 30 == 0:
                print(f"Head delta: ({head_delta_x:+.3f}, {head_delta_y:+.3f}) → Gaze: ({gaze_x:.2f}, {gaze_y:.2f}) → Cursor: ({screen_x}, {screen_y})")
            
        except Exception as e:
            print(f"❌ Cursor error: {e}")
        
        # Draw on frame
        cv2.rectangle(frame, (int(face_min_x), int(face_min_y)), 
                     (int(face_max_x), int(face_max_y)), (0, 255, 0), 2)
        
        gaze_point_x = int(gaze_x * w)
        gaze_point_y = int(gaze_y * h)
        cv2.circle(frame, (gaze_point_x, gaze_point_y), 8, (0, 0, 255), -1)
        
        status = f"Cursor: ({screen_x}, {screen_y})"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
    else:
        reference_face_center = None
        cv2.putText(frame, "NO FACE DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    cv2.imshow("Debug - Gaze to Cursor", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\n✓ Debug complete")