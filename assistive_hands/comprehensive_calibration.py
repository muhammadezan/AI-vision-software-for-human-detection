#!/usr/bin/env python3
"""
COMPREHENSIVE CALIBRATION
- Full eye gaze range (9 positions: center, left, right, up, down, 4 diagonals)
- Full head movement range (9 positions: same as above)
- Face baseline measurements
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options
import time
import numpy as np

base_opts = base_options.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_opts,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
last_ts = 0

# ============================================================================
# STEP 1: EYES CALIBRATION — 9 gaze positions
# ============================================================================
print("\n" + "="*70)
print("STEP 1: EYES FULL RANGE CALIBRATION")
print("="*70)
print("""
Gaze position tracker — ek-ek direction mein 30 frames collect karega:

  ↖  ↑  ↗      Instructions:
  ←  ●  →      1. Press '1' → Look CENTER (relaxed)
  ↙  ↓  ↙      2. Press '2' → Look FAR LEFT (extreme left)
               3. Press '3' → Look FAR RIGHT (extreme right)
               4. Press '4' → Look UP (extreme up)
               5. Press '5' → Look DOWN (extreme down)
               6. Press '6' → Look UP-LEFT diagonal
               7. Press '7' → Look UP-RIGHT diagonal
               8. Press '8' → Look DOWN-LEFT diagonal
               9. Press '9' → Look DOWN-RIGHT diagonal
               SPACE → Next position, Q → Quit, C → Show results
""")

# Gaze positions collection
gaze_data = {
    '1': {'name': 'CENTER', 'iris': []},
    '2': {'name': 'LEFT', 'iris': []},
    '3': {'name': 'RIGHT', 'iris': []},
    '4': {'name': 'UP', 'iris': []},
    '5': {'name': 'DOWN', 'iris': []},
    '6': {'name': 'UP-LEFT', 'iris': []},
    '7': {'name': 'UP-RIGHT', 'iris': []},
    '8': {'name': 'DOWN-LEFT', 'iris': []},
    '9': {'name': 'DOWN-RIGHT', 'iris': []},
}

current_gaze = None
gaze_frame_count = 0
gaze_complete = set()

print("Press 1-9 to select gaze position, or Q to skip to head calibration\n")

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
        
        # Collect if in a position
        if current_gaze:
            gaze_data[current_gaze]['iris'].append((avg_x, avg_y))
            gaze_frame_count += 1
        
        # Display
        status = f"Position: {current_gaze} - {gaze_data[current_gaze]['name'] if current_gaze else 'NONE'}"
        if current_gaze:
            status += f" ({gaze_frame_count}/30)"
        
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Iris: ({avg_x:.3f}, {avg_y:.3f})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        complete_str = f"Completed: {len(gaze_complete)}/9"
        cv2.putText(frame, complete_str, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, "Press 1-9 (pos), SPACE (next), Q (skip), C (results)", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    cv2.imshow("Eyes Calibration", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7'), ord('8'), ord('9')]:
        key_str = chr(key)
        current_gaze = key_str
        gaze_frame_count = 0
        gaze_data[key_str]['iris'] = []  # reset
        print(f"Starting {gaze_data[key_str]['name']} gaze collection...")
    elif key == ord(' '):
        if current_gaze and gaze_frame_count >= 30:
            gaze_complete.add(current_gaze)
            print(f"✓ {gaze_data[current_gaze]['name']} saved ({len(gaze_data[current_gaze]['iris'])} frames)")
            current_gaze = None
            gaze_frame_count = 0
        else:
            print(f"Need 30 frames, have {gaze_frame_count}")
    elif key == ord('c'):
        print("\nEyes Calibration Results so far:")
        for pos in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if gaze_data[pos]['iris']:
                xs = [x for x, y in gaze_data[pos]['iris']]
                ys = [y for x, y in gaze_data[pos]['iris']]
                print(f"  {pos} ({gaze_data[pos]['name']:10s}): X=[{min(xs):.3f}, {max(xs):.3f}]  Y=[{min(ys):.3f}, {max(ys):.3f}]")

cv2.destroyAllWindows()

# Calculate eye statistics
print("\n" + "="*70)
print("EYES CALIBRATION SUMMARY")
print("="*70)

eye_ranges = {}
for pos, data in gaze_data.items():
    if data['iris']:
        xs = [x for x, y in data['iris']]
        ys = [y for x, y in data['iris']]
        eye_ranges[pos] = {
            'x_min': min(xs),
            'x_max': max(xs),
            'y_min': min(ys),
            'y_max': max(ys),
            'x_avg': np.mean(xs),
            'y_avg': np.mean(ys),
        }
        print(f"{pos} ({data['name']:10s}): X_range=[{eye_ranges[pos]['x_min']:.3f}-{eye_ranges[pos]['x_max']:.3f}]  Y_range=[{eye_ranges[pos]['y_min']:.3f}-{eye_ranges[pos]['y_max']:.3f}]")

# Overall iris range
if eye_ranges:
    all_x_min = min(d['x_min'] for d in eye_ranges.values())
    all_x_max = max(d['x_max'] for d in eye_ranges.values())
    all_y_min = min(d['y_min'] for d in eye_ranges.values())
    all_y_max = max(d['y_max'] for d in eye_ranges.values())
    
    print(f"\nOVERALL IRIS RANGE:")
    print(f"  IRIS_X_MIN = {all_x_min:.3f}  (far left)")
    print(f"  IRIS_X_MAX = {all_x_max:.3f}  (far right)")
    print(f"  IRIS_Y_MIN = {all_y_min:.3f}  (up)")
    print(f"  IRIS_Y_MAX = {all_y_max:.3f}  (down)")

# ============================================================================
# STEP 2: HEAD CALIBRATION — 9 head positions
# ============================================================================

print("\n" + "="*70)
print("STEP 2: HEAD MOVEMENT CALIBRATION")
print("="*70)
print("""
Head position tracker — ek-ek direction mein 30 frames:

  ↖  ↑  ↗      Instructions:
  ←  ●  →      1. Press '1' → Head STRAIGHT (relaxed, looking center)
  ↙  ↓  ↙      2. Press '2' → Head FAR LEFT (extreme left)
               3. Press '3' → Head FAR RIGHT (extreme right)
               4. Press '4' → Head UP (extreme up)
               5. Press '5' → Head DOWN (extreme down)
               6. Press '6' → Head UP-LEFT diagonal
               7. Press '7' → Head UP-RIGHT diagonal
               8. Press '8' → Head DOWN-LEFT diagonal
               9. Press '9' → Head DOWN-RIGHT diagonal
               SPACE → Next position, Q → Quit, C → Show results
