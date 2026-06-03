"""
Integration module for Android cameras with AssistiveHands
Provides Flask endpoints and configuration for mobile camera support
"""

from flask import Flask, jsonify, request, Response
from camera.android_camera import AndroidCameraManager, AndroidUSBCamera
import cv2
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AndroidCameraIntegration:
    """Integrates Android cameras into AssistiveHands"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.manager = AndroidCameraManager()
        self.primary_device_id = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes for Android camera control"""
        
        @self.app.route('/api/android/devices', methods=['GET'])
        def list_devices():
            """List connected Android devices"""
            devices = AndroidUSBCamera.get_adb_devices()
            return jsonify({
                'status': 'success',
                'devices': devices,
                'count': len(devices)
            })
        
        @self.app.route('/api/android/device-info/<device_id>', methods=['GET'])
        def device_info(device_id):
            """Get information about specific Android device"""
            info = AndroidUSBCamera.get_device_info(device_id)
            return jsonify({
                'status': 'success',
                'device_id': device_id,
                'info': info
            })
        
        @self.app.route('/api/android/connect', methods=['POST'])
        def connect_device():
            """Connect to Android device for camera streaming"""
            data = request.json
            device_id = data.get('device_id')
            device_ip = data.get('device_ip')
            port = data.get('port', 8888)
            mode = data.get('mode', 'network')  # 'usb' or 'network'
            use_as_primary = data.get('use_as_primary', True)
            
            if not device_id:
                return jsonify({'status': 'error', 'message': 'device_id required'}), 400
            
            if mode == 'usb' and device_id:
                # Enable TCP/IP for USB devices if needed
                AndroidUSBCamera.enable_tcpip_mode(device_id)
            
            success = self.manager.add_device(device_id, device_ip, port, mode)
            
            if success and use_as_primary:
                self.primary_device_id = device_id
            
            return jsonify({
                'status': 'success' if success else 'error',
                'device_id': device_id,
                'connected': success,
                'is_primary': use_as_primary
            })
        
        @self.app.route('/api/android/disconnect/<device_id>', methods=['POST'])
        def disconnect_device(device_id):
            """Disconnect Android device"""
            self.manager.remove_device(device_id)
            if self.primary_device_id == device_id:
                self.primary_device_id = None
            
            return jsonify({
                'status': 'success',
                'device_id': device_id,
                'disconnected': True
            })
        
        @self.app.route('/api/android/stream/<device_id>', methods=['GET'])
        def android_stream(device_id):
            """Stream video from specific Android device"""
            def generate():
                while True:
                    frame = self.manager.get_frame(device_id)
                    if frame is None:
                        continue
                    
                    # Encode frame to JPEG
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    
                    # MJPEG format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                           + frame_bytes + b'\r\n')
            
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/api/android/primary-stream', methods=['GET'])
        def primary_stream():
            """Stream from primary Android device"""
            if not self.primary_device_id:
                return jsonify({'status': 'error', 'message': 'No primary device set'}), 400
            
            def generate():
                while True:
                    frame = self.manager.get_frame(self.primary_device_id)
                    if frame is None:
                        continue
                    
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                           + frame_bytes + b'\r\n')
            
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/api/android/status', methods=['GET'])
        def status():
            """Get status of all connected devices"""
            status_info = {}
            for device_id, camera in self.manager.devices.items():
                status_info[device_id] = {
                    'connected': camera.is_running,
                    'fps': camera.fps,
                    'resolution': f"{camera.frame_width}x{camera.frame_height}",
                    'is_primary': device_id == self.primary_device_id
                }
            
            return jsonify({
                'status': 'success',
                'devices': status_info,
                'active_count': len([d for d in status_info.values() if d['connected']])
            })
        
        @self.app.route('/api/android/set-primary/<device_id>', methods=['POST'])
        def set_primary(device_id):
            """Set device as primary camera"""
            if device_id not in self.manager.devices:
                return jsonify({'status': 'error', 'message': 'Device not found'}), 404
            
            self.primary_device_id = device_id
            return jsonify({
                'status': 'success',
                'primary_device': device_id
            })
        
        @self.app.route('/api/android/configure', methods=['POST'])
        def configure_device():
            """Configure Android device settings"""
            data = request.json
            device_id = data.get('device_id')
            fps = data.get('fps')
            width = data.get('width')
            height = data.get('height')
            
            if device_id not in self.manager.devices:
                return jsonify({'status': 'error', 'message': 'Device not found'}), 404
            
            camera = self.manager.devices[device_id]
            if fps:
                camera.fps = fps
            if width:
                camera.frame_width = width
            if height:
                camera.frame_height = height
            
            return jsonify({
                'status': 'success',
                'device_id': device_id,
                'config': {
                    'fps': camera.fps,
                    'width': camera.frame_width,
                    'height': camera.frame_height
                }
            })
        
        @self.app.route('/api/android/shutdown', methods=['POST'])
        def shutdown():
            """Shutdown all Android camera streams"""
            self.manager.stop_all()
            self.primary_device_id = None
            return jsonify({'status': 'success', 'message': 'All streams stopped'})
    
    def get_primary_frame(self) -> Optional[bytes]:
        """Get frame from primary device as JPEG"""
        if not self.primary_device_id:
            return None
        
        frame = self.manager.get_frame(self.primary_device_id)
        if frame is None:
            return None
        
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes() if ret else None


def init_android_camera(app: Flask) -> AndroidCameraIntegration:
    """Initialize Android camera integration with Flask app"""
    logger.info("Initializing Android camera integration")
    return AndroidCameraIntegration(app)
