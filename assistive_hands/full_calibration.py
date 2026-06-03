#!/usr/bin/env python3
"""
FULL CALIBRATION — Nose center + eyes + face ko measure karo
Straight camera ke saamne baith ke — NO head movement, ONLY eyes
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options
import time

base_opts = base_options.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_opts,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
last_ts = 0

# Eye extremes tracking
eye_x_min, eye_x_max = 1.0, 0.0
eye_y_min, eye_y_max = 1.0, 0.0

# Nose center tracking
nose_x_vals, nose_y_vals = [], []

print("="*60)
print("FULL CALIBRATION")
print("="*60)
print("\n[Step 1/2] EYES CALIBRATION (30 frames)")
print("Seedha camera ke saamne baith ke:")
print("  → LEFT: look far left (1-2 sec)")
print("  → RIGHT: look far right (1-2 sec)")  
print("  → UP: look up (1-2 sec)")
print("  → DOWN: look down (1-2 sec)")
print("Press SPACE when ready, Q to quit\n")

step = 1
frame_count = 0
space_pressed = False

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    
    ts = int(time.time() * 1000)
    if ts <= last_ts:
        ts = last_ts + 1
    last_ts = ts
    
    result = face_landmarker.detect_for_video(mp_img, ts)
    
    if result.face_landmarks and len(result.face_landmarks[0]) >= 478:
        lm = result.face_landmarks[0]
        
        # Eye box calculation
        l_xmin = min(lm[33].x, lm[133].x)
        l_xmax = max(lm[33].x, lm[133].x)
        r_xmin = min(lm[362].x, lm[263].x)
        r_xmax = max(lm[362].x, lm[263].x)
        l_ymin = min(lm[159].y, lm[145].y)
        l_ymax = max(lm[159].y, lm[145].y)
        r_ymin = min(lm[386].y, lm[374].y)
        r_ymax = max(lm[386].y, lm[374].y)
        
        # Iris position
        lg_x = (lm[468].x - l_xmin) / (l_xmax - l_xmin + 1e-6)
        lg_y = (lm[468].y - l_ymin) / (l_ymax - l_ymin + 1e-6)
        rg_x = (lm[473].x - r_xmin) / (r_xmax - r_xmin + 1e-6)
        rg_y = (lm[473].y - r_ymin) / (r_ymax - r_ymin + 1e-6)
        
        avg_x = (lg_x + rg_x) / 2.0
        avg_y = (lg_y + rg_y) / 2.0
        
        # Nose center
        nose_x = lm[1].x
        nose_y = lm[1].y
        
        # Track ranges for step 1 (eyes)
        if step == 1:
            if eye_x_min > avg_x:
                eye_x_min = avg_x
            if eye_x_max < avg_x:
                eye_x_max = avg_x
            if eye_y_min > avg_y:
                eye_y_min = avg_y
            if eye_y_max < avg_y:
                eye_y_max = avg_y
            frame_count += 1
        
        # Track nose center for step 2
        if step == 2 and space_pressed:
            nose_x_vals.append(nose_x)
            nose_y_vals.append(nose_y)
            frame_count += 1
        
        # Display
        cv2.putText(frame, f"[STEP {step}] iris_x: {avg_x:.3f} [{eye_x_min:.3f},{eye_x_max:.3f}]",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"[STEP {step}] iris_y: {avg_y:.3f} [{eye_y_min:.3f},{eye_y_max:.3f}]",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"nose: ({nose_x:.3f}, {nose_y:.3f})",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        if step == 1:
            cv2.putText(frame, f"Frames collected: {frame_count}/300",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, "Press SPACE when done looking around",
                        (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
        else:
            cv2.putText(frame, f"Nose center frames: {frame_count}/60",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, "Baith ja seedha camera ke saamne",
                        (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
    
    cv2.imshow("Full Calibration", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        if step == 1:
            print(f"\n✓ Eyes calibration done! ({frame_count} frames)")
            print("Now moving to NOSE CENTER calibration...")
            print("Baith ja seedha camera ke saamne — NO head movement")
            print("Press SPACE again to start nose collection\n")
            step = 2
            frame_count = 0
        elif step == 2 and not space_pressed:
            space_pressed = True
            print("Nose collection started... (60 frames)")
        elif step == 2 and space_pressed and frame_count >= 60:
            print("\n✓ Nose calibration done!")
            break

cap.release()
cv2.destroyAllWindows()

# Calculate nose center
if nose_x_vals and nose_y_vals:
    nose_center_x = sum(nose_x_vals) / len(nose_x_vals)
    nose_center_y = sum(nose_y_vals) / len(nose_y_vals)
else:
    nose_center_x = 0.5
    nose_center_y = 0.5

print("\n" + "="*60)
print("CALIBRATION RESULTS")
print("="*60)
print(f"\n[EYES RANGE]")
print(f"IRIS_X_MIN = {eye_x_min:.3f}")
print(f"IRIS_X_MAX = {eye_x_max:.3f}")
print(f"IRIS_Y_MIN = {eye_y_min:.3f}")
print(f"IRIS_Y_MAX = {eye_y_max:.3f}")
print(f"\n[NOSE CENTER] (seedha camera ke saamne)")
print(f"NOSE_CENTER_X = {nose_center_x:.3f}")
print(f"NOSE_CENTER_Y = {nose_center_y:.3f}")
print(f"\nYe values app.py mein paste karo!")
print("="*60)
