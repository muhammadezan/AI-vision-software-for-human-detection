import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options
import numpy as np
import pyautogui
import time
from flask import Flask, Response, render_template, jsonify, request, send_from_directory
import threading
import webbrowser

app = Flask(__name__, template_folder='ui/templates', static_folder='ui/static')

# ---- Camera ----
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ---- MediaPipe VIDEO mode ----
base_opts = base_options.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_opts,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)
last_ts = 0

def now_ms():
    return int(time.time() * 1000)

# ---- PyAutoGUI ----
pyautogui.FAILSAFE = False
pyautogui.MINIMUM_DURATION = 0
pyautogui.PAUSE = 0
screen_w, screen_h = pyautogui.size()

# ---- EMA cursor smoothing ----
EMA_ALPHA   = 0.30
ema_x       = None
ema_y       = None
sensitivity = 5.0

# ---- Blink state ----
face_detected      = False
blink_detected     = False
eye_openness       = 1.0
eyes_closed        = False
last_blink_time    = 0.0
last_click_time    = 0.0
CLICK_COOLDOWN     = 1.2
BLINK_FLAG_DUR     = 0.4
ear_open_avg       = 0.30
BLINK_RATIO        = 0.25  # Very sensitive - threshold will be ~0.13
calibration_frames = 0

# ---- Dwell state ----
dwell_position   = None
dwell_start_time = 0.0
dwell_progress   = 0.0
dwell_fired      = False
last_dwell_click = 0.0
DWELL_RADIUS     = 60
DWELL_TIME       = 1.5
DWELL_COOLDOWN   = 1.5


def get_ear(lm, w, h):
    def d(a, b):
        return np.hypot(a[0]-b[0], a[1]-b[1])
    try:
        lp = [[lm[i].x*w, lm[i].y*h] for i in [33, 160, 158, 133, 153, 144]]
        rp = [[lm[i].x*w, lm[i].y*h] for i in [362, 385, 387, 263, 373, 380]]
        l = d(lp[1], lp[4]) / (d(lp[0], lp[3]) + 1e-6)
        r = d(rp[1], rp[4]) / (d(rp[0], rp[3]) + 1e-6)
        return float(max(0.0, (l + r) / 2.0))
    except Exception as e:
        print(f"EAR err: {e}")
        return 1.0


