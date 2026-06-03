"""Keyboard control module for gaze-based text input and shortcuts."""

import logging

logger = logging.getLogger(__name__)


class KeyboardController:
    """Manages system keyboard input based on gaze and gestures."""
    
    def __init__(self):
        """Initialize keyboard controller."""
        self.pyautogui = None
        self.keyboard_enabled = False
        self._initialize_pyautogui()
    
    def _initialize_pyautogui(self):
        """Try to import and initialize pyautogui for keyboard control."""
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.keyboard_enabled = True
            logger.info("Keyboard control enabled (pyautogui available)")
        except ImportError:
            logger.warning("pyautogui not installed - keyboard control disabled")
            logger.info("To enable keyboard control, run: pip install pyautogui")
            self.keyboard_enabled = False
    
    def press_key(self, key: str) -> bool:
        """
        Press a system key.
        
        Args:
            key: Key name (e.g., 'enter', 'space', 'a', 'backspace')
            
        Returns:
            True if key pressed successfully, False otherwise
        """
        if not self.keyboard_enabled or self.pyautogui is None:
            logger.debug(f"Keyboard control disabled - cannot press {key}")
            return False
        
        try:
            # Normalize key names
            key_map = {
                'enter': 'return',
                'space': 'space',
                'backspace': 'backspace',
                'tab': 'tab',
                'escape': 'esc',
                'delete': 'delete',
                'shift': 'shift',
                'ctrl': 'ctrl',
                'alt': 'alt',
            }
            
            normalized_key = key_map.get(key.lower(), key.lower())
            self.pyautogui.press(normalized_key)
            logger.debug(f"Key pressed: {normalized_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key '{key}': {type(e).__name__}: {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """
        Type text to the system.
        
        Args:
            text: Text to type
            interval: Delay between characters (seconds)
            
        Returns:
            True if text typed successfully, False otherwise
        """
        if not self.keyboard_enabled or self.pyautogui is None:
            logger.debug("Keyboard control disabled - cannot type text")
            return False
        
        try:
            self.pyautogui.typewrite(text, interval=interval)
            logger.debug(f"Text typed: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to type text: {type(e).__name__}: {e}")
            return False
    
    def write_text(self, text: str) -> bool:
        """
        Write text using write() which handles special characters better.
        
        Args:
            text: Text to write
            
        Returns:
            True if text written successfully, False otherwise
        """
        if not self.keyboard_enabled or self.pyautogui is None:
            logger.debug("Keyboard control disabled - cannot write text")
            return False
        
        try:
            self.pyautogui.write(text, interval=0.01)
            logger.debug(f"Text written: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to write text: {type(e).__name__}: {e}")
            return False
    
    def hotkey(self, *keys) -> bool:
        """
        Press multiple keys simultaneously (hotkey).
        
        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
            
        Returns:
            True if hotkey executed successfully, False otherwise
        """
        if not self.keyboard_enabled or self.pyautogui is None:
            logger.debug(f"Keyboard control disabled - cannot execute hotkey {keys}")
            return False
        
        try:
            self.pyautogui.hotkey(*keys)
            logger.debug(f"Hotkey executed: {' + '.join(keys)}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute hotkey: {type(e).__name__}: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if keyboard control is enabled."""
        return self.keyboard_enabled
