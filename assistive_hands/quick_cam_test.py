import cv2
import time

print("DroidCam camera index test...")
print("DroidCam PC Client USB tab mein Start dabao pehle!\n")

found = []
for i in range(4):
    print(f"Index {i} try kar raha hoon...", end=" ")
    try:
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"KAAM KIYA! Size: {w}x{h}")
                cv2.imwrite(f"cam_{i}.jpg", frame)
                print(f"  -> cam_{i}.jpg save hua - check karo yeh phone camera hai?")
                found.append(i)
            else:
                print("Khula lekin frame nahi aya")
        else:
            print("Nahi mila")
        cap.release()
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.3)

print()
if found:
    print(f"Kaam karne wale indices: {found}")
    print("cam_0.jpg, cam_1.jpg etc check karo - konsa phone camera hai?")
else:
    print("Koi camera nahi mila!")
    print("Check karo: DroidCam Client USB tab mein Start dabaya?")
