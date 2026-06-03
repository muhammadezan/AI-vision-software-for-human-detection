"""
Android Camera Integration Module for AssistiveHands
Provides real-time camera feed from Android devices via USB or network streaming
"""

import cv2
import numpy as np
import threading
import socket
import struct
import time
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class AndroidCameraStream:
    """Handles streaming from Android device camera"""
    
    def __init__(self, device_ip: Optional[str] = None, port: int = 8888, 
                 mode: str = 'usb'):
        """
        Initialize Android camera stream
        
        Args:
            device_ip: IP address of Android device (for network mode)
            port: Port number for streaming
            mode: 'usb' for USB connection, 'network' for WiFi streaming
        """
        self.device_ip = device_ip
        self.port = port
        self.mode = mode
        self.cap = None
        self.frame = None
        self.is_running = False
        self.thread = None
        self.fps = 30
        self.frame_width = 640
        self.frame_height = 480
        
    def connect_usb(self) -> bool:
        """
        Connect via USB (adb forward)
        Requires: adb installed and device connected
        """
        try:
            import subprocess
            # Forward port via adb
            result = subprocess.run(
                ['adb', 'forward', f'tcp:{self.port}', 'tcp:5555'],
                capture_output=True
            )
            if result.returncode == 0:
                logger.info("USB ADB forward configured successfully")
                return self._connect_to_stream()
            else:
                logger.error("Failed to configure ADB forward")
                return False
        except Exception as e:
            logger.error(f"USB connection failed: {e}")
            return False
    
    def connect_network(self) -> bool:
        """
        Connect via WiFi/Network
        Requires IP-Webcam or similar app on Android device
        """
        try:
            if not self.device_ip:
                logger.error("Device IP not provided for network connection")
                return False
            
            # URL format for IP-Webcam or similar apps
            stream_url = f"http://{self.device_ip}:{self.port}/video"
            self.cap = cv2.VideoCapture(stream_url)
            
            if self.cap.isOpened():
                logger.info(f"Connected to Android device at {self.device_ip}:{self.port}")
                return True
            else:
                logger.error(f"Failed to connect to {stream_url}")
                return False
        except Exception as e:
            logger.error(f"Network connection failed: {e}")
            return False
    
    def _connect_to_stream(self) -> bool:
        """Connect to localhost stream after USB forward"""
        try:
            self.cap = cv2.VideoCapture(f"http://localhost:{self.port}/video")
            if self.cap.isOpened():
                logger.info("Connected to USB stream")
                return True
            else:
                logger.error("Failed to open USB stream")
                return False
        except Exception as e:
            logger.error(f"Stream connection failed: {e}")
            return False
    
    def start(self) -> bool:
        """Start streaming from Android device"""
        if self.is_running:
            logger.warning("Stream already running")
            return False
        
        # Connect based on mode
        if self.mode == 'usb':
            connected = self.connect_usb()
        elif self.mode == 'network':
            connected = self.connect_network()
        else:
            logger.error(f"Unknown connection mode: {self.mode}")
            return False
        
        if not connected:
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Android camera stream started")
        return True
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.frame = frame
                else:
                    logger.warning("Failed to read frame")
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.1)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame from Android camera"""
        return self.frame.copy() if self.frame is not None else None
    
    def stop(self):
        """Stop streaming from Android device"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        logger.info("Android camera stream stopped")


class AndroidCameraManager:
    """Manages multiple Android device connections"""
    
    def __init__(self):
        self.devices: Dict[str, AndroidCameraStream] = {}
    
    def add_device(self, device_id: str, device_ip: Optional[str] = None,
                   port: int = 8888, mode: str = 'network') -> bool:
        """
        Add new Android device to manager
        
        Args:
            device_id: Unique identifier for device
            device_ip: IP address (required for network mode)
            port: Streaming port
            mode: 'usb' or 'network'
        """
        if device_id in self.devices:
            logger.warning(f"Device {device_id} already exists")
            return False
        
        camera = AndroidCameraStream(device_ip, port, mode)
        if camera.start():
            self.devices[device_id] = camera
            logger.info(f"Device {device_id} added successfully")
            return True
        else:
            logger.error(f"Failed to start device {device_id}")
            return False
    
    def remove_device(self, device_id: str):
        """Remove Android device from manager"""
        if device_id in self.devices:
            self.devices[device_id].stop()
            del self.devices[device_id]
            logger.info(f"Device {device_id} removed")
    
    def get_frame(self, device_id: str) -> Optional[np.ndarray]:
        """Get frame from specific device"""
        if device_id in self.devices:
            return self.devices[device_id].get_frame()
        return None
    
    def get_all_frames(self) -> Dict[str, Optional[np.ndarray]]:
        """Get frames from all connected devices"""
        return {
            device_id: camera.get_frame()
            for device_id, camera in self.devices.items()
        }
    
    def stop_all(self):
        """Stop all device streams"""
        for device_id in list(self.devices.keys()):
            self.remove_device(device_id)


class AndroidUSBCamera:
    """Direct USB camera access using adb"""
    
    @staticmethod
    def get_adb_devices() -> list:
        """List all connected Android devices via adb"""
        try:
            import subprocess
            result = subprocess.run(
                ['adb', 'devices', '-l'],
                capture_output=True,
                text=True
            )
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if line.strip() and not line.startswith('*'):
                    devices.append(line.split()[0])
            return devices
        except Exception as e:
            logger.error(f"Failed to list ADB devices: {e}")
            return []
    
    @staticmethod
    def enable_tcpip_mode(device_id: str, port: int = 5555) -> bool:
        """Enable TCP/IP mode on device for wireless connection"""
        try:
            import subprocess
            subprocess.run(['adb', '-s', device_id, 'tcpip', str(port)])
            logger.info(f"TCP/IP mode enabled on {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable TCP/IP: {e}")
            return False
    
    @staticmethod
    def get_device_info(device_id: str) -> Dict:
        """Get information about Android device"""
        try:
            import subprocess
            info = {}
            
            # Get device model
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                capture_output=True,
                text=True
            )
            info['model'] = result.stdout.strip()
            
            # Get Android version
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'],
                capture_output=True,
                text=True
            )
            info['android_version'] = result.stdout.strip()
            
            # Get screen resolution
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'wm', 'size'],
                capture_output=True,
                text=True
            )
            info['screen_resolution'] = result.stdout.strip()
            
            return info
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {}
