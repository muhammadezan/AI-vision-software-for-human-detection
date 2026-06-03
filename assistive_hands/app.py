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
import math

app = Flask(__name__, template_folder='ui/templates', static_folder='ui/static')

# ── Camera ────────────────────────────────────────────────────────────────────
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ── MediaPipe ─────────────────────────────────────────────────────────────────
# output_face_blendshapes=True populates the full 478-pt list including iris
# landmarks 468 (left iris centre) and 473 (right iris centre).
base_opts = base_options.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_opts,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)
last_ts = 0

def now_ms():
    return int(time.time() * 1000)

# ── PyAutoGUI ─────────────────────────────────────────────────────────────────
pyautogui.FAILSAFE = False
pyautogui.MINIMUM_DURATION = 0
pyautogui.PAUSE = 0
screen_w, screen_h = pyautogui.size()

# ── Blink state ───────────────────────────────────────────────────────────────
face_detected      = False
blink_detected     = False
eye_openness       = 1.0
eyes_closed        = False
last_blink_time    = 0.0
last_click_time    = 0.0
CLICK_COOLDOWN     = 1.2
BLINK_FLAG_DUR     = 0.4
ear_open_avg       = 0.30
BLINK_RATIO        = 0.60
calibration_frames = 0

# ── Dwell state ───────────────────────────────────────────────────────────────
dwell_position   = None
dwell_start_time = 0.0
dwell_progress   = 0.0
dwell_fired      = False
last_dwell_click = 0.0
DWELL_RADIUS     = 60
DWELL_TIME       = 1.5
DWELL_COOLDOWN   = 1.5

# ── Cursor positioning constants ──────────────────────────────────────────────
# How much of the frame edge is "already at screen edge".
# Shrink HEAD_MARGIN if cursor doesn't reach screen corners when you look there.
HEAD_MARGIN  = 0.01

# Iris-position gain: iris sits in ~[0.3,0.7] of the eye box.
# GAZE_GAIN stretches that to ±[0,1].  3.5 = 1/0.28 stretch for 80% iris weight.
GAZE_GAIN    = 3.5

# Blend weights (must sum to 1.0)
HEAD_WEIGHT  = 0.20   # 20% stable head-pose via nose tip
GAZE_WEIGHT  = 0.80   # 80% fine-grained iris offset - primary control

# Dead zone: cursor won't move unless raw position changes by this fraction.
# Kills micro-jitter from camera noise.
DEAD_ZONE    = 0.004   # ~0.4% of screen width/height; raise to 0.008 if still shaky

# ── Debug frame counter ───────────────────────────────────────────────────────
_debug_frame = 0

# ── One-Euro Filter ───────────────────────────────────────────────────────────
# Much better than EMA for cursor control:
#   - at low speed (nearly still) → heavy smoothing, kills jitter
#   - at high speed (intentional movement) → light smoothing, stays responsive
# Reference: Casiez et al. 2012, "1€ Filter"

class OneEuroFilter:
    """Scalar 1€ filter.  Call .filter(value, timestamp_sec) each frame."""

    def __init__(self, freq=30.0, mincutoff=1.0, beta=0.007, dcutoff=1.0):
        # freq      – nominal sample rate (Hz); updated dynamically each call
        # mincutoff – lower = smoother when still, but adds lag
        # beta      – higher = faster response when moving, but more jitter
        # dcutoff   – cutoff for the derivative (leave at 1.0)
        self.freq      = freq
        self.mincutoff = mincutoff
        self.beta      = beta
        self.dcutoff   = dcutoff
        self._x        = None   # previous filtered value
        self._dx       = 0.0    # previous filtered derivative
        self._last_t   = None

    @staticmethod
    def _alpha(cutoff, freq):
        te  = 1.0 / freq
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def filter(self, x, t):
        if self._last_t is not None:
            dt = t - self._last_t
            if dt > 0:
                self.freq = 1.0 / dt
        self._last_t = t

        if self._x is None:   # first sample — no history yet
            self._x  = x
            self._dx = 0.0
            return x

        # Derivative with low-pass filter
        dx_raw       = (x - self._x) * self.freq
        a_d          = self._alpha(self.dcutoff, self.freq)
        self._dx     = a_d * dx_raw + (1.0 - a_d) * self._dx

        # Adaptive cutoff based on speed
        cutoff       = self.mincutoff + self.beta * abs(self._dx)
        a            = self._alpha(cutoff, self.freq)
        self._x      = a * x + (1.0 - a) * self._x
        return self._x

    def reset(self):
        self._x      = None
        self._dx     = 0.0
        self._last_t = None


