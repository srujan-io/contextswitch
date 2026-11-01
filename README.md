# ContextSwitch — Multimodal Touchless KiCanvas Controller
### Unified Electronics Lab System (Context Detection + Voice Commands + Computer Vision)

ContextSwitch transforms KiCanvas into a hands-free, touchless workstation tailored for hardware engineers and electronics lab environments where hands may be occupied holding probes, soldering irons, or test tools.

---

## What is Integrated in this Demo Branch (`demo-integrated`)

1. **Context Detection & Browser Action Dispatch** (from `context-detection`):
   - Observes active tabs and automatically recognizes KiCanvas schematics.
   - Action validation engine with safety boundaries and state tracking.
   - Shadow DOM traversal adapter (`kicanvas.js`) that searches component references in `<kc-schematic-app>`, filters symbols, selects matching elements, and triggers `zoom_to_selection`.

2. **KiCad Voice Commands & Semantic Resolver** (from `kicad_voicecommands`):
   - Ground truth entity resolver (`data/kicad_ground_truth.json`) matching KiCad components (`R1`, `C4`, `U1`, `C101`, `R101`, `J106`), signals (`VCC`, `GND`, `USB_DATA`), sheets, and sections.
   - Calibrated FastEmbed local embedding matcher (`BAAI/bge-small-en-v1.5`) with zero false accepts.
   - Gemini intent interpreter escalation for ambiguous and complex queries.
   - Automatic mapping of voice commands into executable KiCanvas DOM actions (`LOCATE_COMPONENT` -> `search_component`, `ZOOM_IN`/`OUT`, `PAN`).

3. **Computer Vision Head & Hand Tracking** (from `cv`):
   - MediaPipe Face Landmarker (`face_landmarker.task`) for head pose tracking (Pitch, Yaw, Roll).
   - Head gestures:
     - `HEAD_UP` / `HEAD_DOWN` -> Pan Up / Down
     - `HEAD_LEFT` / `HEAD_RIGHT` -> Pan Left / Right
     - `HEAD_TILT_RIGHT` / `HEAD_TILT_LEFT` -> Smooth Zoom In / Out
   - MediaPipe Hand Landmarker (`hand_landmarker.task`) for index finger tracking (`CURSOR_MOVE`) and thumb-index pinch detection (`PINCH_START` / `PINCH_END` -> Click).
   - High-performance WebSocket stream at `ws://127.0.0.1:8001/ws/cv`.

4. **Electronics Lab Workstation UI (Light Mode)**:
   - Crisp, cleanroom-grade Light Mode dashboard served at `http://127.0.0.1:8001/demo`.
   - Real-time head orientation gauges (Pitch, Yaw, Roll) with interactive neutral calibration.
   - Interactive virtual cursor preview pad and pinch state indicator.
   - Browser-side Push-to-Talk voice recognition (Web Speech API) + quick action preset buttons.
   - Real-time action queue and verification monitor showing exact KiCanvas DOM results.

5. **Upgraded KiCanvas Browser Extension**:
   - In-page floating **Lab HUD Overlay** right on `https://kicanvas.org` showing live gesture & voice feedback toasts (`[👆 PINCH]`, `[🔍 TILT ZOOM]`, `[🎙️ LOCATE R1]`).
   - Virtual on-screen cursor following hand movement with pinch-to-click.
   - Seamless WebSocket connection to CV service and REST connection to the action queue.

---

## Getting Started

### 1. Requirements & Dependencies
Ensure Python 3.10+ and Node.js are available. Install dependencies:

```powershell
pip install fastapi uvicorn websockets opencv-python mediapipe fastembed SpeechRecognition google-genai python-dotenv
```

### 2. Start the Unified Workstation
From the repository root, run:

```powershell
python run_lab.py
```

This launches the unified server on port **8001**:
- **Electronics Lab Dashboard**: [http://127.0.0.1:8001/demo](http://127.0.0.1:8001/demo)
- **REST Context API**: [http://127.0.0.1:8001](http://127.0.0.1:8001)
- **CV WebSocket**: `ws://127.0.0.1:8001/ws/cv`

*(Optional)* If you prefer running the CV server in standalone debug mode on port 8000 with OpenCV camera preview window:
```powershell
python cv_server.py
```

### 3. Load the Browser Extension
1. Open Google Chrome or Microsoft Edge.
2. Navigate to `chrome://extensions` (or `edge://extensions`).
3. Toggle on **Developer mode** in the top right.
4. Click **Load unpacked**.
5. Select the `extension` folder inside this repository:
   `contextswitch/extension`

### 4. Open KiCanvas
1. Navigate to [https://kicanvas.org](https://kicanvas.org) (or open any schematic, such as `https://kicanvas.org/?github=https://github.com/geeksville/esp32-breadboard-v1`).
2. Refresh the tab once so the newly loaded extension content scripts attach.
3. You will see the floating **Lab Mode** widget in the bottom-right corner of KiCanvas!

---

## Interacting with KiCanvas

### A. Voice Commands
- Click the **🎙️ Push-to-Talk** button in the extension popup, or on the in-page HUD, or on the Lab Dashboard ([http://127.0.0.1:8001/demo](http://127.0.0.1:8001/demo)).
- Speak any command:
  - `"Locate R1"` or `"Find capacitor C4"` -> Focuses Symbols panel, searches, selects component, and zooms to selection!
  - `"Zoom in"` / `"Zoom out"` -> Adjusts canvas zoom.
  - `"Pan left"` / `"Pan right"` / `"Pan up"` / `"Pan down"` -> Panning across the schematic.
  - `"Trace signal VCC"` -> Traces and highlights net connections.
  - `"Explain R101"` -> Explains component function from schematic facts.

### B. Computer Vision Gestures (Touchless)
- **Head Gestures**:
  - Look Up / Down -> Pans schematic up / down.
  - Look Left / Right -> Pans schematic left / right.
  - Tilt Head Right -> Zooms In.
  - Tilt Head Left -> Zooms Out.
  - Press **C** or click **Calibrate Neutral** to recalibrate neutral pose at any time.
- **Hand Gestures**:
  - Raise index finger -> Virtual blue cursor appears on KiCanvas and tracks finger movement.
  - Pinch thumb + index finger -> Sends `pointerdown`/`mousedown`, and releasing clicks on whatever element is under the cursor!

---

## Automated Verification Tests
Run the test suites to verify that both the voice router and KiCanvas DOM shadow root traverser are functioning correctly:

```powershell
# 1. Test KiCad Voice Intent Router & Ground Truth Resolver (36 tests)
python -m pytest member3/test_actions.py

# 2. Test KiCanvas Shadow DOM Component Search & Zoom (4 tests)
node extension/tests/kicanvas.test.cjs
```
