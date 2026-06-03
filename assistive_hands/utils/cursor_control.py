"""Cursor control module for head movement tracking"""

import logging
import time

logger = logging.getLogger(__name__)


class CursorController:
    """Cursor controller optimized for head movement"""
    
    def __init__(self):
        self.pyautogui = None
        self.cursor_enabled = False
        
        # Head movement settings
        self.sensitivity = 2.5
        self.min_movement = 1
        
        # Tracking
        self.last_position = None
        self.debug_count = 0
        
        self._initialize_pyautogui()
    
    def _initialize_pyautogui(self):
        """Initialize pyautogui for cursor control"""
        try:
            import pyautogui
            
            # Configure pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.MINIMUM_DURATION = 0
            pyautogui.PAUSE = 0
            
            self.pyautogui = pyautogui
            self.cursor_enabled = True
            
            # Get screen size
            screen_w, screen_h = pyautogui.size()
            
            print("=" * 50)
            print("✓ CURSOR CONTROL ENABLED")
            print(f"  Screen: {screen_w} x {screen_h}")
            print(f"  Sensitivity: {self.sensitivity}x")
            print("=" * 50)
            
            logger.info(f"Cursor control enabled. Screen: {screen_w}x{screen_h}")
            
        except ImportError:
            print("✗ pyautogui not installed!")
            print("  Run: pip install pyautogui")
            logger.error("pyautogui not installed")
            self.cursor_enabled = False
            
        except PermissionError:
            print("✗ PERMISSION DENIED!")
            print("  Run this program as Administrator")
            print("  Right-click on terminal -> Run as Administrator")
            logger.error("Permission denied - run as administrator")
            self.cursor_enabled = False
    
    def move_cursor(self, x: int, y: int, duration: float = 0) -> bool:
        """
        Move cursor to screen coordinates
        
        Args:
            x: X coordinate (screen pixels)
            y: Y coordinate (screen pixels)
            duration: Movement duration (0 = instant)
        
        Returns:
            True if cursor moved, False otherwise
        """
        if not self.cursor_enabled or self.pyautogui is None:
            return False
        
        try:
            screen_width, screen_height = self.pyautogui.size()
            
            # Get current position
            if self.last_position is None:
                current_x, current_y = self.pyautogui.position()
            else:
                current_x, current_y = self.last_position
            
            # Clamp target to screen
            target_x = max(0, min(int(x), screen_width - 1))
            target_y = max(0, min(int(y), screen_height - 1))
            
            # Calculate movement delta
            delta_x = target_x - current_x
            delta_y = target_y - current_y
            
            # Apply sensitivity
            delta_x = delta_x * self.sensitivity
            delta_y = delta_y * self.sensitivity
            
            # Only move if exceeds minimum threshold
            if abs(delta_x) >= self.min_movement or abs(delta_y) >= self.min_movement:
                new_x = current_x + delta_x
                new_y = current_y + delta_y
                
                # Clamp to screen
                new_x = max(0, min(int(new_x), screen_width - 1))
                new_y = max(0, min(int(new_y), screen_height - 1))
                
                # Move cursor
                self.pyautogui.moveTo(new_x, new_y, duration=duration)
                self.last_position = (new_x, new_y)
                
                # Debug every 50 moves
                self.debug_count += 1
                if self.debug_count % 50 == 0:
                    logger.debug(f"Cursor moved: ({new_x}, {new_y}) delta=({delta_x:.1f}, {delta_y:.1f})")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cursor move failed: {e}")
            if "permission" in str(e).lower():
                self.cursor_enabled = False
                print("✗ Permission error! Run as Administrator")
            return False
    
    def is_enabled(self) -> bool:
        """Check if cursor control is enabled"""
        return self.cursor_enabled
    
    def reset_position(self):
        """Reset last known cursor position"""
        if self.pyautogui:
            self.last_position = self.pyautogui.position()