"""Signal processing utilities for gaze tracking."""

import numpy as np
import logging
from typing import List, Tuple, Optional
from collections import deque

logger = logging.getLogger(__name__)


def moving_average(data: List[float], window_size: int = 5) -> List[float]:
    """
    Apply moving average filter to data.
    
    Args:
        data: Input data array
        window_size: Size of moving average window
        
    Returns:
        Smoothed data
    """
    if len(data) < window_size:
        return data
    
    smoothed = []
    for i in range(len(data)):
        start = max(0, i - window_size // 2)
        end = min(len(data), i + window_size // 2 + 1)
        smoothed.append(np.mean(data[start:end]))
    
    return smoothed


def kalman_filter(
    measurements: List[float],
    process_variance: float = 0.01,
    measurement_variance: float = 4.0,
    initial_value: float = 0.0
) -> List[float]:
    """
    Apply Kalman filter to measurements.
    
    Args:
        measurements: Input measurements
        process_variance: Process noise variance
        measurement_variance: Measurement noise variance
        initial_value: Initial estimate
        
    Returns:
        Filtered values
    """
    filtered = []
    
    # Initialize state
    x = initial_value  # State estimate
    P = 1.0  # Error covariance
    
    for z in measurements:
        # Prediction
        x_pred = x
        P_pred = P + process_variance
        
        # Update
        K = P_pred / (P_pred + measurement_variance)  # Kalman gain
        x = x_pred + K * (z - x_pred)
        P = (1 - K) * P_pred
        
        filtered.append(x)
    
    return filtered


def calculate_dwell_time(
    gaze_points: List[Tuple[float, float]],
    target_region: Tuple[int, int, int, int],
    threshold: float = 50.0,
    fps: int = 30
) -> float:
    """
    Calculate dwell time in a target region.
    
    Args:
        gaze_points: List of (x, y) gaze points
        target_region: (x_min, y_min, x_max, y_max) of target
        threshold: Distance threshold in pixels
        fps: Frames per second
        
    Returns:
        Dwell time in seconds
    """
    x_min, y_min, x_max, y_max = target_region
    center_x = (x_min + x_max) / 2.0
    center_y = (y_min + y_max) / 2.0
    
    dwell_frames = 0
    for gaze_x, gaze_y in gaze_points:
        distance = np.sqrt((gaze_x - center_x)**2 + (gaze_y - center_y)**2)
        if distance < threshold:
            dwell_frames += 1
    
    dwell_time = dwell_frames / fps
    return dwell_time


def debounce_signal(
    signal: List[bool],
    min_duration: float = 0.2,
    fps: int = 30
) -> List[bool]:
    """
    Debounce a boolean signal to avoid false positives.
    
    Args:
        signal: Input signal (True/False)
        min_duration: Minimum duration to trigger (seconds)
        fps: Frames per second
        
    Returns:
        Debounced signal
    """
    min_frames = int(min_duration * fps)
    debounced = []
    
    i = 0
    while i < len(signal):
        if signal[i]:
            # Count consecutive True values
            count = 0
            j = i
            while j < len(signal) and signal[j]:
                count += 1
                j += 1
            
            # Include event if it lasts long enough
            if count >= min_frames:
                for _ in range(count):
                    debounced.append(True)
            else:
                for _ in range(count):
                    debounced.append(False)
            
            i = j
        else:
            debounced.append(False)
            i += 1
    
    return debounced


def remove_outliers(data: np.ndarray, std_threshold: float = 2.0) -> np.ndarray:
    """
    Remove outliers from data using standard deviation.
    
    Args:
        data: Input data array
        std_threshold: Number of standard deviations for outlier detection
        
    Returns:
        Filtered data (outliers replaced with mean)
    """
    if len(data) < 2:
        return data
    
    mean = np.mean(data)
    std = np.std(data)
    
    if std == 0:
        return data
    
    filtered = data.copy()
    outlier_mask = np.abs(data - mean) > (std_threshold * std)
    filtered[outlier_mask] = mean
    
    return filtered


def calculate_confidence_score(
    measurements: List[float],
    variance_weight: float = 0.3
) -> float:
    """
    Calculate confidence score for measurements.
    
    Args:
        measurements: List of measurements
        variance_weight: Weight for variance penalty
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    if len(measurements) < 2:
        return 0.0
    
    measurements = np.array(measurements)
    variance = np.var(measurements)
    
    # Normalize variance (assuming max variance of 0.1)
    variance_penalty = min(1.0, variance / 0.1)
    
    # Confidence decreases with variance
    confidence = 1.0 - (variance_weight * variance_penalty)
    
    return max(0.0, min(1.0, confidence))


class RollingBuffer:
    """Rolling buffer for time series data."""
    
    def __init__(self, max_size: int = 100):
        """Initialize rolling buffer."""
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
    
    def append(self, value):
        """Add value to buffer."""
        self.buffer.append(value)
    
    def get_array(self) -> np.ndarray:
        """Get buffer as numpy array."""
        return np.array(list(self.buffer))
    
    def clear(self):
        """Clear buffer."""
        self.buffer.clear()
    
    def __len__(self):
        """Get buffer size."""
        return len(self.buffer)
