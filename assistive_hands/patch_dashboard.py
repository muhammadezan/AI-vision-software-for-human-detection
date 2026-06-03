#!/usr/bin/env python3
"""Script to patch dashboard.js with gaze-to-cursor control."""

# Read the dashboard.js file
with open(r'd:\New folder (2)\assistive_hands\ui\static\js\dashboard.js', 'r') as f:
    lines = f.readlines()

# Find the line that has "updateGazeCursor(gaze_screen.x, gaze_screen.y);" and add cursor movement after it
patched_lines = []
for i, line in enumerate(lines):
    patched_lines.append(line)
    
    # After updating gaze cursor, add system cursor movement
    if 'updateGazeCursor(gaze_screen.x, gaze_screen.y);' in line and 'moveSystemCursor' not in lines[i+1]:
        # Add indentation matching the previous line
        indent = len(line) - len(line.lstrip())
        patched_lines.append(' ' * indent + 'moveSystemCursor(gaze_screen.x, gaze_screen.y);\n')

# Add the moveSystemCursor function at the end if it doesn't exist
content = ''.join(patched_lines)
if 'function moveSystemCursor' not in content:
    # Find the location to add (before "// Cleanup on page unload")
    if '// Cleanup on page unload' in content:
        cleanup_index = content.find('// Cleanup on page unload')
        insert_code = '''
// Move system cursor based on gaze
let cursorMoveInterval = null;
function moveSystemCursor(x, y) {
    // Throttle cursor updates to avoid excessive API calls
    if (!cursorMoveInterval) {
        cursorMoveInterval = setInterval(() => {
            if (lastGazeX !== undefined && lastGazeY !== undefined) {
                api.post('/api/cursor/move', { x: lastGazeX, y: lastGazeY })
                    .catch(err => console.debug('Cursor move error:', err));
            }
        }, 50); // Update cursor every 50ms
    }
    
    // Store latest gaze position
    window.lastGazeX = x;
    window.lastGazeY = y;
}

'''
        content = content[:cleanup_index] + insert_code + content[cleanup_index:]

# Write back
with open(r'd:\New folder (2)\assistive_hands\ui\static\js\dashboard.js', 'w') as f:
    f.write(content)

print("Successfully patched dashboard.js with gaze-to-cursor control")