# One filter per axis
oef_x = OneEuroFilter(freq=30.0, mincutoff=0.8, beta=0.005)
oef_y = OneEuroFilter(freq=30.0, mincutoff=0.8, beta=0.005)

# Smoothed cursor position (screen fraction [0,1])
cur_x = None
cur_y = None

# Current gaze position for API response
current_gaze_x = 0.5
current_gaze_y = 0.5
current_cursor_x = 0
current_cursor_y = 0


# ── EAR (unchanged) ───────────────────────────────────────────────────────────
def get_ear(lm, w, h):
    def d(a, b):
        return np.hypot(a[0] - b[0], a[1] - b[1])
    try:
        lp = [[lm[i].x * w, lm[i].y * h] for i in [33, 160, 158, 133, 153, 144]]
        rp = [[lm[i].x * w, lm[i].y * h] for i in [362, 385, 387, 263, 373, 380]]
        l = d(lp[1], lp[4]) / (d(lp[0], lp[3]) + 1e-6)
        r = d(rp[1], rp[4]) / (d(rp[0], rp[3]) + 1e-6)
        return float(max(0.0, (l + r) / 2.0))
    except Exception as e:
        print(f"EAR err: {e}")
        return 1.0


# ── process_frame ─────────────────────────────────────────────────────────────
def process_frame(frame):
    global last_ts
    global blink_detected, face_detected, eye_openness
    global last_blink_time, last_click_time, eyes_closed, ear_open_avg
    global dwell_position, dwell_start_time, dwell_progress, dwell_fired
    global last_dwell_click, calibration_frames, _debug_frame
    global cur_x, cur_y, current_gaze_x, current_gaze_y, current_cursor_x, current_cursor_y

    h, w = frame.shape[:2]
    now  = time.time()
    _debug_frame += 1

    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    ts = now_ms()
    if ts <= last_ts:
        ts = last_ts + 1
    last_ts = ts

    result        = face_landmarker.detect_for_video(mp_image, ts)
    face_detected = bool(result.face_landmarks)

    if face_detected:
        lm = result.face_landmarks[0]

        # ── Blink / EAR (unchanged logic) ─────────────────────────────────
        ear       = get_ear(lm, w, h)
        eye_openness = ear
        threshold = ear_open_avg * BLINK_RATIO

        if calibration_frames < 30:
            ear_open_avg = 0.9 * ear_open_avg + 0.1 * ear
            calibration_frames += 1
            if calibration_frames == 30:
                print(f"\n✓ Calibration done  avg_ear={ear_open_avg:.4f}  thr={ear_open_avg*BLINK_RATIO:.4f}\n")
        else:
            currently_closed = ear < threshold
            if not currently_closed:
                ear_open_avg = 0.97 * ear_open_avg + 0.03 * ear
            if currently_closed and not eyes_closed:
                blink_detected  = True
                last_blink_time = now
                print(f">>> BLINK  EAR={ear:.4f}  thr={threshold:.4f}")
                if (now - last_click_time) >= CLICK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    print("    -> CLICK fired")
            eyes_closed = currently_closed

        if blink_detected and (now - last_blink_time) > BLINK_FLAG_DUR:
            blink_detected = False

        # ── HEAD POSE: use nose tip (lm[1]) — far more stable than bbox ───
        # lm[1] is the nose tip; it sits near the face centre and barely
        # wobbles compared with the bbox extremes which jump with any landmark
        # that touches the edge.
        nose_x = lm[1].x   # already normalised to [0,1] by MediaPipe
        nose_y = lm[1].y

        # Remap [HEAD_MARGIN, 1-HEAD_MARGIN] → [0, 1]
        head_x = (nose_x - HEAD_MARGIN) / (1.0 - 2 * HEAD_MARGIN)
        head_y = (nose_y - HEAD_MARGIN) / (1.0 - 2 * HEAD_MARGIN)
        head_x = max(0.0, min(1.0, head_x))
        head_y = max(0.0, min(1.0, head_y))
        # Mirror x: nose moves left in frame → cursor should move right
        head_x = 1.0 - head_x

        # ── IRIS GAZE: fine offset ─────────────────────────────────────────
        gaze_x = 0.5   # neutral fallback
        gaze_y = 0.5

        if len(lm) >= 478:
            try:
                # Left eye corners: lm[33]=inner, lm[133]=outer
                # Right eye corners: lm[362]=inner, lm[263]=outer
                # Use min/max so the denominator is always positive regardless
                # of which corner is numerically larger.
                l_xmin = min(lm[33].x,  lm[133].x)
                l_xmax = max(lm[33].x,  lm[133].x)
                l_ymin = min(lm[159].y, lm[145].y)
                l_ymax = max(lm[159].y, lm[145].y)

                r_xmin = min(lm[362].x, lm[263].x)
                r_xmax = max(lm[362].x, lm[263].x)
                r_ymin = min(lm[386].y, lm[374].y)
                r_ymax = max(lm[386].y, lm[374].y)

                # Iris position within eye box → [0,1]
                lg_x = (lm[468].x - l_xmin) / (l_xmax - l_xmin + 1e-6)
                lg_y = (lm[468].y - l_ymin) / (l_ymax - l_ymin + 1e-6)
                rg_x = (lm[473].x - r_xmin) / (r_xmax - r_xmin + 1e-6)
                rg_y = (lm[473].y - r_ymin) / (r_ymax - r_ymin + 1e-6)

                avg_gx = max(0.0, min(1.0, (lg_x + rg_x) / 2.0))
                avg_gy = max(0.0, min(1.0, (lg_y + rg_y) / 2.0))

                # Stretch ~[0.3,0.7] range to [0,1] and mirror x
                gaze_x = max(0.0, min(1.0, (avg_gx - 0.5) * GAZE_GAIN + 0.5))
                gaze_y = max(0.0, min(1.0, (avg_gy - 0.5) * GAZE_GAIN + 0.5))
                gaze_x = 1.0 - gaze_x   # mirror to match head-pose
                gaze_y = 1.0 - gaze_y   # mirror Y-axis for correct vertical direction

                if _debug_frame % 30 == 0:
                    print(
                        f"[GAZE] iris=({avg_gx:.3f},{avg_gy:.3f})  "
                        f"norm=({gaze_x:.3f},{gaze_y:.3f})  "
                        f"nose=({nose_x:.3f},{nose_y:.3f})  "
                        f"head=({head_x:.3f},{head_y:.3f})"
                    )

            except (IndexError, ZeroDivisionError) as e:
                print(f"[WARN] iris err: {e}")

        # ── Blend head + gaze ─────────────────────────────────────────────
        # Eyes are primary control; head adds additive offset for stability + range
        head_offset_x = (head_x - 0.5) * 0.6   # head contributes ±30% offset range
        head_offset_y = (head_y - 0.5) * 0.6

        raw_x = max(0.0, min(1.0, gaze_x + head_offset_x))
        raw_y = max(0.0, min(1.0, gaze_y + head_offset_y))
        raw_x = max(0.02, min(0.98, raw_x))
        raw_y = max(0.02, min(0.98, raw_y))

        # ── Dead zone — ignore micro-movements smaller than DEAD_ZONE ─────
        # This is the primary jitter killer: if the blended position hasn't
        # moved enough, we stay at the last cursor position instead of
        # transmitting camera noise to the cursor.
        if cur_x is None:
            cur_x, cur_y = raw_x, raw_y
        else:
            if abs(raw_x - cur_x) > DEAD_ZONE:
                cur_x = raw_x
            if abs(raw_y - cur_y) > DEAD_ZONE:
                cur_y = raw_y

        # ── One-Euro Filter — adaptive smoothing ─────────────────────────
        # Replaces EMA.  Kills jitter when still, stays fast when moving.
        smooth_x = oef_x.filter(cur_x, now)
        smooth_y = oef_y.filter(cur_y, now)

        # Update global gaze position for API
        current_gaze_x = smooth_x
        current_gaze_y = smooth_y

        scr_x = max(0, min(int(smooth_x * screen_w), screen_w - 1))
        scr_y = max(0, min(int(smooth_y * screen_h), screen_h - 1))
        
        # Update global cursor position for API
        current_cursor_x = scr_x
        current_cursor_y = scr_y

        if _debug_frame % 30 == 0:
            print(f"[CURSOR] smooth=({smooth_x:.3f},{smooth_y:.3f})  px=({scr_x},{scr_y})")

        pyautogui.moveTo(scr_x, scr_y, duration=0)

        # ── Dwell (unchanged logic) ────────────────────────────────────────
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

        # ── Overlay ───────────────────────────────────────────────────────
        # Nose-tip dot (green) — shows what head-pose is tracking
        nose_px = int(lm[1].x * w)
        nose_py = int(lm[1].y * h)
        cv2.circle(frame, (nose_px, nose_py), 5, (0, 255, 0), -1)
        # Cursor position dot (red) on frame
        cv2.circle(frame, (int(smooth_x * w), int(smooth_y * h)), 8, (0, 0, 255), -1)

        ear_col = (0, 0, 255) if (calibration_frames >= 30 and ear < threshold) else (255, 255, 255)
        cv2.putText(frame, f"EAR:{ear:.3f} thr:{threshold:.3f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, ear_col, 2)
        cv2.putText(frame, f"avg:{ear_open_avg:.3f}  cal:{min(calibration_frames,30)}/30",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        if dwell_progress > 0 and not dwell_fired:
            angle = int(360 * dwell_progress)
            cv2.ellipse(frame, (int(smooth_x * w), int(smooth_y * h)),
                        (18, 18), -90, 0, angle, (0, 255, 255), 3)
        if blink_detected:
            cv2.putText(frame, "BLINK!", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 3)
        if dwell_fired and (now - last_dwell_click) < 0.5:
            cv2.putText(frame, "DWELL CLICK!", (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

    else:
        # Face lost — reset all filters and state
        oef_x.reset()
        oef_y.reset()
        cur_x          = None
        cur_y          = None
        eyes_closed    = False
        dwell_position = None
        dwell_progress = 0.0
        dwell_fired    = False
        cv2.putText(frame, "No face detected", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return frame


# ─────────────────────────────────────────────────────────────────────────────
# FLASK ROUTES & VIDEO STREAMING
# ─────────────────────────────────────────────────────────────────────────────

def generate_frames():
    """Video stream generator for Flask."""
    while True:
        ret, frame = camera.read()
        if not ret:
            time.sleep(0.01)  # Small delay if frame read fails
            continue

        # Process frame with eye-tracking logic
        processed_frame = process_frame(frame)

        # Encode frame to JPEG with quality compression
        ret, buffer = cv2.imencode('.jpg', processed_frame, 
                                    [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
               + frame_bytes + b'\r\n')
        
        # Add small delay to prevent 100% CPU usage
        time.sleep(0.01)


@app.route('/')
def dashboard():
    """Serve the main dashboard."""
    return render_template('dashboard.html')


@app.route('/video_feed')
def video_feed():
    """Stream video with eye-tracking overlay."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/camera_feed')
def camera_feed():
    """Stream video with eye-tracking overlay (desktop camera endpoint)."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/api/status')
def api_status():
    """Get current tracking status."""
    return jsonify({
        'face_detected': face_detected,
        'blink_detected': blink_detected,
        'eye_openness': eye_openness,
        'calibration_frames': min(calibration_frames, 30),
        'dwell_progress': dwell_progress,
    })


@app.route('/api/gaze/current')
def api_gaze_current():
    """Get current gaze position."""
    return jsonify({
        'gaze_x': current_gaze_x,
        'gaze_y': current_gaze_y,
        'cursor_x': current_cursor_x,
        'cursor_y': current_cursor_y,
        'screen_width': screen_w,
        'screen_height': screen_h,
        'face_detected': face_detected,
        'timestamp': time.time(),
    })


@app.route('/api/android/status')
def api_android_status():
    """Get Android camera status (stub for dashboard compatibility)."""
    return jsonify({
        'connected': False,
        'status': 'Using desktop camera',
        'ip': 'N/A',
        'port': 'N/A',
    })


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset tracking state."""
    global cur_x, cur_y, dwell_position, dwell_fired, eyes_closed
    global calibration_frames, ear_open_avg, last_blink_time
    
    cur_x = None
    cur_y = None
    dwell_position = None
    dwell_fired = False
    eyes_closed = False
    calibration_frames = 0
    ear_open_avg = 0.30
    last_blink_time = 0.0
    
    oef_x.reset()
    oef_y.reset()
    
    return jsonify({'status': 'reset'})


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page for calibration and configuration."""
    if request.method == 'POST':
        global HEAD_WEIGHT, GAZE_WEIGHT, BLINK_RATIO, DWELL_TIME
        
        data = request.get_json()
        if 'head_weight' in data:
            HEAD_WEIGHT = float(data['head_weight'])
        if 'gaze_weight' in data:
            GAZE_WEIGHT = float(data['gaze_weight'])
        if 'blink_ratio' in data:
            BLINK_RATIO = float(data['blink_ratio'])
        if 'dwell_time' in data:
            DWELL_TIME = float(data['dwell_time'])
        
        return jsonify({'status': 'updated'})
    
    return render_template('settings.html', 
                          head_weight=HEAD_WEIGHT,
                          gaze_weight=GAZE_WEIGHT,
                          blink_ratio=BLINK_RATIO,
                          dwell_time=DWELL_TIME)


@app.route('/calibration')
def calibration():
    """Calibration interface."""
    return render_template('calibration.html')


if __name__ == '__main__':
    print("=" * 60)
    print("[EYE GAZE TRACKING] - FLASK DASHBOARD")
    print("=" * 60)
    print("[*] Opening browser at http://127.0.0.1:5000")
    print("=" * 60)
    
    # Open browser after small delay
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://127.0.0.1:5000')
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run Flask app
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True, use_reloader=False)