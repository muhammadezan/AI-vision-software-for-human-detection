"""Utility modules for signal processing and event handling."""

from .signal_processing import (
    moving_average,
    kalman_filter,
    calculate_dwell_time,
    debounce_signal,
    remove_outliers
)
from .event_handler import EventHandler

__all__ = [
    'moving_average',
    'kalman_filter',
    'calculate_dwell_time',
    'debounce_signal',
    'remove_outliers',
    'EventHandler'
]
