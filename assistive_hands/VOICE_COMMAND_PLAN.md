# Voice Commands Implementation Plan

## What I Will Do

I will add voice command support to the existing Communication / On-Screen Keyboard page so the user can type, delete, clear, speak, and insert common phrases using their voice. The first implementation will use the browser's built-in Web Speech API, so we do not need to add Python audio dependencies or build a separate speech server immediately.

The feature will be added carefully into the existing communication flow:

- Voice input will write into the same text area used by the gaze keyboard.
- Voice commands will reuse existing functions such as `addText()`, `clearText()`, and the existing Speak button behavior.
- The microphone button will be usable by mouse, touch, and gaze dwell selection.
- If voice recognition is not supported by the browser, the interface will show a clear fallback message.

## Goal

Make manual typing easier by allowing the user to control the on-screen keyboard and communication text using spoken commands.

## Recommended First Version

Use the browser Web Speech API:

```js
window.SpeechRecognition || window.webkitSpeechRecognition
```

This is the simplest and fastest option because the app already uses browser speech features for text-to-speech in `communication.js`.

## Files To Update

### `assistive_hands/ui/templates/communication.html`

Add a voice control button near the existing `Speak` and `Clear` buttons.

Planned UI additions:

- `Voice` / microphone button
- Voice status area
- Accessibility status using `aria-live`
- Add the button as a gaze target so dwell selection can activate it

Example controls:

```html
<button class="btn btn-sm btn-outline-primary gaze-target gaze-target-dense" id="voiceBtn" aria-pressed="false">
    <i class="fas fa-microphone"></i> Voice
</button>

<div class="voice-status" id="voiceStatus" role="status" aria-live="polite">
    Voice idle
</div>
```

### `assistive_hands/ui/static/js/communication.js`

Add the main voice recognition logic.

Planned JavaScript additions:

- Detect browser speech recognition support
- Start and stop listening from the voice button
- Convert speech transcript into commands
- Add dictated text into `displayText`
- Show status updates such as `Listening`, `Voice stopped`, or `Voice not supported`
- Register the voice button as a dwell/gaze target

### `assistive_hands/ui/static/css/style.css`

Add small styles for the voice status state.

Possible states:

- Idle
- Listening
- Unsupported
- Error

## Voice Commands To Support

Initial command list:

| Spoken Command | Action |
| --- | --- |
| `type hello` | Adds `hello` to the message |
| `hello how are you` | Adds the spoken text directly |
| `space` | Adds a space |
| `new line` | Adds a line break |
| `enter` | Adds a line break |
| `backspace` | Deletes the last character |
| `delete` | Deletes the last character |
| `clear` | Clears all text |
| `speak` | Speaks the current message |
| `stop listening` | Turns voice recognition off |
| `yes` | Adds `Yes` |
| `no` | Adds `No` |
| `thank you` | Adds `Thank you` |
| `i need help` | Adds `I need help` |

## Voice Command Parser

Create a helper function in `communication.js`:

```js
function handleVoiceCommand(transcript) {
    const spoken = transcript.trim();
    const command = spoken.toLowerCase();

    if (!spoken) return;

    if (command === 'clear') {
        clearText();
    } else if (command === 'speak') {
        document.getElementById('speakBtn')?.click();
    } else if (command === 'backspace' || command === 'delete') {
        deleteLastCharacter();
    } else if (command === 'space') {
        addText(' ');
    } else if (command === 'enter' || command === 'new line') {
        addText('\n');
    } else if (command === 'stop listening') {
        stopVoiceRecognition();
    } else if (command.startsWith('type ')) {
        addText(spoken.slice(5));
    } else {
        addText(spoken);
    }
}
```

## New Helper Functions

Planned helpers:

```js
function setupVoiceControls() {}
function startVoiceRecognition() {}
function stopVoiceRecognition() {}
function toggleVoiceRecognition() {}
function handleVoiceCommand(transcript) {}
function updateVoiceStatus(message, state) {}
function deleteLastCharacter() {}
```

## Integration With Existing Code

The voice feature should not create a separate text system. It should use the current state:

```js
let displayText = '';
```

And existing functions:

```js
addText(text);
clearText();
updateTextDisplay();
```

This keeps gaze typing, button typing, quick phrases, and voice input consistent.

## Gaze / Dwell Integration

The new `voiceBtn` should be included in `refreshGazeTargets()`:

```js
...document.querySelectorAll('#speakBtn, #voiceBtn, #clearBtn, #pauseGazeInputBtn, #communicationBackBtn, .communication-toolbar a')
```

This allows the user to start or stop voice input by looking at the microphone button.

## Browser Support

The Web Speech API works best in Chrome and Edge. Firefox support may be limited.

If unsupported, the app should show:

```text
Voice commands are not supported in this browser. Try Chrome or Edge.
```

## Privacy Note

Browser speech recognition may use the browser vendor's online speech service. If offline recognition is required later, we can add a Python backend using an offline engine such as Vosk.

## Future Offline Option

If browser recognition is not enough, a later version can use:

- Vosk for offline speech recognition
- A Flask endpoint or WebSocket for microphone transcription
- Custom command mapping on the Python backend

This is more complex, so it should be version 2.

## Implementation Order

1. Add microphone button and status UI in `communication.html`.
2. Add voice status styles in `style.css`.
3. Add speech recognition setup in `communication.js`.
4. Add command parser.
5. Connect voice output to existing `displayText`.
6. Add `voiceBtn` to gaze dwell targets.
7. Test in Chrome or Edge.
8. Test unsupported-browser fallback.

## Testing Checklist

- Voice button appears near Speak and Clear.
- Clicking Voice starts listening.
- Clicking Voice again stops listening.
- Saying `hello` adds text.
- Saying `type I need water` adds `I need water`.
- Saying `backspace` deletes one character.
- Saying `clear` clears the message.
- Saying `speak` reads the current message aloud.
- Gaze dwell can activate the Voice button.
- Unsupported browsers show a helpful message.

## Final Expected Result

The Communication page will support three input methods:

- Gaze-controlled on-screen keyboard
- Quick phrase buttons
- Voice commands

This will reduce manual effort and make the app easier to use for fast communication.
