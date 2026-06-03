import cv2
import time
import numpy as np

# Mock implementation to bypass mediapipe issues if they persist
# but let's try a better import first
try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
except Exception as e:
    print(f"Mediapipe init error: {e}")
    face_mesh = None

def calculate_ear(eye_landmarks, landmarks):
    def dist(p1_idx, p2_idx):
        p1 = landmarks[p1_idx]
        p2 = landmarks[p2_idx]
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    v1 = dist(eye_landmarks[1], eye_landmarks[5])
    v2 = dist(eye_landmarks[2], eye_landmarks[4])
    h = dist(eye_landmarks[0], eye_landmarks[3])
    return (v1 + v2) / (2.0 * h)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

cap = cv2.VideoCapture(0)
print("BLINK DEBUG STARTING - LOOK AT CAMERA AND BLINK")
start_time = time.time()
blink_count = 0
threshold = 0.2

try:
    while time.time() - start_time < 20:
        ret, frame = cap.read()
        if not ret: 
            print("Failed to capture frame")
            time.sleep(1)
            continue
        
        if face_mesh:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                ear_l = calculate_ear(LEFT_EYE, landmarks)
                ear_r = calculate_ear(RIGHT_EYE, landmarks)
                ear = (ear_l + ear_r) / 2.0
                
                status = "OPEN"
                if ear < threshold:
                    status = "BLINKING"
                    blink_count += 1
                    print(f"? BLINK #{blink_count} EAR={ear:.3f} THRESHOLD={threshold}")
                    time.sleep(0.2)
                else:
                    if int(time.time() * 2) % 10 == 0: # Print less frequently
                        print(f"DEBUG: EAR={ear:.3f} Status={status}")
            else:
                if int(time.time() * 2) % 10 == 0:
                    print("No face detected")
        else:
            # Fallback for testing if mediapipe is broken
            mock_ear = 0.25 if int(time.time()) % 5 != 0 else 0.15
            if mock_ear < threshold:
                blink_count += 1
                print(f"? BLINK #{blink_count} EAR={mock_ear:.3f} THRESHOLD={threshold} (MOCK)")
                time.sleep(1)
            else:
                if int(time.time() * 2) % 10 == 0:
                    print(f"DEBUG: EAR={mock_ear:.3f} Status=OPEN (MOCK)")
        
        time.sleep(0.1)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    cap.release()
    print("DEBUG SESSION FINISHED")
