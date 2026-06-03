# range_finder.py
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options
import time

base_opts = base_options.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(base_options=base_opts,
    running_mode=vision.RunningMode.VIDEO, num_faces=1)
face_landmarker = vision.FaceLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
last_ts = 0

ix_min, ix_max = 1.0, 0.0
iy_min, iy_max = 1.0, 0.0

print("Aankhein hilao — 4 corners dekho, phir Q dabao")
print("LEFT → RIGHT → TOP → BOTTOM → phir Q\n")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret: continue
    
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    
    ts = int(time.time() * 1000)
    if ts <= last_ts: ts = last_ts + 1
    last_ts = ts
    
    result = face_landmarker.detect_for_video(mp_img, ts)
    
    if result.face_landmarks and len(result.face_landmarks[0]) >= 478:
        lm = result.face_landmarks[0]
        
        l_xmin = min(lm[33].x, lm[133].x)
        l_xmax = max(lm[33].x, lm[133].x)
        r_xmin = min(lm[362].x, lm[263].x)
        r_xmax = max(lm[362].x, lm[263].x)
        l_ymin = min(lm[159].y, lm[145].y)
        l_ymax = max(lm[159].y, lm[145].y)
        r_ymin = min(lm[386].y, lm[374].y)
        r_ymax = max(lm[386].y, lm[374].y)
        
        lg_x = (lm[468].x - l_xmin) / (l_xmax - l_xmin + 1e-6)
        lg_y = (lm[468].y - l_ymin) / (l_ymax - l_ymin + 1e-6)
        rg_x = (lm[473].x - r_xmin) / (r_xmax - r_xmin + 1e-6)
        rg_y = (lm[473].y - r_ymin) / (r_ymax - r_ymin + 1e-6)
        
        avg_x = (lg_x + rg_x) / 2.0
        avg_y = (lg_y + rg_y) / 2.0
        
        if avg_x < ix_min: ix_min = avg_x
        if avg_x > ix_max: ix_max = avg_x
        if avg_y < iy_min: iy_min = avg_y
        if avg_y > iy_max: iy_max = avg_y
        
        frame_count += 1
        
        cv2.putText(frame, f"iris_x: {avg_x:.3f}  range:[{ix_min:.3f},{ix_max:.3f}]",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.putText(frame, f"iris_y: {avg_y:.3f}  range:[{iy_min:.3f},{iy_max:.3f}]",
                    (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.putText(frame, "LOOK: corners + edges, then press Q",
                    (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,255), 1)
    
    cv2.imshow("Range Finder", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n=== AAPKI ACTUAL RANGE ===")
print(f"IRIS_X_MIN = {ix_min:.3f}")
print(f"IRIS_X_MAX = {ix_max:.3f}")
print(f"IRIS_Y_MIN = {iy_min:.3f}")
print(f"IRIS_Y_MAX = {iy_max:.3f}")
print(f"\nYe values app.py mein paste karo!")