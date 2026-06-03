// assistive_hands/ui/static/js/dashboard.js

/* Dashboard JavaScript */

const performanceMonitor = new PerformanceMonitor();
let gazeUpdateInterval;
let sessionDurationInterval;
let commandCount = 0;
let gazeControlEnabled = true;  // Toggle to disable gaze cursor control
let cursorMoveInterval = null;
let lastCursorX = null;
let lastCursorY = null;
let cursorMoveCount = 0;  // For debugging

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Dashboard loaded');
    
    try {
        // Start camera with better error handling
        try {
            const camResp = await api.post('/api/camera/start');
            console.log('Camera start response:', camResp);
            if (!camResp || camResp.status !== 'success') {
                throw new Error(camResp?.message || 'Camera start failed');
            }
            showToast('Camera started', 'success');
        } catch (err) {
            console.error('Camera initialization error:', err);
            showToast('Camera error: ' + err.message, 'danger');
        }

        // MJPEG stream is continuous - don't add query params that would break it
        // The <img src> is set in the HTML template and will auto-stream MJPEG
        const cameraFeed = document.getElementById('cameraFeed');
        if (cameraFeed) {
            // Don't add ?ts= to MJPEG streams - it breaks the continuous stream
            // The stream is already connected via the HTML src attribute
            console.log('Camera feed element found and ready for MJPEG streaming');
        }

        // Initialize gaze updates
        startGazeUpdates();
        
        // Initialize session duration tracker
        startSessionTracker();

        // Setup event listeners
        setupButtonListeners();
        
        // Load system status
        updateSystemStatus();
        
        // Add keyboard shortcut to disable gaze control
        setupKeyboardShortcuts();

    } catch (error) {
        console.error('Dashboard initialization error:', error);
        showToast('Error initializing dashboard', 'danger');
    }
});

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // SPACE = Toggle gaze control on/off
        if (e.code === 'Space') {
            e.preventDefault();
            toggleGazeControl(!gazeControlEnabled);
        }
        // ESC = Emergency disable
        if (e.code === 'Escape') {
            e.preventDefault();
            toggleGazeControl(false);
        }
        // M = Mouse mode (disable gaze)
        if (e.code === 'KeyM') {
            e.preventDefault();
            toggleGazeControl(false);
        }
    });
}

function toggleGazeControl(enabled) {
    gazeControlEnabled = enabled;
    const statusEl = document.getElementById('gazeControlStatus');
    if (statusEl) {
        statusEl.textContent = enabled ? '✓ ENABLED' : '✗ DISABLED';
        statusEl.className = enabled ? 'text-success' : 'text-danger';
    }
    const status = enabled ? 'ENABLED' : 'DISABLED';
    console.log(`Gaze control ${status}`);
    showToast(`Gaze control ${status} (Space/ESC to toggle)`, enabled ? 'success' : 'warning');
}

function setupButtonListeners() {
    const recalibrateBtn = document.getElementById('recalibrateBtn');
    const textEntryBtn = document.getElementById('textEntryBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    recalibrateBtn?.addEventListener('click', () => {
        window.location.href = '/calibration';
    });

    textEntryBtn?.addEventListener('click', () => {
        window.location.href = '/communication';
    });

    voiceBtn?.addEventListener('click', () => {
        showToast('Voice commands module coming soon', 'info');
    });

    pauseBtn?.addEventListener('click', () => {
        toggleSystemPause(pauseBtn);
    });
}

function startGazeUpdates() {
    gazeUpdateInterval = setInterval(async () => {
        try {
            const response = await api.get('/api/gaze/current');
            
            if (response.status === 'success') {
                const { gaze_normalized, gaze_screen, face_detected, eye_openness, blink_detected, fps } = response;

                // Viewport coords for on-screen gaze cursor
                const viewX = gaze_normalized.x * window.innerWidth;
                const viewY = gaze_normalized.y * window.innerHeight;
                // updateGazeCursor(viewX, viewY);

                // Screen coords for actual system cursor
                if (face_detected) {
                    moveSystemCursor(gaze_screen.x, gaze_screen.y);
                }

                // FPS display
                if (fps > 0) {
                    document.getElementById('responseTime').textContent = (1/fps).toFixed(2) + 's';
                }

                // Face detection status
                const faceDetectionStatus = document.getElementById('faceDetectionStatus');
                if (faceDetectionStatus) {
                    if (face_detected) {
                        faceDetectionStatus.textContent = 'Active';
                        faceDetectionStatus.className = 'status-badge status-active';
                    } else {
                        faceDetectionStatus.textContent = 'Inactive';
                        faceDetectionStatus.className = 'status-badge bg-warning';
                    }
                }

                // Double blink detection - SIMPLE VERSION
if (blink_detected) {
    recordCommand();
    if (!window.lastBlinkTime) {
        window.lastBlinkTime = Date.now();
    } else {
        let timeBetween = Date.now() - window.lastBlinkTime;
        if (timeBetween > 80 && timeBetween < 500) {
            // Double blink! Send click
            console.log('Double blink detected!');
            api.post('/api/mouse/click').catch(() => {});
            window.lastBlinkTime = null;
        } else {
            window.lastBlinkTime = Date.now();
        }
    }
}
                performanceMonitor.recordFrame();
            }
        } catch (error) {
            console.error('Gaze update error:', error);
        }
    }, 50); // Update every 50ms for smoother movement 
}

