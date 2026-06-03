"""Event handler for UI interactions based on gaze and gestures."""

import logging
from typing import Tuple, List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from config.settings import SystemConfig

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types."""
    DWELL_CLICK = "dwell_click"
    BLINK_CLICK = "blink_click"
    HOVER = "hover"
    HEAD_TURN = "head_turn"
    SMILE = "smile"
    BLINK = "blink"


@dataclass
class UIElement:
    """Represents a UI element."""
    element_id: str
    x: int
    y: int
    width: int
    height: int
    label: str = ""
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is inside element."""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def get_center(self) -> Tuple[int, int]:
        """Get center of element."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def distance_to_point(self, x: int, y: int) -> float:
        """Get distance from point to element center."""
        cx, cy = self.get_center()
        return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5


@dataclass
class Event:
    """Represents an event."""
    event_type: EventType
    element: Optional[UIElement] = None
    data: Optional[Dict] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventHandler:
    """Handles UI interactions based on gaze, blinks, and gestures."""
    
    def __init__(self):
        """Initialize event handler."""
        self.ui_elements: Dict[str, UIElement] = {}
        self.event_queue: List[Event] = []
        self.dwell_tracker: Dict[str, float] = {}  # element_id -> dwell_time
        self.hover_element: Optional[UIElement] = None
        self.last_blink_time: Optional[datetime] = None
        self.callbacks: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self.dwell_threshold = SystemConfig.DWELL_TIME
        self.hover_threshold = SystemConfig.BUTTON_HOVER_THRESHOLD
    
    def register_ui_element(self, element: UIElement) -> None:
        """
        Register a UI element.
        
        Args:
            element: UIElement to register
        """
        self.ui_elements[element.element_id] = element
        self.dwell_tracker[element.element_id] = 0.0
        logger.debug(f"Registered UI element: {element.element_id}")
    
    def register_callback(self, event_type: EventType, callback: Callable) -> None:
        """
        Register callback for event type.
        
        Args:
            event_type: Type of event
            callback: Callable to execute
        """
        self.callbacks[event_type].append(callback)
    
    def detect_hover(self, gaze_point: Tuple[int, int]) -> Optional[UIElement]:
        """
        Detect which UI element gaze is hovering over.
        
        Args:
            gaze_point: (x, y) gaze coordinates
            
        Returns:
            Hovered UIElement or None
        """
        gaze_x, gaze_y = gaze_point
        
        # Find closest element within threshold
        closest_element = None
        min_distance = self.hover_threshold
        
        for element in self.ui_elements.values():
            if element.contains_point(gaze_x, gaze_y):
                return element
            
            distance = element.distance_to_point(gaze_x, gaze_y)
            if distance < min_distance:
                min_distance = distance
                closest_element = element
        
        return closest_element
    
    def trigger_dwell_click(self, element: UIElement, dwell_duration: float) -> None:
        """
        Trigger click event after dwell time threshold.
        
        Args:
            element: UI element
            dwell_duration: Time spent dwelling (seconds)
        """
        if dwell_duration >= self.dwell_threshold:
            event = Event(
                event_type=EventType.DWELL_CLICK,
                element=element,
                data={'dwell_duration': dwell_duration}
            )
            self.queue_event(event)
            logger.info(f"Dwell click triggered on {element.element_id}")
    
    def confirm_with_blink(self, element: UIElement, blink_detected: bool) -> None:
        """
        Confirm selection with blink.
        
        Args:
            element: UI element
            blink_detected: Whether blink was detected
        """
        if blink_detected:
            event = Event(
                event_type=EventType.BLINK_CLICK,
                element=element
            )
            self.queue_event(event)
            logger.info(f"Blink click triggered on {element.element_id}")
    
    def navigate_with_gesture(self, gesture_type: str, direction: Optional[str] = None) -> None:
        """
        Navigate using facial gestures.
        
        Args:
            gesture_type: Type of gesture (head_turn, smile)
            direction: Direction for head turn (left, right, up, down)
        """
        event = Event(
            event_type=EventType.HEAD_TURN if gesture_type == "head_turn" else EventType.SMILE,
            data={'gesture': gesture_type, 'direction': direction}
        )
        self.queue_event(event)
        logger.info(f"Navigation gesture: {gesture_type} {direction}")
    
    def queue_event(self, event: Event) -> None:
        """
        Queue an event for processing.
        
        Args:
            event: Event to queue
        """
        self.event_queue.append(event)
    
    def process_event_queue(self) -> List[Event]:
        """
        Process and clear event queue.
        
        Returns:
            List of processed events
        """
        processed_events = []
        
        for event in self.event_queue:
            processed_events.append(event)
            
            # Execute callbacks
            if event.event_type in self.callbacks:
                for callback in self.callbacks[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Error executing callback: {e}")
        
        self.event_queue.clear()
        return processed_events
    
    def update_dwell(self, gaze_point: Tuple[int, int], delta_time: float) -> None:
        """
        Update dwell time tracking.
        
        Args:
            gaze_point: Current gaze point
            delta_time: Time since last update (seconds)
        """
        current_hover = self.detect_hover(gaze_point)
        
        # Reset all dwell counters
        for element_id in self.dwell_tracker:
            if self.ui_elements[element_id] != current_hover:
                self.dwell_tracker[element_id] = 0.0
        
        # Increment dwell for current element
        if current_hover:
            self.dwell_tracker[current_hover.element_id] += delta_time
            self.trigger_dwell_click(current_hover, self.dwell_tracker[current_hover.element_id])
        
        self.hover_element = current_hover
    
    def get_current_hover_element(self) -> Optional[UIElement]:
        """Get currently hovered element."""
        return self.hover_element
    
    def get_dwell_time(self, element_id: str) -> float:
        """Get dwell time for element."""
        return self.dwell_tracker.get(element_id, 0.0)
    
    def clear_ui_elements(self) -> None:
        """Clear all registered UI elements."""
        self.ui_elements.clear()
        self.dwell_tracker.clear()
        self.hover_element = None
        logger.info("Cleared all UI elements")
    
    def set_dwell_threshold(self, threshold: float) -> None:
        """Set dwell time threshold."""
        self.dwell_threshold = threshold
        logger.debug(f"Dwell threshold set to {threshold}s")
