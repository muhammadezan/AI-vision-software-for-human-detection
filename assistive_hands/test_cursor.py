#!/usr/bin/env python3
"""Test cursor control directly."""

import requests
import time
import sys

print("Testing cursor control...")
print("-" * 50)

# Test 1: Check if server is running
try:
    resp = requests.get('http://127.0.0.1:5000/api/status')
    print(f"✓ Server running: {resp.status_code}")
except Exception as e:
    print(f"✗ Server not running: {e}")
    sys.exit(1)

# Test 2: Try to move cursor to different positions
test_positions = [
    (100, 100, "top-left"),
    (500, 300, "center"),
    (1800, 1000, "bottom-right"),
    (960, 540, "screen center"),
]

print("\nMoving cursor to test positions...")
for x, y, desc in test_positions:
    try:
        resp = requests.post('http://127.0.0.1:5000/api/cursor/move', 
                           json={'x': x, 'y': y})
        data = resp.json()
        status = "✓" if resp.status_code == 200 else "✗"
        cursor_enabled = data.get('cursor_enabled', False)
        print(f"{status} {desc:15} ({x:4}, {y:4}): {resp.status_code} | cursor_enabled={cursor_enabled}")
        time.sleep(0.5)
    except Exception as e:
        print(f"✗ {desc:15} ({x:4}, {y:4}): ERROR: {e}")

print("\nDone! Check if your mouse cursor moved to the positions above.")
print("If cursor didn't move but status was 200:")
print("  → You may need to run VS Code as Administrator")
print("  → On Windows, right-click VS Code → Run as Administrator")
