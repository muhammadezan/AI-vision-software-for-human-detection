#!/usr/bin/env python3
"""Script to patch app.py with cursor control endpoint."""

import re

# Read the app.py file
with open(r'd:\New folder (2)\assistive_hands\app.py', 'r') as f:
    content = f.read()

# Find the position to insert (before "# ========== Error Handlers ==========")
pattern = r'(# ========== Error Handlers ==========)'

cursor_endpoint = '''
# ========== Cursor Control API ==========

@app.route('/api/cursor/move', methods=['POST'])
def move_cursor():
    """Move system cursor based on gaze position."""
    from utils.cursor_control import CursorController
    try:
        data = request.get_json()
        x = int(data.get('x', 0))
        y = int(data.get('y', 0))
        
        controller = CursorController()
        success = controller.move_cursor(x, y, duration=0)
        
        return jsonify({'status': 'success' if success else 'info', 'x': x, 'y': y, 'cursor_enabled': controller.is_enabled()})
    except Exception as e:
        logger.error(f"Error moving cursor: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


'''

# Replace
if '# ========== Cursor Control API ==========' not in content:
    content = re.sub(pattern, cursor_endpoint + r'\1', content)
    
    # Write back
    with open(r'd:\New folder (2)\assistive_hands\app.py', 'w') as f:
        f.write(content)
    
    print("Successfully patched app.py with cursor control endpoint")
else:
    print("Cursor control endpoint already exists")
