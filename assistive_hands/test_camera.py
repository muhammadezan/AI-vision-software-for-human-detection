import cv2
import sys

print("=== CAMERA DETECTION TEST ===\n")

# Test camera 0
cap = cv2.VideoCapture(0)
print(f"Camera 0 opened: {cap.isOpened()}")

if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"✅ Frame captured! Shape: {frame.shape}")
    else:
        print("❌ Could not read frame from camera 0")
    cap.release()
else:
    print("❌ Camera 0 not available")
    print("\nSearching for other cameras...")
    found_any = False
    for i in range(1, 5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ Camera {i} found!")
            cap.release()
            found_any = True
    
    if not found_any:
        print("❌ No cameras found!")
        sys.exit(1)
