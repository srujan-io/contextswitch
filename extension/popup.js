const API = globalThis.BeyondTouchApi || "http://127.0.0.1:8001";
let recognition = null;
let isRecording = false;

async function syncContext() {
  const tabStatus = document.getElementById("tab-status");
  const tabDot = document.getElementById("dot-tab");
  try {
    const res = await chrome.runtime.sendMessage({ type: "SYNC_ACTIVE_CONTEXT" });
    if (res?.error) throw new Error(res.error);
    const ctx = res.context;
    tabDot.className = "dot green";
    tabStatus.textContent = ctx.title ? ctx.title.slice(0, 18) + "..." : "KiCanvas Tab Active";
    return ctx;
  } catch (e) {
    tabDot.className = "dot amber";
    tabStatus.textContent = "Open & Refresh KiCanvas";
    return null;
  }
}

async function checkCVStatus() {
  const cvStatus = document.getElementById("cv-status");
  const cvDot = document.getElementById("dot-cv");
  try {
    const res = await chrome.runtime.sendMessage({ type: "CONTEXTSWITCH_GET_STATUS" });
    if (res?.connected) {
      cvDot.className = "dot green";
      cvStatus.textContent = "CV Connected";
    } else {
      cvDot.className = "dot amber";
      cvStatus.textContent = "CV Standby";
    }
  } catch (_) {
    cvDot.className = "dot amber";
    cvStatus.textContent = "CV Offline";
  }
}

// Voice Command Execution
window.sendVoice = async function(text) {
  const transcriptEl = document.getElementById("transcript");
  transcriptEl.textContent = `Dispatching: "${text}"...`;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const res = await fetch(`${API}/voice/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        tab_id: tab?.id,
        auto_dispatch: true
      })
    });
    const data = await res.json();
    if (data.dispatched) {
      transcriptEl.textContent = `✓ Dispatched "${data.action_name}" to KiCanvas!`;
    } else {
      transcriptEl.textContent = `Result: ${data.action_name || data.status}`;
    }
  } catch (err) {
    transcriptEl.textContent = `Error: ${err.message}`;
  }
};

// Web Speech API
const pttBtn = document.getElementById("ptt-btn");
const pttText = document.getElementById("ptt-text");
const transcriptEl = document.getElementById("transcript");

function initSpeech() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    pttText.textContent = "Speech API not available";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.onstart = () => {
    isRecording = true;
    pttBtn.classList.add("listening");
    pttText.textContent = "Listening... Speak now";
  };
  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    transcriptEl.textContent = `Heard: "${text}"`;
    window.sendVoice(text);
  };
  recognition.onend = () => {
    isRecording = false;
    pttBtn.classList.remove("listening");
    pttText.textContent = "Click to Speak";
  };
  recognition.onerror = () => {
    isRecording = false;
    pttBtn.classList.remove("listening");
    pttText.textContent = "Click to Speak";
  };
}

pttBtn.addEventListener("click", () => {
  if (!recognition) initSpeech();
  if (!recognition) return;
  if (isRecording) {
    recognition.stop();
  } else {
    try { recognition.start(); } catch (_) {}
  }
});

// Manual Component Search Form
document.getElementById("search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("ref-input");
  const query = input.value.trim().toUpperCase();
  if (query) {
    window.sendVoice(`locate ${query}`);
    input.value = "";
  }
});

// Open Full Lab Dashboard
document.getElementById("open-dashboard-link").addEventListener("click", () => {
  chrome.tabs.create({ url: `${API}/demo` });
});

// Initialize on popup open
syncContext();
checkCVStatus();
