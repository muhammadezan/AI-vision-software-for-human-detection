// assistive_hands/ui/static/js/communication.js

/* Communication JavaScript */

let displayText = '';
let dwellTime = 1.0;
let gazeUpdateInterval;
const mapper = new GazeElementMapper();
const dwellTimers = new Map();

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Communication page loaded');

    try {
        // Start camera
        await api.post('/api/camera/start');
        showToast('Camera started', 'success');

        // Initialize keyboard
        initializeKeyboard();

        // Initialize quick phrases
        initializeQuickPhrases();

        // Setup controls
        setupControls();

        // Start gaze tracking
        startGazeTracking();

    } catch (error) {
        console.error('Communication initialization error:', error);
        showToast('Error initializing communication interface', 'danger');
    }
});

function initializeKeyboard() {
    const keyboardBtns = document.querySelectorAll('.keyboard-btn');

    keyboardBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            handleKeyPress(btn.dataset.key, btn);
        });
    });

    // Register after layout so getBoundingClientRect is accurate
    requestAnimationFrame(() => {
        keyboardBtns.forEach(btn => {
            const key = btn.dataset.key;
            const rect = btn.getBoundingClientRect();
            mapper.registerElement(
                `key-${key}`,
                rect.left + window.scrollX,
                rect.top  + window.scrollY,
                rect.width,
                rect.height,
                () => btn.classList.add('hovered'),
                () => btn.classList.remove('hovered')
            );
        });
        console.log(`Registered ${keyboardBtns.length} keyboard buttons for gaze mapping`);
    });
}

function initializeQuickPhrases() {
    const phraseBtns = document.querySelectorAll('.phrase-btn');

    phraseBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const phrase = btn.dataset.phrase;
            addText(phrase);
            tts.speak(phrase);
        });
    });
}

function setupControls() {
    console.log('=== Setting up controls ===');
    
    const speakBtn = document.getElementById('speakBtn');
    const clearBtn = document.getElementById('clearBtn');
    const dwellTimeInput = document.getElementById('dwellTimeInput');

    console.log('Speak Button found:', !!speakBtn);
    console.log('Clear Button found:', !!clearBtn);

    // Speak button - DIRECT IMPLEMENTATION
    if (speakBtn) {
        speakBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('SPEAK BUTTON CLICKED');
            console.log('Display text:', displayText);
            console.log('Display text length:', displayText.length);
            
            if (!displayText || displayText.trim().length === 0) {
                alert('No text to speak!');
                return;
            }
            
            try {
                // Use Web Speech API directly
                const text = displayText;
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 1;
                utterance.pitch = 1;
                utterance.volume = 1;
                utterance.lang = 'en-US';
                
                utterance.onstart = function() {
                    console.log('Speech started');
                    alert('Speaking: ' + text.substring(0, 50));
                };
                
                utterance.onend = function() {
                    console.log('Speech ended');
                };
                
                utterance.onerror = function(e) {
                    console.error('Speech error:', e);
                    alert('Speech error: ' + e.error);
                };
                
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utterance);
                console.log('Speech synthesis started');
                
            } catch (error) {
                console.error('Error:', error);
                alert('Error: ' + error.message);
            }
            
            return false;
        };
    }

    // Clear button
    if (clearBtn) {
        clearBtn.onclick = function(e) {
            e.preventDefault();
            clearText();
            return false;
        };
    }

    // Dwell time input
    if (dwellTimeInput) {
        dwellTimeInput.addEventListener('input', (e) => {
            dwellTime = parseFloat(e.target.value) || 1.0;
        });
    }
    
    console.log('Controls setup complete');
}

function startGazeTracking() {
    gazeUpdateInterval = setInterval(async () => {
        try {
            const response = await api.get('/api/gaze/current');

            if (response.status === 'success') {
                const { gaze_normalized, gaze_screen, face_detected } = response;

                // Convert normalized gaze (0-1) to VIEWPORT pixels for element hit-testing
                // getBoundingClientRect() returns viewport coords, so we must match that
                const viewX = gaze_normalized.x * window.innerWidth;
                const viewY = gaze_normalized.y * window.innerHeight;

                // Update on-screen gaze cursor (viewport coords)
                updateGazeCursor(viewX, viewY);

                // Update keyboard element mapping (viewport coords)
                mapper.updateGaze(viewX, viewY);

                // Trigger dwell timer for hovered key
                updateDwellTimers();

                // Move actual system cursor (screen pixels)
                if (face_detected) {
                    moveSystemCursor(gaze_screen.x, gaze_screen.y);
                }
            }
        } catch (error) {
            console.error('Gaze tracking error:', error);
        }
    }, 50);
}