""")

# Head positions collection
head_data = {
    '1': {'name': 'STRAIGHT', 'nose': [], 'forehead': [], 'chin': []},
    '2': {'name': 'LEFT', 'nose': [], 'forehead': [], 'chin': []},
    '3': {'name': 'RIGHT', 'nose': [], 'forehead': [], 'chin': []},
    '4': {'name': 'UP', 'nose': [], 'forehead': [], 'chin': []},
    '5': {'name': 'DOWN', 'nose': [], 'forehead': [], 'chin': []},
    '6': {'name': 'UP-LEFT', 'nose': [], 'forehead': [], 'chin': []},
    '7': {'name': 'UP-RIGHT', 'nose': [], 'forehead': [], 'chin': []},
    '8': {'name': 'DOWN-LEFT', 'nose': [], 'forehead': [], 'chin': []},
    '9': {'name': 'DOWN-RIGHT', 'nose': [], 'forehead': [], 'chin': []},
}

current_head = None
head_frame_count = 0
head_complete = set()

print("Press 1-9 to select head position, or Q to finish\n")

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
        
        # Nose tip
        nose_x = lm[1].x
        nose_y = lm[1].y
        
        # Forehead center (average of forehead landmarks)
        forehead_x = np.mean([lm[i].x for i in [10, 67, 69, 104, 108, 109, 151]])
        forehead_y = np.mean([lm[i].y for i in [10, 67, 69, 104, 108, 109, 151]])
        
        # Chin
        chin_x = lm[152].x
        chin_y = lm[152].y
        
        # Collect if in a position
        if current_head:
            head_data[current_head]['nose'].append((nose_x, nose_y))
            head_data[current_head]['forehead'].append((forehead_x, forehead_y))
            head_data[current_head]['chin'].append((chin_x, chin_y))
            head_frame_count += 1
        
        # Display
        status = f"Head: {current_head} - {head_data[current_head]['name'] if current_head else 'NONE'}"
        if current_head:
            status += f" ({head_frame_count}/30)"
        
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Nose: ({nose_x:.3f}, {nose_y:.3f})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.putText(frame, f"Forehead: ({forehead_x:.3f}, {forehead_y:.3f})", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)
        cv2.putText(frame, f"Chin: ({chin_x:.3f}, {chin_y:.3f})", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
        
        complete_str = f"Completed: {len(head_complete)}/9"
        cv2.putText(frame, complete_str, (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, "Press 1-9 (pos), SPACE (next), Q (finish), C (results)", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    cv2.imshow("Head Calibration", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7'), ord('8'), ord('9')]:
        key_str = chr(key)
        current_head = key_str
        head_frame_count = 0
        head_data[key_str]['nose'] = []
        head_data[key_str]['forehead'] = []
        head_data[key_str]['chin'] = []
        print(f"Starting {head_data[key_str]['name']} head collection...")
    elif key == ord(' '):
        if current_head and head_frame_count >= 30:
            head_complete.add(current_head)
            print(f"✓ {head_data[current_head]['name']} saved ({len(head_data[current_head]['nose'])} frames)")
            current_head = None
            head_frame_count = 0
        else:
            print(f"Need 30 frames, have {head_frame_count}")
    elif key == ord('c'):
        print("\nHead Calibration Results so far:")
        for pos in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if head_data[pos]['nose']:
                noses_x = [x for x, y in head_data[pos]['nose']]
                noses_y = [y for x, y in head_data[pos]['nose']]
                print(f"  {pos} ({head_data[pos]['name']:10s}): Nose X=[{min(noses_x):.3f}, {max(noses_x):.3f}]  Y=[{min(noses_y):.3f}, {max(noses_y):.3f}]")

cap.release()
cv2.destroyAllWindows()

# Calculate head statistics
print("\n" + "="*70)
print("HEAD CALIBRATION SUMMARY")
print("="*70)

head_ranges = {}
for pos, data in head_data.items():
    if data['nose']:
        noses_x = [x for x, y in data['nose']]
        noses_y = [y for x, y in data['nose']]
        heads_x = [x for x, y in data['forehead']]
        heads_y = [y for x, y in data['forehead']]
        chins_x = [x for x, y in data['chin']]
        chins_y = [y for x, y in data['chin']]
        
        head_ranges[pos] = {
            'nose_x': (min(noses_x), max(noses_x), np.mean(noses_x)),
            'nose_y': (min(noses_y), max(noses_y), np.mean(noses_y)),
            'forehead_x': (min(heads_x), max(heads_x), np.mean(heads_x)),
            'forehead_y': (min(heads_y), max(heads_y), np.mean(heads_y)),
            'chin_x': (min(chins_x), max(chins_x), np.mean(chins_x)),
            'chin_y': (min(chins_y), max(chins_y), np.mean(chins_y)),
        }
        print(f"{pos} ({data['name']:10s}):")
        print(f"    Nose:     X=[{head_ranges[pos]['nose_x'][0]:.3f}-{head_ranges[pos]['nose_x'][1]:.3f}] (avg={head_ranges[pos]['nose_x'][2]:.3f})")
        print(f"              Y=[{head_ranges[pos]['nose_y'][0]:.3f}-{head_ranges[pos]['nose_y'][1]:.3f}] (avg={head_ranges[pos]['nose_y'][2]:.3f})")

# Get straight position baseline
if '1' in head_ranges:
    straight_nose_x = head_ranges['1']['nose_x'][2]
    straight_nose_y = head_ranges['1']['nose_y'][2]
    print(f"\nSTRAIGHT BASELINE:")
    print(f"  NOSE_CENTER_X = {straight_nose_x:.3f}")
    print(f"  NOSE_CENTER_Y = {straight_nose_y:.3f}")

# Overall head range
if head_ranges:
    all_nose_x_min = min(d['nose_x'][0] for d in head_ranges.values())
    all_nose_x_max = max(d['nose_x'][1] for d in head_ranges.values())
    all_nose_y_min = min(d['nose_y'][0] for d in head_ranges.values())
    all_nose_y_max = max(d['nose_y'][1] for d in head_ranges.values())
    
    print(f"\nOVERALL HEAD RANGE:")
    print(f"  NOSE_X: [{all_nose_x_min:.3f}, {all_nose_x_max:.3f}]")
    print(f"  NOSE_Y: [{all_nose_y_min:.3f}, {all_nose_y_max:.3f}]")
    print(f"  SENSITIVITY_X = {(all_nose_x_max - all_nose_x_min):.3f}")
    print(f"  SENSITIVITY_Y = {(all_nose_y_max - all_nose_y_min):.3f}")

print("\n" + "="*70)
print("COPY YE VALUES APP.PY MEIN!")
print("="*70)
