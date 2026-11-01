"""
Light Mode Electronics Lab UI for ContextSwitch
A crisp, clean, elegant light-theme dashboard designed for hardware and electronics lab workstations.
"""

def get_demo_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ContextSwitch — Electronics Lab Controller</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --border-focus: #0284c7;
      --text: #0f172a;
      --text-muted: #64748b;
      --primary: #0284c7;
      --primary-hover: #0369a1;
      --primary-light: #e0f2fe;
      --teal: #0d9488;
      --teal-light: #ccfbf1;
      --success: #16a34a;
      --success-light: #dcfce7;
      --warning: #d97706;
      --warning-light: #fef3c7;
      --danger: #dc2626;
      --danger-light: #fee2e2;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
      --radius: 12px;
      --radius-sm: 8px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
    }

    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-icon {
      width: 44px;
      height: 44px;
      background: linear-gradient(135deg, #0284c7, #0d9488);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 22px;
      font-weight: 700;
      box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25);
    }

    .brand-text h1 {
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text);
    }

    .brand-text p {
      font-size: 13px;
      color: var(--text-muted);
    }

    .status-chips {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      background: var(--card-bg);
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--text-muted);
    }
    .dot.online { background: var(--success); box-shadow: 0 0 6px rgba(22, 163, 74, 0.6); }
    .dot.offline { background: var(--danger); }
    .dot.standby { background: var(--warning); }

    /* Grid Layout */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 24px;
    }

    @media (max-width: 960px) {
      .dashboard-grid { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .card-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #fafbfc;
    }

    .card-header h2 {
      font-size: 15px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text);
    }

    .card-body {
      padding: 20px;
      flex: 1;
    }

    /* Schematic Context Bar */
    .context-banner {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      border-radius: var(--radius-sm);
      padding: 14px 18px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .context-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .context-tag {
      background: var(--primary);
      color: white;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .context-details {
      font-size: 13px;
    }
    .context-details strong { color: var(--text); }
    .context-details span { color: var(--text-muted); }

    /* Voice Station */
    .voice-ptt-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px 0 24px 0;
    }

    .ptt-button {
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background: linear-gradient(135deg, #0284c7, #0284c7);
      border: 4px solid var(--primary-light);
      color: white;
      font-size: 32px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
      transition: all 0.2s ease;
      position: relative;
    }

    .ptt-button:hover {
      transform: scale(1.05);
      background: var(--primary-hover);
    }

    .ptt-button.listening {
      background: #dc2626;
      border-color: #fee2e2;
      animation: pulse 1.5s infinite;
      box-shadow: 0 0 24px rgba(220, 38, 38, 0.5);
    }

    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.08); }
      100% { transform: scale(1); }
    }

    .ptt-label {
      margin-top: 12px;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
    }

    .transcript-box {
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      min-height: 56px;
      display: flex;
      align-items: center;
      font-size: 14px;
      margin-bottom: 16px;
      color: var(--text);
    }

    .transcript-box.empty {
      color: #94a3b8;
      font-style: italic;
    }

    .input-row {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }

    input[type="text"] {
      flex: 1;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: border 0.2s;
    }

    input[type="text"]:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);
    }

    .btn {
      padding: 9px 16px;
      font-size: 13px;
      font-weight: 600;
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
      white-space: nowrap;
    }

    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-outline { background: white; border-color: var(--border); color: var(--text); }
    .btn-outline:hover { background: #f1f5f9; }
    .btn-teal { background: var(--teal); color: white; }
    .btn-teal:hover { background: #0f766e; }

    .quick-tags-title {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }

    .quick-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .pill-btn {
      padding: 5px 10px;
      border-radius: 6px;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      font-size: 12px;
      font-weight: 500;
      color: var(--text);
      cursor: pointer;
      transition: all 0.15s;
    }

    .pill-btn:hover {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
    }

    /* CV & Gestures Section */
    .gauges-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 20px;
    }

    .gauge-box {
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px;
      text-align: center;
    }

    .gauge-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
    }

    .gauge-value {
      font-family: 'JetBrains Mono', monospace;
      font-size: 20px;
      font-weight: 700;
      color: var(--text);
      margin: 4px 0;
    }

    .gauge-bar-bg {
      height: 4px;
      background: #e2e8f0;
      border-radius: 2px;
      overflow: hidden;
    }

    .gauge-bar {
      height: 100%;
      background: var(--primary);
      width: 50%;
      transition: width 0.1s ease;
    }

    .cv-state-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      margin-bottom: 12px;
      font-size: 13px;
    }

    .gesture-indicator {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 12px;
      background: #e2e8f0;
      color: #334155;
    }

    .gesture-indicator.active {
      background: var(--teal-light);
      color: var(--teal);
      border: 1px solid var(--teal);
    }

    /* Hand Pad Preview */
    .hand-pad {
      height: 130px;
      background: #f1f5f9;
      border: 2px dashed #cbd5e1;
      border-radius: var(--radius-sm);
      position: relative;
      margin-bottom: 16px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .cursor-preview {
      width: 24px;
      height: 24px;
      border: 2px solid var(--primary);
      background: rgba(2, 132, 199, 0.2);
      border-radius: 50%;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      pointer-events: none;
      transition: background 0.1s;
    }

    .cursor-preview.pinching {
      background: var(--danger);
      border-color: var(--danger);
      transform: translate(-50%, -50%) scale(0.8);
    }

    .hand-pad-hint {
      font-size: 11px;
      color: #94a3b8;
      pointer-events: none;
      font-weight: 500;
    }

    /* Logs Table */
    .table-container {
      width: 100%;
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }

    th {
      background: #f8fafc;
      padding: 10px 14px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      color: var(--text);
    }

    tr:last-child td { border-bottom: none; }

    .tag-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
    }

    .tag-badge.queued { background: #fef3c7; color: #b45309; }
    .tag-badge.success { background: #dcfce7; color: #15803d; }
    .tag-badge.failed { background: #fee2e2; color: #b91c1c; }

    footer {
      text-align: center;
      padding-top: 24px;
      font-size: 12px;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="brand">
      <div class="brand-icon">⚡</div>
      <div class="brand-text">
        <h1>ContextSwitch</h1>
        <p>Multimodal Electronics Lab Workstation Controller</p>
      </div>
    </div>
    <div class="status-chips">
      <div class="chip">
        <div id="dot-backend" class="dot online"></div>
        <span>Backend API: 8001</span>
      </div>
      <div class="chip">
        <div id="dot-cv" class="dot online"></div>
        <span>CV WebSocket: Connected</span>
      </div>
      <div class="chip">
        <div id="dot-tab" class="dot standby"></div>
        <span id="tab-status-text">KiCanvas Tab: Checking...</span>
      </div>
    </div>
  </header>

  <!-- Active Context Banner -->
  <div class="context-banner">
    <div class="context-info">
      <span class="context-tag" id="site-tag">KiCanvas</span>
      <div class="context-details">
        <strong id="active-tab-title">Loading active schematic context...</strong>
        <span id="active-tab-url"></span>
      </div>
    </div>
    <button class="btn btn-outline" onclick="syncActiveContext()">🔄 Sync Active Tab</button>
  </div>

  <!-- Dashboard Grid -->
  <div class="dashboard-grid">

    <!-- Card 1: Voice Commands Station -->
    <div class="card">
      <div class="card-header">
        <h2>🎙️ Voice Commands & Intent Routing</h2>
        <span class="chip" id="voice-status-chip">Member 3 Ready</span>
      </div>
      <div class="card-body">

        <!-- Push to talk button -->
        <div class="voice-ptt-container">
          <button id="ptt-btn" class="ptt-button" onclick="toggleVoiceRecording()">
            🎙️
          </button>
          <div id="ptt-status" class="ptt-label">Click to Speak (Push-to-Talk)</div>
        </div>

        <!-- Live transcript box -->
        <div id="transcript-display" class="transcript-box empty">
          Voice transcript will appear here in real time...
        </div>

        <!-- Text command fallback input -->
        <div class="input-row">
          <input type="text" id="manual-voice-input" placeholder="Or type a voice command e.g. 'locate R1', 'zoom in'..." onkeydown="if(event.key==='Enter') submitManualCommand()">
          <button class="btn btn-primary" onclick="submitManualCommand()">Execute</button>
        </div>

        <!-- Lab preset quick pills -->
        <div class="quick-tags-title">Quick Lab Presets (Click to Dispatch)</div>
        <div class="quick-tags">
          <button class="pill-btn" onclick="executeQuickVoice('locate R1')">🔍 Locate R1</button>
          <button class="pill-btn" onclick="executeQuickVoice('find C4')">🔍 Find C4</button>
          <button class="pill-btn" onclick="executeQuickVoice('locate U1')">🔍 Locate U1</button>
          <button class="pill-btn" onclick="executeQuickVoice('zoom in')">🔎 Zoom In</button>
          <button class="pill-btn" onclick="executeQuickVoice('zoom out')">🔍 Zoom Out</button>
          <button class="pill-btn" onclick="executeQuickVoice('pan left')">⬅️ Pan Left</button>
          <button class="pill-btn" onclick="executeQuickVoice('pan right')">➡️ Pan Right</button>
          <button class="pill-btn" onclick="executeQuickVoice('pan up')">⬆️ Pan Up</button>
          <button class="pill-btn" onclick="executeQuickVoice('trace signal VCC')">⚡ Trace VCC</button>
          <button class="pill-btn" onclick="executeQuickVoice('explain R101')">ℹ️ Explain R101</button>
        </div>

      </div>
    </div>

    <!-- Card 2: CV, Head & Hand Gestures -->
    <div class="card">
      <div class="card-header">
        <h2>👁️ Head & Hand Gesture Tracking</h2>
        <span class="chip" id="cv-status-chip">MediaPipe Active</span>
      </div>
      <div class="card-body">

        <!-- Head orientation gauges -->
        <div class="gauges-grid">
          <div class="gauge-box">
            <div class="gauge-label">Pitch (Up/Down)</div>
            <div id="pitch-val" class="gauge-value">0.0°</div>
            <div class="gauge-bar-bg"><div id="pitch-bar" class="gauge-bar"></div></div>
          </div>
          <div class="gauge-box">
            <div class="gauge-label">Yaw (Left/Right)</div>
            <div id="yaw-val" class="gauge-value">0.0°</div>
            <div class="gauge-bar-bg"><div id="yaw-bar" class="gauge-bar"></div></div>
          </div>
          <div class="gauge-box">
            <div class="gauge-label">Roll (Tilt Zoom)</div>
            <div id="roll-val" class="gauge-value">0.0°</div>
            <div class="gauge-bar-bg"><div id="roll-bar" class="gauge-bar"></div></div>
          </div>
        </div>

        <!-- Head status row -->
        <div class="cv-state-row">
          <div>
            <strong>Head Gesture: </strong>
            <span id="last-head-action" class="gesture-indicator">NONE</span>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 12px;" onclick="calibrateNeutral()">🎯 Calibrate Neutral (C)</button>
            <button class="btn btn-outline" style="padding: 4px 10px; font-size: 12px;" onclick="resetNeutral()">🔄 Reset</button>
          </div>
        </div>

        <!-- Hand & Cursor state row -->
        <div class="cv-state-row">
          <div>
            <strong>Hand Tracking: </strong>
            <span id="hand-state-text" class="gesture-indicator">TRACKING</span>
          </div>
          <div>
            <strong>Pinch: </strong>
            <span id="pinch-state-text" class="gesture-indicator">IDLE</span>
          </div>
        </div>

        <!-- Virtual Cursor Interactive Pad -->
        <div class="hand-pad" id="hand-preview-pad">
          <div id="cursor-indicator" class="cursor-preview"></div>
          <span class="hand-pad-hint">Virtual Hand Cursor Surface (Move finger or pinch to test)</span>
        </div>

        <!-- Simulation quick actions -->
        <div class="quick-tags-title">Gesture Simulation (For Lab Demos)</div>
        <div class="quick-tags">
          <button class="pill-btn" onclick="simulateHead('HEAD_UP')">⬆️ Head Up (Pan)</button>
          <button class="pill-btn" onclick="simulateHead('HEAD_DOWN')">⬇️ Head Down (Pan)</button>
          <button class="pill-btn" onclick="simulateHead('HEAD_LEFT')">⬅️ Head Left</button>
          <button class="pill-btn" onclick="simulateHead('HEAD_RIGHT')">➡️ Head Right</button>
          <button class="pill-btn" onclick="simulateHead('HEAD_TILT_RIGHT')">🔍 Tilt Zoom In</button>
          <button class="pill-btn" onclick="simulateHead('HEAD_TILT_LEFT')">🔎 Tilt Zoom Out</button>
          <button class="pill-btn" onclick="simulatePinch()">👆 Simulate Pinch Click</button>
        </div>

      </div>
    </div>

  </div>

  <!-- Real-Time KiCanvas Action Dispatch & Verification Log -->
  <div class="card">
    <div class="card-header">
      <h2>📋 Real-Time KiCanvas Action Queue & Verification Log</h2>
      <button class="btn btn-outline" style="font-size: 12px; padding: 4px 10px;" onclick="fetchActionJobs()">Refresh Queue</button>
    </div>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Source</th>
            <th>Action</th>
            <th>Target / Parameters</th>
            <th>Status</th>
            <th>KiCanvas DOM Verification</th>
          </tr>
        </thead>
        <tbody id="actions-table-body">
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">
              No actions executed yet. Use Voice, Head gestures, or the quick presets above!
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <footer>
    ContextSwitch • Integrated Multimodal KiCanvas Controller • Context Detection + Member 3 Voice + Computer Vision
  </footer>

  <script>
    const API_BASE = window.location.origin;
    let ws = null;
    let recognition = null;
    let isListening = false;
    let actionLog = [];

    // Initialize Web Speech API for browser-side instant push-to-talk
    function initSpeech() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        document.getElementById('ptt-status').textContent = "Web Speech API not supported in this browser. Use text input.";
        return;
      }
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        isListening = true;
        document.getElementById('ptt-btn').classList.add('listening');
        document.getElementById('ptt-status').textContent = "Listening... Speak your command now";
        document.getElementById('transcript-display').classList.remove('empty');
      };

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        const text = final || interim;
        if (text) {
          document.getElementById('transcript-display').textContent = text;
        }
        if (final) {
          submitVoiceCommand(final.trim());
        }
      };

      recognition.onerror = (event) => {
        console.warn("Speech error:", event.error);
        stopVoiceRecording();
      };

      recognition.onend = () => {
        stopVoiceRecording();
      };
    }

    function toggleVoiceRecording() {
      if (isListening) {
        stopVoiceRecording();
      } else {
        startVoiceRecording();
      }
    }

    function startVoiceRecording() {
      if (!recognition) initSpeech();
      if (recognition) {
        try { recognition.start(); } catch (e) {}
      }
    }

    function stopVoiceRecording() {
      isListening = false;
      document.getElementById('ptt-btn').classList.remove('listening');
      document.getElementById('ptt-status').textContent = "Click to Speak (Push-to-Talk)";
      if (recognition) {
        try { recognition.stop(); } catch (e) {}
      }
    }

    // Submit Voice Command to Backend
    async function submitVoiceCommand(text) {
      if (!text) return;
      document.getElementById('transcript-display').textContent = "Processing: " + text + "...";

      try {
        const res = await fetch(`${API_BASE}/voice/command`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: text, auto_dispatch: true})
        });
        const data = await res.json();
        
        let msg = `"${text}" -> Recognized as ${data.action_name || 'UNRESOLVED'}`;
        if (data.dispatched) {
          msg += " • Dispatched to KiCanvas tab!";
        }
        document.getElementById('transcript-display').textContent = msg;
        
        addLogEntry({
          source: data.voice_decision?.details?.source || "VOICE",
          action: data.mapped_action?.action || data.action_name || "VOICE_COMMAND",
          params: JSON.stringify(data.mapped_action?.parameters || data.parameters || {}),
          status: data.dispatched ? "QUEUED" : "PROCESSED",
          verification: data.dispatched ? `Queued Job ${data.job?.job_id}. KiCanvas executing...` : "Recognized by intent pipeline"
        });

      } catch (err) {
        document.getElementById('transcript-display').textContent = "Error: " + err.message;
      }
    }

    function submitManualCommand() {
      const input = document.getElementById('manual-voice-input');
      const text = input.value.trim();
      if (!text) return;
      submitVoiceCommand(text);
      input.value = '';
    }

    function executeQuickVoice(cmd) {
      submitVoiceCommand(cmd);
    }

    // CV WebSocket Connection
    function connectCVWebSocket() {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${proto}//${window.location.host}/ws/cv`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        document.getElementById('dot-cv').className = "dot online";
        document.getElementById('cv-status-chip').textContent = "CV Connected";
      };

      ws.onmessage = (event) => {
        try {
          const ev = JSON.parse(event.data);
          handleCVEvent(ev);
        } catch (e) {}
      };

      ws.onclose = () => {
        document.getElementById('dot-cv').className = "dot offline";
        document.getElementById('cv-status-chip').textContent = "Reconnecting...";
        setTimeout(connectCVWebSocket, 2000);
      };
    }

    function handleCVEvent(ev) {
      if (ev.source === "HEAD") {
        const badge = document.getElementById('last-head-action');
        badge.textContent = ev.action;
        badge.classList.add('active');
        setTimeout(() => badge.classList.remove('active'), 800);

        addLogEntry({
          source: "HEAD_GESTURE",
          action: ev.action,
          params: JSON.stringify(ev.parameters || {}),
          status: "DISPATCHED",
          verification: `Canvas Wheel Navigation (${ev.action})`
        });
      }

      if (ev.source === "HAND") {
        if (ev.action === "CURSOR_MOVE" && ev.parameters) {
          const pad = document.getElementById('hand-preview-pad');
          const cursor = document.getElementById('cursor-indicator');
          const rect = pad.getBoundingClientRect();
          const x = (ev.parameters.x || 0.5) * rect.width;
          const y = (ev.parameters.y || 0.5) * rect.height;
          cursor.style.left = `${x}px`;
          cursor.style.top = `${y}px`;
          document.getElementById('hand-state-text').textContent = `X:${(ev.parameters.x||0).toFixed(2)} Y:${(ev.parameters.y||0).toFixed(2)}`;
        } else if (ev.action === "PINCH_START") {
          document.getElementById('cursor-indicator').classList.add('pinching');
          document.getElementById('pinch-state-text').textContent = "PINCHING";
          document.getElementById('pinch-state-text').classList.add('active');
        } else if (ev.action === "PINCH_END") {
          document.getElementById('cursor-indicator').classList.remove('pinching');
          document.getElementById('pinch-state-text').textContent = "CLICKED";
          setTimeout(() => {
            document.getElementById('pinch-state-text').textContent = "IDLE";
            document.getElementById('pinch-state-text').classList.remove('active');
          }, 600);
        }
      }
    }

    // Polling CV Status
    async function pollCVStatus() {
      try {
        const res = await fetch(`${API_BASE}/cv/status`);
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.latest_pose) {
          const p = data.latest_pose.pitch || 0;
          const y = data.latest_pose.yaw || 0;
          const r = data.latest_pose.roll || 0;
          document.getElementById('pitch-val').textContent = `${p.toFixed(1)}°`;
          document.getElementById('yaw-val').textContent = `${y.toFixed(1)}°`;
          document.getElementById('roll-val').textContent = `${r.toFixed(1)}°`;

          document.getElementById('pitch-bar').style.width = `${Math.min(100, Math.max(0, (p + 30) * 1.6))}%`;
          document.getElementById('yaw-bar').style.width = `${Math.min(100, Math.max(0, (y + 30) * 1.6))}%`;
          document.getElementById('roll-bar').style.width = `${Math.min(100, Math.max(0, (r + 30) * 1.6))}%`;
        }

        if (data.last_head_action && data.last_head_action !== "NONE") {
          document.getElementById('last-head-action').textContent = data.last_head_action;
        }
      } catch (e) {}
    }

    async function calibrateNeutral() {
      try {
        await fetch(`${API_BASE}/cv/calibrate`, {method: 'POST'});
        alert("Neutral head pose calibrated!");
      } catch (e) { alert(e.message); }
    }

    async function resetNeutral() {
      try {
        await fetch(`${API_BASE}/cv/reset`, {method: 'POST'});
      } catch (e) {}
    }

    async function simulateHead(action) {
      try {
        await fetch(`${API_BASE}/cv/inject-event`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({source: 'HEAD', action: action, parameters: {}})
        });
      } catch (e) {}
    }

    async function simulatePinch() {
      try {
        await fetch(`${API_BASE}/cv/inject-event`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({source: 'HAND', action: 'PINCH_START', parameters: {}})
        });
        setTimeout(async () => {
          await fetch(`${API_BASE}/cv/inject-event`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({source: 'HAND', action: 'PINCH_END', parameters: {}})
          });
        }, 150);
      } catch (e) {}
    }

    // Active Context Polling
    async function syncActiveContext() {
      try {
        const res = await fetch(`${API_BASE}/context/active`);
        if (!res.ok) {
          document.getElementById('dot-tab').className = "dot standby";
          document.getElementById('tab-status-text').textContent = "KiCanvas Tab: Not Detected";
          document.getElementById('active-tab-title').textContent = "Open KiCanvas (https://kicanvas.org) in a Chrome tab";
          document.getElementById('active-tab-url').textContent = "Ensure ContextSwitch extension is installed and loaded.";
          return;
        }
        const ctx = await res.json();
        document.getElementById('dot-tab').className = "dot online";
        document.getElementById('tab-status-text').textContent = `KiCanvas Active (Tab ${ctx.tab_id})`;
        document.getElementById('active-tab-title').textContent = ctx.title || "KiCanvas Schematic";
        document.getElementById('active-tab-url').textContent = ctx.url || "";
        document.getElementById('site-tag').textContent = (ctx.website_id || "KiCanvas").toUpperCase();
      } catch (e) {}
    }

    // Action Table Rendering
    function addLogEntry(entry) {
      const now = new Date().toLocaleTimeString();
      actionLog.unshift({ ...entry, time: now });
      if (actionLog.length > 20) actionLog.pop();
      renderLogTable();
    }

    function renderLogTable() {
      const tbody = document.getElementById('actions-table-body');
      if (!actionLog.length) return;
      tbody.innerHTML = actionLog.map(item => `
        <tr>
          <td><span style="font-family: monospace;">${item.time}</span></td>
          <td><span class="tag-badge" style="background: #e2e8f0;">${item.source}</span></td>
          <td><strong>${item.action}</strong></td>
          <td><span style="font-family: monospace; font-size: 11px;">${item.params}</span></td>
          <td><span class="tag-badge ${item.status === 'SUCCESS' ? 'success' : item.status === 'QUEUED' ? 'queued' : 'success'}">${item.status}</span></td>
          <td>${item.verification || 'Dispatched to KiCanvas DOM'}</td>
        </tr>
      `).join('');
    }

    // Periodically refresh data
    setInterval(pollCVStatus, 500);
    setInterval(syncActiveContext, 2000);

    // Initial startup
    initSpeech();
    connectCVWebSocket();
    syncActiveContext();
  </script>
</body>
</html>
"""