def process_frame(frame):
    global ema_x, ema_y, last_ts
    global blink_detected, face_detected, eye_openness
    global last_blink_time, last_click_time, eyes_closed, ear_open_avg
    global dwell_position, dwell_start_time, dwell_progress, dwell_fired
    global last_dwell_click, calibration_frames

    h, w = frame.shape[:2]
    now  = time.time()

    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    ts = now_ms()
    if ts <= last_ts:
        ts = last_ts + 1
    last_ts = ts

    result = face_landmarker.detect_for_video(mp_image, ts)
    face_detected = bool(result.face_landmarks)

    if face_detected:
        lm  = result.face_landmarks[0]
        pts = np.array([[l.x*w, l.y*h] for l in lm])
        cx  = (np.min(pts[:,0]) + np.max(pts[:,0])) / 2
        cy  = (np.min(pts[:,1]) + np.max(pts[:,1])) / 2

        # ── EAR blink detection ──────────────────────
        ear       = get_ear(lm, w, h)
        eye_openness = ear
        threshold = ear_open_avg * BLINK_RATIO

        if calibration_frames < 30:
            # First 30 frames: build stable open average
            ear_open_avg = 0.9 * ear_open_avg + 0.1 * ear
            calibration_frames += 1
            if calibration_frames == 30:
                print(f"\n✓ Calibration complete! avg_open_ear={ear_open_avg:.4f}  threshold={ear_open_avg * BLINK_RATIO:.4f}\n")
        else:
            currently_closed = ear < threshold
            print(f"EAR={ear:.4f} thr={threshold:.4f} eyes_closed={eyes_closed} -> {currently_closed}")

            if not currently_closed:
                ear_open_avg = 0.97 * ear_open_avg + 0.03 * ear

            # Open -> Closed = blink onset
            if currently_closed and not eyes_closed:
                blink_detected  = True
                last_blink_time = now
                print(f">>> BLINK DETECTED! EAR={ear:.4f}  thr={threshold:.4f}")

                if (now - last_click_time) >= CLICK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    print("    -> CLICK fired")

            eyes_closed = currently_closed

        if blink_detected and (now - last_blink_time) > BLINK_FLAG_DUR:
            blink_detected = False

        # ===== LEFT EYE REGION =====
        # Eye corners for left eye
        left_eye_inner = lm[33]    # Inner corner
        left_eye_outer = lm[133]   # Outer corner
        left_eye_top = lm[159]     # Top
        left_eye_bottom = lm[145]  # Bottom
        
        # Left eye bounds
        left_eye_left = left_eye_inner.x
        left_eye_right = left_eye_outer.x
        left_eye_top_y = left_eye_top.y
        left_eye_bottom_y = left_eye_bottom.y
        
        # Left iris (pupil) position
        left_iris = lm[468]
        left_iris_x = left_iris.x
        left_iris_y = left_iris.y
        
        # ===== RIGHT EYE REGION =====
        # Eye corners for right eye
        right_eye_inner = lm[362]   # Inner corner
        right_eye_outer = lm[263]   # Outer corner
        right_eye_top = lm[386]     # Top
        right_eye_bottom = lm[374]  # Bottom
        
        # Right eye bounds
        right_eye_left = right_eye_outer.x
        right_eye_right = right_eye_inner.x
        right_eye_top_y = right_eye_top.y
        right_eye_bottom_y = right_eye_bottom.y
        
        # Right iris (pupil) position
        right_iris = lm[473]
        right_iris_x = right_iris.x
        right_iris_y = right_iris.y
        
        # ===== NORMALIZE IRIS POSITION WITHIN EYE REGION =====
        # This makes it INDEPENDENT of head movement
        # Range: 0 = left/top, 1 = right/bottom
        left_gaze_x = (left_iris_x - left_eye_left) / (left_eye_right - left_eye_left + 0.0001)
        left_gaze_y = (left_iris_y - left_eye_top_y) / (left_eye_bottom_y - left_eye_top_y + 0.0001)
        
        right_gaze_x = (right_iris_x - right_eye_left) / (right_eye_right - right_eye_left + 0.0001)
        right_gaze_y = (right_iris_y - right_eye_top_y) / (right_eye_bottom_y - right_eye_top_y + 0.0001)
        
        # Average both eyes (0.5 = center gaze, <0.5 = left, >0.5 = right)
        avg_gaze_x = (left_gaze_x + right_gaze_x) / 2
        avg_gaze_y = (left_gaze_y + right_gaze_y) / 2
        
        # ── Calculate cursor movement from gaze ──────
        # Convert to screen coordinates
        gaze_dx = (avg_gaze_x - 0.5) * sensitivity * screen_w * 2
        gaze_dy = (avg_gaze_y - 0.5) * sensitivity * screen_h * 2
        
        # Clamp gaze to valid range
        gx = max(0.02, min(0.98, 0.5 + gaze_dx / screen_w))
        gy = max(0.02, min(0.98, 0.5 + gaze_dy / screen_h))

        # ── Cursor EMA for extra smoothing ───────────
        if ema_x is None:
            ema_x, ema_y = gx, gy
        else:
            ema_x = EMA_ALPHA * gx + (1 - EMA_ALPHA) * ema_x
            ema_y = EMA_ALPHA * gy + (1 - EMA_ALPHA) * ema_y

        scr_x = max(0, min(int(ema_x * screen_w), screen_w - 1))
        scr_y = max(0, min(int(ema_y * screen_h), screen_h - 1))
        pyautogui.moveTo(scr_x, scr_y, duration=0)

        # ── Dwell click ──────────────────────────────
        if dwell_position is None:
            dwell_position   = (scr_x, scr_y)
            dwell_start_time = now
            dwell_fired      = False

        dist = np.hypot(scr_x - dwell_position[0], scr_y - dwell_position[1])

        if dist > DWELL_RADIUS:
            dwell_position   = (scr_x, scr_y)
            dwell_start_time = now
            dwell_progress   = 0.0
            dwell_fired      = False
        else:
            elapsed        = now - dwell_start_time
            dwell_progress = min(1.0, elapsed / DWELL_TIME)

            if dwell_progress >= 1.0 and not dwell_fired:
                if (now - last_dwell_click) >= DWELL_COOLDOWN:
                    pyautogui.click()
                    last_dwell_click = now
                    dwell_fired      = True
                    print(f"DWELL CLICK at ({scr_x},{scr_y})")

        # ── Visual overlay ────────────────────────────
        x1 = int(np.min(pts[:,0])); x2 = int(np.max(pts[:,0]))
        y1 = int(np.min(pts[:,1])); y2 = int(np.max(pts[:,1]))
        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
        cv2.circle(frame, (int(ema_x*w), int(ema_y*h)), 8, (0,0,255), -1)

        ear_col = (0,0,255) if (calibration_frames >= 30 and ear < threshold) else (255,255,255)
        cv2.putText(frame, f"EAR:{ear:.3f} thr:{threshold:.3f}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, ear_col, 2)
        cv2.putText(frame, f"avg:{ear_open_avg:.3f}  cal:{min(calibration_frames,30)}/30",
                    (10,55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180,180,180), 1)

        if dwell_progress > 0 and not dwell_fired:
            angle = int(360 * dwell_progress)
            cv2.ellipse(frame, (int(ema_x*w), int(ema_y*h)),
                        (18,18), -90, 0, angle, (0,255,255), 3)

        if blink_detected:
            cv2.putText(frame, "BLINK!", (10,90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,0,255), 3)
        if dwell_fired and (now - last_dwell_click) < 0.5:
            cv2.putText(frame, "DWELL CLICK!", (10,130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 3)

    else:
        ref_head_center = None
        ref_eye_center = None
        ema_x          = None
        ema_y          = None
        eyes_closed    = False
        dwell_position = None
        dwell_progress = 0.0
        dwell_fired    = False
        cv2.putText(frame, "No face detected", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    return frame


# ── Flask routes ─────────────────────────────────

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/calibration')
def calibration():
    return render_template('calibration.html')

@app.route('/communication')
def communication():
    return render_template('communication.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/debug')
def debug():
    return render_template('debug.html')

@app.route('/camera_feed')
def camera_feed():
    def generate():
        while True:
            ret, frame = camera.read()
            if not ret:
                break
            frame = process_frame(frame)
            _, buf = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/gaze/current')
def api_gaze_current():
    return jsonify({
        'status': 'success',
        'gaze_normalized': {'x': round(ema_x or 0.5, 4), 'y': round(ema_y or 0.5, 4)},
        'gaze_screen': {'x': screen_w//2, 'y': screen_h//2},
        'face_detected': face_detected,
        'blink_detected': blink_detected,
        'eye_openness': round(eye_openness, 4),
        'dwell_progress': round(dwell_progress, 3),
        'fps': 30
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'success',
        'system': {
            'camera_running': True,
            'face_detected': face_detected,
            'calibrated': calibration_frames >= 30
        },
        'gaze': {'normalized': {'x': ema_x or 0.5, 'y': ema_y or 0.5}},
        'dwell_progress': round(dwell_progress, 3)
    })

@app.route('/api/mouse/click', methods=['POST'])
def api_mouse_click():
    try:
        pyautogui.click()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/cursor/move', methods=['POST'])
def api_cursor_move():
    try:
        data = request.get_json()
        x = max(0, min(int(data.get('x', 0)), screen_w-1))
        y = max(0, min(int(data.get('y', 0)), screen_h-1))
        pyautogui.moveTo(x, y, duration=0)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/calibration/start', methods=['POST'])
def cal_start():
    return jsonify({'status': 'success', 'points': []})

@app.route('/api/calibration/point', methods=['POST'])
def cal_point():
    return jsonify({'status': 'success'})

@app.route('/api/calibration/calculate', methods=['POST'])
def cal_calc():
    return jsonify({'status': 'success', 'calibrated': True})

@app.route('/api/camera/status')
def cam_status():
    return jsonify({'status': 'success', 'running': True})

@app.route('/api/camera/start', methods=['POST'])
def cam_start():
    return jsonify({'status': 'success'})

@app.route('/api/camera/stop', methods=['POST'])
def cam_stop():
    return jsonify({'status': 'success'})

@app.route('/api/gesture/detect')
def gesture_detect():
    return jsonify({
        'status': 'success',
        'blink_detected': blink_detected,
        'eye_openness': round(eye_openness, 4),
        'face_detected': face_detected
    })

@app.route('/api/settings/get')
def settings_get():
    return jsonify({
        'status': 'success',
        'settings': {
            'dwell_time': DWELL_TIME,
            'sensitivity': sensitivity,
            'click_cooldown': CLICK_COOLDOWN
        }
    })

@app.route('/api/settings/update', methods=['POST'])
def settings_update():
    global sensitivity, CLICK_COOLDOWN, DWELL_TIME
    try:
        data = request.get_json()
        if 'sensitivity' in data:
            sensitivity = float(data['sensitivity'])
        if 'click_cooldown' in data:
            CLICK_COOLDOWN = float(data['click_cooldown'])
        if 'dwell_time' in data:
            DWELL_TIME = float(data['dwell_time'])
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('ui/static', path)

@app.route('/send_static/<path:path>')
def send_static(path):
    return send_from_directory('ui/static', path)

# ── Auto open browser ─────────────────────────────
threading.Thread(
    target=lambda: (time.sleep(1.5), webbrowser.open('http://127.0.0.1:5000')),
    daemon=True
).start()

if __name__ == '__main__':
    print("=" * 55)
    print("  AssistiveHands  |  BLINK + DWELL CLICK")
    print(f"  Screen : {screen_w} x {screen_h}")
    print(f"  EMA alpha  : {EMA_ALPHA}   Sensitivity: {sensitivity}")
    print(f"  Blink cooldown : {CLICK_COOLDOWN}s   ratio: {BLINK_RATIO}")
    print(f"  Dwell time     : {DWELL_TIME}s   radius: {DWELL_RADIUS}px")
    print("  Pehle 30 frames calibration — phir blink/dwell kaam karega")
    print("=" * 55)
    app.run(host='127.0.0.1', port=5000, debug=False)