#!/usr/bin/env python3
"""
DIAGNOSTIC — Auto finds model path, tests raw landmark values
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options
import time
import os
import sys

# ── Auto-find model ───────────────────────────────────────────────────────────
def find_model():
    candidates = [
        'models/face_landmarker.task',
        '../models/face_landmarker.task',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'face_landmarker.task'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'face_landmarker.task'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)

    # Walk from script directory upward
    start = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(start):
        dirs[:] = [d for d in dirs if d not in ['.venv','venv','node_modules','__pycache__','.git']]
        if 'face_landmarker.task' in files:
            return os.path.join(root, 'face_landmarker.task')
    return None

MODEL_PATH = find_model()
if MODEL_PATH is None:
    print("\n❌ face_landmarker.task not found!")
    print("   Download from:")
    print("   https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
    print("   Save to: assistive_hands\\models\\face_landmarker.task")
    input("\nPress Enter to exit...")
    sys.exit(1)

print(f"✓ Model: {MODEL_PATH}")

opts = vision.FaceLandmarkerOptions(
    base_options=base_options.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,
)
detector = vision.FaceLandmarker.create_from_options(opts)

cap = cv2.VideoCapture(0)
last_ts = 0

print("\n" + "="*60)
print("Move head LEFT and RIGHT — watch the 3 values")
print("Tell me: which value goes DOWN when you move LEFT?")
print("Press Q to quit")
print("="*60 + "\n")

while True:
    ok, frame = cap.read()
    if not ok:
        continue

    frame_flip = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    def run(f, offset=0):
        global last_ts
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(time.time() * 1000) + offset
        if ts <= last_ts:
            ts = last_ts + 1
        last_ts = ts
        return detector.detect_for_video(img, ts)

    r1 = run(frame, 0)
    r2 = run(frame_flip, 1)

    raw  = r1.face_landmarks[0][1].x if r1.face_landmarks and len(r1.face_landmarks[0]) >= 5 else None
    flip = r2.face_landmarks[0][1].x if r2.face_landmarks and len(r2.face_landmarks[0]) >= 5 else None

    display = frame_flip.copy()

    if raw is not None and flip is not None:
        cv2.putText(display, f"flip      = {flip:.3f}  (flipped before detect)",
                    (10, 40),  cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 100), 2)
        cv2.putText(display, f"raw       = {raw:.3f}  (no flip)",
                    (10, 80),  cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)
        cv2.putText(display, f"1 - raw   = {1-raw:.3f}  (inverted)",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 140, 255), 2)
        cv2.putText(display, "Move head LEFT/RIGHT slowly",
                    (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,180), 1)

        print(f"flip={flip:.3f}   raw={raw:.3f}   1-raw={1-raw:.3f}")

    cv2.imshow("DIAGNOSTIC", display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\nPaste output + tell me which value matched LEFT movement")