// function updateGazeCursor(viewX, viewY) {
//     let cursor = document.getElementById('gazeCursor');
//     if (!cursor) {
//         cursor = document.createElement('div');
//         cursor.id = 'gazeCursor';
//         cursor.style.cssText = `
//             position: fixed;
//             width: 24px; height: 24px;
//             border: 3px solid #00ff88;
//             border-radius: 50%;
//             background: rgba(0,255,136,0.12);
//             pointer-events: none;
//             z-index: 9999;
//             transform: translate(-50%,-50%);
//             box-shadow: 0 0 14px rgba(0,255,136,0.7);
//             transition: left 0.02s ease-out, top 0.02s ease-out;
//         `;
//         document.body.appendChild(cursor);
//     }
//     cursor.style.left = viewX + 'px';
//     cursor.style.top  = viewY + 'px';
// }

function moveSystemCursor(screenX, screenY) {
    if (!gazeControlEnabled) return;
    const rx = Math.round(screenX);
    const ry = Math.round(screenY);
    if (lastCursorX !== null && Math.abs(rx - lastCursorX) < 2 && Math.abs(ry - lastCursorY) < 2) return;
    lastCursorX = rx;
    lastCursorY = ry;
    api.post('/api/cursor/move', { x: rx, y: ry }).catch(() => {});
}

function startSessionTracker() {
    sessionDurationInterval = setInterval(() => {
        const sessionTimeEl = document.getElementById('sessionTime');
        if (sessionTimeEl) {
            const uptime = performanceMonitor.getUptime();
            sessionTimeEl.textContent = formatTime(Math.floor(uptime / 1000));
        }
    }, 1000);
}

function updateSystemStatus() {
    setInterval(async () => {
        try {
            const response = await api.get('/api/status');
            if (response.status === 'success') {
                const { system } = response;
                
                if (!system.camera_running) {
                    document.getElementById('recordingBadge').classList.remove('bg-success');
                    document.getElementById('recordingBadge').classList.add('bg-danger');
                    document.getElementById('recordingBadge').innerHTML = '<i class="fas fa-circle"></i> Offline';
                }
            }
        } catch (error) {
            console.error('Status update error:', error);
        }
    }, 5000);
}

function recordCommand() {
    commandCount++;
    const commandCountEl = document.getElementById('commandCount');
    if (commandCountEl) {
        commandCountEl.textContent = commandCount;
    }
}

function toggleSystemPause(btn) {
    const isPaused = btn.classList.contains('active');
    
    if (isPaused) {
        btn.classList.remove('active');
        btn.innerHTML = '<i class="fas fa-pause"></i> Pause System';
        api.post('/api/camera/start');
    } else {
        btn.classList.add('active');
        btn.innerHTML = '<i class="fas fa-play"></i> Resume System';
        api.post('/api/camera/stop');
    }
}


// Move system cursor based on gaze
function moveSystemCursor(x, y) {
    // ONLY move if gaze control is ENABLED
    if (!gazeControlEnabled) {
        if (cursorMoveInterval) {
            clearInterval(cursorMoveInterval);
            cursorMoveInterval = null;
        }
        return;
    }
    
    // Store latest gaze position first
    window.lastGazeX = x;
    window.lastGazeY = y;
    
    // Immediately send cursor move (don't throttle too much - causes lag)
    const roundedX = Math.round(x);
    const roundedY = Math.round(y);
    
    // Only move if position actually changed significantly
    if (!lastCursorX || Math.abs(roundedX - lastCursorX) > 20 || Math.abs(roundedY - lastCursorY) > 20) {
        // Send to backend immediately
        api.post('/api/cursor/move', { x: roundedX, y: roundedY })
            .then(resp => {
                lastCursorX = roundedX;
                lastCursorY = roundedY;
                cursorMoveCount++;
                
                if (cursorMoveCount % 100 === 0) {
                    console.log(`Cursor moves: ${cursorMoveCount}, Last pos: (${roundedX}, ${roundedY})`);
                }
                
                if (resp && resp.cursor_enabled === false) {
                    console.warn('Cursor control disabled:', resp.message);
                    showToast('Cursor control disabled - may need admin privileges', 'warning');
                }
            })
            .catch(err => {
                console.error('Cursor move API error:', err);
                if (err.response?.status === 403) {
                    showToast('Admin privileges required for cursor control', 'danger');
                }
            });
    }
}

// Cleanup on page unload - do NOT stop camera, it must keep running across pages
window.addEventListener('beforeunload', () => {
    clearInterval(gazeUpdateInterval);
    clearInterval(sessionDurationInterval);
});