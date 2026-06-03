#!/usr/bin/env python3
"""Simple test to verify cursor control is working"""

import cv2
import numpy as np
import time

def test_cursor_only():
    """Test if cursor control works at all"""
    print("\n" + "=" * 50)
    print("CURSOR CONTROL TEST")
    print("=" * 50)
    
    try:
        import pyautogui
        print("✓ pyautogui found")
        
        # Get screen size
        w, h = pyautogui.size()
        print(f"✓ Screen: {w} x {h}")
        
        # Get current position
        x, y = pyautogui.position()
        print(f"✓ Current cursor: ({x}, {y})")
        
        # Test move
        print("\n→ Moving cursor to center...")
        pyautogui.moveTo(w//2, h//2)
        print("✓ Cursor moved to center!")
        
        # Test small movements
        print("\n→ Testing small movements...")
        for i in range(5):
            pyautogui.moveRel(10, 0)
            time.sleep(0.1)
            pyautogui.moveRel(-10, 0)
            time.sleep(0.1)
        print("✓ Small movements work!")
        
        print("\n" + "=" * 50)
        print("✅ CURSOR CONTROL IS WORKING PERFECTLY!")
        print("=" * 50)
        return True
        
    except ImportError:
        print("\n❌ pyautogui NOT INSTALLED")
        print("   Run: pip install pyautogui")
        return False
        
    except PermissionError:
        print("\n❌ PERMISSION DENIED")
        print("   Run this script as Administrator")
        print("   Right-click on terminal -> Run as Administrator")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_head_tracking():
    """Test full head tracking"""
    print("\n" + "=" * 50)
    print("HEAD TRACKING TEST")
    print("=" * 50)
    
    try:
        from camera.gaze_estimator import GazeEstimator
        from utils.cursor_control import CursorController
        
        gaze = GazeEstimator()
        cursor = CursorController()
        
        if not cursor.is_enabled():
            print("❌ Cursor controller not enabled!")
            return False
        
        print("✓ Both modules loaded")
        print("\n⚠️ Note: This test requires camera and face detection")
        print("   Run your main app.py for full testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading modules: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "🔧 ASSISTIVE HANDS DIAGNOSTIC TOOL")
    
    # Test 1: Basic cursor
    cursor_works = test_cursor_only()
    
    # Test 2: Module loading
    if cursor_works:
        test_head_tracking()
    
    print("\n" + "=" * 50)
    if cursor_works:
        print("✅ Ready to run: python app.py")
    else:
        print("⚠️ Fix issues above first")
    print("=" * 50)