function updateGazeCursor(viewX, viewY) {
    let cursor = document.getElementById('gazeCursor');
    if (!cursor) {
        cursor = document.createElement('div');
        cursor.id = 'gazeCursor';
        cursor.style.cssText = `
            position: fixed;
            width: 22px; height: 22px;
            border: 3px solid #00ff88;
            border-radius: 50%;
            background: rgba(0,255,136,0.15);
            pointer-events: none;
            z-index: 9999;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 12px rgba(0,255,136,0.6);
            transition: left 0.05s, top 0.05s;
        `;
        document.body.appendChild(cursor);
    }
    cursor.style.left = viewX + 'px';
    cursor.style.top  = viewY + 'px';
}

function moveSystemCursor(screenX, screenY) {
    api.post('/api/cursor/move', { x: Math.round(screenX), y: Math.round(screenY) })
       .catch(() => {});
}

function handleKeyPress(key, btn) {
    console.log(`Key pressed: ${key}`);
    
    // Update local display
    if (key === 'Enter') {
        addText('\n');
    } else if (key === 'Space') {
        addText(' ');
    } else if (key === 'Backspace' || key === '⌫') {
        if (displayText.length > 0) {
            displayText = displayText.slice(0, -1);
        }
    } else if (key !== 'Shift') {
        addText(key);
    }

    updateTextDisplay();

    // Send key press to system keyboard (optional - can be disabled)
    const sendToSystem = document.getElementById('sendToSystemCheckbox')?.checked ?? false;
    if (sendToSystem) {
        sendKeyToSystem(key);
    }

    // Visual feedback
    btn.classList.add('active');
    setTimeout(() => btn.classList.remove('active'), 100);
}

async function sendKeyToSystem(key) {
    // Send key press to the system keyboard
    try {
        const keyMap = {
            'Enter': 'enter',
            'Space': 'space',
            'Backspace': 'backspace',
            '⌫': 'backspace',
            'Tab': 'tab',
        };
        
        const systemKey = keyMap[key] || key.toLowerCase();
        
        const response = await api.post('/api/keyboard/press', {
            key: systemKey
        });
        
        if (response.status !== 'success') {
            console.error('Failed to send key to system:', response.message);
        }
    } catch (error) {
        console.error('Error sending key to system:', error);
    }
}

function addText(text) {
    displayText += text;
    updateTextDisplay();
}

function clearText() {
    displayText = '';
    updateTextDisplay();
    showToast('Text cleared', 'info');
}

function updateTextDisplay() {
    const displayEl = document.getElementById('displayText');
    const charCountEl = document.querySelector('[id="charCount"]');

    if (displayEl) {
        displayEl.textContent = displayText || 'Start typing...';
    }

    if (charCountEl) {
        charCountEl.textContent = `Character count: ${displayText.length}`;
    }
}

function updateDwellTimers() {
    const currentElement = mapper.currentElement;

    if (!currentElement) {
        // Gaze left all buttons – cancel all timers
        dwellTimers.forEach(timer => timer.stop());
        dwellTimers.clear();
        // Remove any progress rings
        document.querySelectorAll('.keyboard-btn').forEach(b => b.classList.remove('dwell-active'));
        return;
    }

    const elementId = currentElement.id;

    // OPTION B: IGNORE keyboard buttons - no auto click
    if (elementId && elementId.startsWith('key-')) {
        // Do nothing for keyboard buttons
        return;
    }

    // Already tracking this element
    if (dwellTimers.has(elementId)) return;

    // Cancel timers for other elements
    dwellTimers.forEach((timer, id) => {
        if (id !== elementId) {
            timer.stop();
            dwellTimers.delete(id);
        }
    });

    // Find the actual button for this element
    const keyName = elementId.replace('key-', '');
    const keyBtn = document.querySelector(`[data-key="${keyName}"]`);
    if (!keyBtn) return;

    keyBtn.classList.add('dwell-active');

    const timerObj = {
        _timeout: null,
        stop() {
            clearTimeout(this._timeout);
            keyBtn.classList.remove('dwell-active');
        }
    };

    timerObj._timeout = setTimeout(() => {
        keyBtn.classList.remove('dwell-active');
        dwellTimers.delete(elementId);
        handleKeyPress(keyName, keyBtn);
    }, dwellTime * 1000);

    dwellTimers.set(elementId, timerObj);
}

// Cleanup — do NOT stop camera on page unload
window.addEventListener('beforeunload', () => {
    clearInterval(gazeUpdateInterval);
    dwellTimers.forEach(timer => timer.stop());
});
