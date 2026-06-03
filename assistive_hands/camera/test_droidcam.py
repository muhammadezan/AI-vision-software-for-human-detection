"""
DroidCam USB Camera Test Script

Run this script BEFORE starting Flask to confirm which camera index is DroidCam.

Usage:
    cd D:/New folder (2)/assistive_hands
    python camera/test_droidcam.py

Make sure:
    1. DroidCam PC Client is running
    2. Phone is connected via USB cable
    3. USB Debugging is enabled on phone
    4. DroidCam app shows "Connected" status
"""

import cv2
import time
import os


def test_cameras():
    """Test camera indices 0,1,2,3 and save test frames."""
    print("=" * 70)
    print("DroidCam USB Camera Detection Test")
    print("=" * 70)
    print()
    print("Prerequisites:")
    print("  ✓ DroidCam PC Client running (USB tab, click Start)")
    print("  ✓ Phone connected via USB cable")
    print("  ✓ USB Debugging enabled")
    print()
    print("Testing camera indices: 0, 1, 2, 3")
    print("-" * 70)
    print()
    
    found_cameras = []
    
    for index in [0, 1, 2, 3]:
        print(f"[Index {index}] Testing...", end=" ")
        
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            
            if not cap.isOpened():
                print("Not available")
                cap.release()
                continue
            
            # Try to read frame
            ret, frame = cap.read()
            
            if ret and frame is not None and frame.size > 0:
                h, w = frame.shape[:2]
                print(f"✓ SUCCESS! Resolution: {w}x{h}")
                
                # Save test image
                filename = f"test_camera_{index}.jpg"
                cv2.imwrite(filename, frame)
                print(f"          Saved: {filename}")
                
                found_cameras.append({
                    'index': index,
                    'resolution': (w, h),
                    'filename': filename
                })
            else:
                print("Opened but no valid frame")
            
            cap.release()
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(0.5)
    
    print()
    print("-" * 70)
    print()
    
    if found_cameras:
        print(f"✓ Found {len(found_cameras)} working camera(s):")
        print()
        for cam in found_cameras:
            print(f"  Index {cam['index']}: {cam['resolution'][0]}x{cam['resolution'][1]} -> {cam['filename']}")
        print()
        print("NEXT STEPS:")
        print("  1. Check the saved .jpg files to see which one is your phone")
        print("  2. If phone camera is at index 1 or 2, DroidCam is working!")
        print("  3. Start Flask: python app.py")
        print("  4. Open dashboard and check Desktop Camera tab")
    else:
        print("✗ No working cameras found!")
        print()
        print("TROUBLESHOOTING:")
        print("  1. Is DroidCam PC Client running? (check system tray)")
        print("  2. Phone connected via USB cable? (check Device Manager)")
        print("  3. USB Debugging enabled? (Settings > Developer Options)")
        print("  4. Did you click 'Start' in DroidCam USB tab?")
        print()
        print("Try these fixes:")
        print("  • Unplug USB cable and reconnect")
        print("  • Restart DroidCam PC Client")
        print("  • Restart Flask server after reconnecting")


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_cameras()
