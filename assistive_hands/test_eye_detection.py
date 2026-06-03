#!/usr/bin/env python3
"""Test eye detection and gaze tracking functionality."""

import requests
import time
import json
import sys

def test_eye_detection():
    """Test eye detection workflow."""
    base_url = "http://127.0.0.1:5000"
    
    print("=" * 60)
    print("EYE DETECTION & GAZE TRACKING TEST")
    print("=" * 60)
    
    # Test 1: Check server status
    print("\n[1] Checking server status...")
    try:
        resp = requests.get(f"{base_url}/api/status")
        if resp.status_code == 200:
            print("✓ Server is running")
        else:
            print(f"✗ Server returned status {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return False
    
    # Test 2: Start camera
    print("\n[2] Starting camera...")
    try:
        resp = requests.post(f"{base_url}/api/camera/start")
        data = resp.json()
        if resp.status_code == 200 and data.get('status') == 'success':
            print("✓ Camera started successfully")
        else:
            print(f"✗ Camera start failed: {data}")
            return False
    except Exception as e:
        print(f"✗ Camera start error: {e}")
        return False
    
    # Wait for camera to initialize
    time.sleep(2)
    
    # Test 3: Get gaze data (verify eye detection working)
    print("\n[3] Testing eye detection and gaze tracking...")
    print("   Capturing 10 gaze samples...\n")
    
    gaze_samples = []
    face_detected_count = 0
    iris_data_count = 0
    
    for i in range(10):
        try:
            resp = requests.get(f"{base_url}/api/gaze/current")
            data = resp.json()
            
            if resp.status_code == 200 and data.get('status') in ['success', 'info']:
                gaze = data.get('gaze_screen', {})
                face_detected = data.get('face_detected', False)
                eye_openness = data.get('eye_openness', 0)
                blink = data.get('blink_detected', False)
                fps = data.get('fps', 0)
                
                gaze_samples.append((gaze.get('x'), gaze.get('y')))
                
                if face_detected:
                    face_detected_count += 1
                
                status = "✓" if face_detected else "✗"
                print(f"   Sample {i+1:2d}: {status} Face={face_detected} | "
                      f"Gaze=({gaze.get('x', 0):4.0f}, {gaze.get('y', 0):4.0f}) | "
                      f"EyeOpen={eye_openness:.2f} | Blink={blink} | FPS={fps:.1f}")
                
                time.sleep(0.3)
            else:
                print(f"   Sample {i+1:2d}: ✗ API returned error: {data}")
        
        except Exception as e:
            print(f"   Sample {i+1:2d}: ✗ Error: {e}")
    
    # Test 4: Analyze results
    print("\n[4] Eye Detection Results:")
    print(f"   Face detected in {face_detected_count}/10 frames")
    
    if face_detected_count > 0:
        print("   ✓ Eye detection is WORKING")
    else:
        print("   ✗ Eye detection FAILED - no faces detected")
        print("   → Make sure camera is connected and you're visible to it")
        print("   → Try running VS Code as Administrator (Windows)")
        return False
    
    # Check gaze data variation (should not all be at center)
    if gaze_samples:
        x_values = [s[0] for s in gaze_samples if s[0] is not None]
        y_values = [s[1] for s in gaze_samples if s[1] is not None]
        
        if x_values and y_values:
            x_range = max(x_values) - min(x_values)
            y_range = max(y_values) - min(y_values)
            print(f"   Gaze movement range: X={x_range:.0f}px, Y={y_range:.0f}px")
            
            if x_range > 50 or y_range > 50:
                print("   ✓ Gaze tracking is responsive to eye movement")
            else:
                print("   ⚠ Gaze tracking shows minimal movement (may need calibration)")
    
    # Test 5: Test cursor control
    print("\n[5] Testing cursor control...")
    try:
        # Test moving to center
        resp = requests.post(f"{base_url}/api/cursor/move", json={'x': 960, 'y': 540})
        data = resp.json()
        
        if resp.status_code == 200:
            cursor_enabled = data.get('cursor_enabled', False)
            if cursor_enabled:
                print("✓ Cursor control is ENABLED and working")
            else:
                print("⚠ Cursor control disabled")
                print("   → May need admin privileges on Windows")
        else:
            print(f"✗ Cursor control error: {data}")
    
    except Exception as e:
        print(f"✗ Cursor control test error: {e}")
    
    # Test 6: Test cursor test endpoint
    print("\n[6] Running cursor movement test...")
    try:
        resp = requests.get(f"{base_url}/api/cursor/test")
        data = resp.json()
        
        if resp.status_code == 200:
            moves = data.get('moves', [])
            for move in moves:
                status = "✓" if move.get('success') else "✗"
                print(f"   {status} {move.get('position')}: {move.get('coords')}")
            print("✓ Cursor test complete - check if mouse moved")
        else:
            print(f"⚠ Cursor test not available: {data.get('message')}")
    
    except Exception as e:
        print(f"✗ Cursor test error: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY: Eye detection is working correctly!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_eye_detection()
    sys.exit(0 if success else 1)
