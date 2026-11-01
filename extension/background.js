importScripts("config.js");

const API = globalThis.BeyondTouchApi || "http://127.0.0.1:8001";
const WS_URL_PRIMARY = globalThis.BeyondTouchWs || "ws://127.0.0.1:8001/ws/cv";
const WS_URL_FALLBACK = globalThis.BeyondTouchWsFallback || "ws://127.0.0.1:8000/ws/cv";

const contexts = new Map();
const timers = new Map();
let socket = null;
let reconnectTimer = null;
let usingFallbackWs = false;

const ALLOWED_ACTIONS = new Set([
  "HEAD_UP",
  "HEAD_DOWN",
  "HEAD_LEFT",
  "HEAD_RIGHT",
  "HEAD_TILT_LEFT",
  "HEAD_TILT_RIGHT",
  "CURSOR_MOVE",
  "PINCH_START",
  "PINCH_END",
  "TRACKING_LOST"
]);

// ==================================================
// 1. CONTEXT SYNCHRONIZATION
// ==================================================

async function postContext(tabId, context) {
  try {
    const payload = { ...context, tab_id: tabId };
    const response = await fetch(`${API}/context/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Context update failed: ${response.status} ${err}`);
    }

    const data = await response.json();
    contexts.set(tabId, data.context);
    await chrome.storage.local.set({ activeContext: data.context });

    // If active tab, activate in backend context store
    const [current] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabId === current?.id) {
      await fetch(`${API}/context/activate/${tabId}`, { method: "POST" }).catch(() => {});
    }

    return data.context;
  } catch (error) {
    console.warn("[ContextSwitch] Context sync error:", error.message);
    throw error;
  }
}

// ==================================================
// 2. ACTION POLLING & RESULT DISPATCH
// ==================================================

async function sendResult(action, result) {
  try {
    await fetch(`${API}/actions/result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_id: action.action_id,
        tab_id: action.tab_id,
        status: result?.status || "FAILED",
        verified: result?.verified === true,
        result: result?.result || {},
        error: result?.error || null
      })
    });
  } catch (e) {
    console.warn("[ContextSwitch] Result upload error:", e.message);
  }
}

async function poll(tabId) {
  try {
    const r = await fetch(`${API}/actions/next?tab_id=${tabId}`);
    if (!r.ok) return;
    const data = await r.json();
    if (!data.action) return;

    console.log("[ContextSwitch] Claimed action for tab", tabId, data.action);
    let result;
    try {
      result = await chrome.tabs.sendMessage(tabId, {
        type: "EXECUTE_ACTION",
        action: data.action
      });
    } catch (e) {
      result = { status: "FAILED", verified: false, error: `Content script unavailable: ${e.message}` };
    }
    await sendResult(data.action, result);
  } catch (_) {
    // Backend may be offline; retry on next poll interval
  }
}

function startPolling(tabId) {
  if (timers.has(tabId)) return;
  poll(tabId);
  timers.set(tabId, setInterval(() => poll(tabId), 1000));
}

function stopPolling(tabId) {
  if (timers.has(tabId)) clearInterval(timers.get(tabId));
  timers.delete(tabId);
}

// ==================================================
// 3. COMPUTER VISION WEBSOCKET CLIENT
// ==================================================

function broadcastStatus(connected) {
  chrome.tabs.query({}, (tabs) => {
    for (const tab of tabs) {
      if (!tab.id) continue;
      chrome.tabs.sendMessage(tab.id, {
        type: "CONTEXTSWITCH_STATUS",
        connected
      }).catch(() => {});
    }
  });
}

function forwardCvEvent(event) {
  if (!ALLOWED_ACTIONS.has(event.action)) return;

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab?.id) return;
    chrome.tabs.sendMessage(tab.id, {
      type: "CONTEXTSWITCH_CV",
      event
    }).catch(() => {});
  });
}

function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const targetUrl = usingFallbackWs ? WS_URL_FALLBACK : WS_URL_PRIMARY;
  console.log(`[ContextSwitch] Connecting to CV WebSocket: ${targetUrl}...`);

  try {
    socket = new WebSocket(targetUrl);
  } catch (err) {
    scheduleReconnect();
    return;
  }

  socket.onopen = () => {
    console.log(`[ContextSwitch] CV WebSocket connected to ${targetUrl}`);
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    broadcastStatus(true);
  };

  socket.onmessage = (message) => {
    try {
      const event = JSON.parse(message.data);
      forwardCvEvent(event);
    } catch (e) {}
  };

  socket.onclose = () => {
    console.log("[ContextSwitch] CV WebSocket closed.");
    socket = null;
    broadcastStatus(false);
    usingFallbackWs = !usingFallbackWs; // Alternate between primary (8001) and standalone (8000)
    scheduleReconnect();
  };

  socket.onerror = () => {
    console.warn("[ContextSwitch] CV WebSocket error; will retry.");
  };
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWebSocket();
  }, 2000);
}

// ==================================================
// 4. MESSAGE ROUTING & EXTENSION EVENTS
// ==================================================

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "SYNC_ACTIVE_CONTEXT") {
    (async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id || !/^https?:/.test(tab.url || "")) {
        throw new Error("Open a KiCanvas schematic tab first.");
      }
      let response;
      try {
        response = await chrome.tabs.sendMessage(tab.id, { type: "REQUEST_CONTEXT" });
      } catch (_) {
        throw new Error("Refresh the KiCanvas tab after reloading the extension, then reopen the popup.");
      }
      if (!response?.context) {
        throw new Error("Refresh the KiCanvas tab to load the updated content script.");
      }
      const context = await postContext(tab.id, response.context);
      startPolling(tab.id);
      return { context };
    })().then(sendResponse).catch(error => sendResponse({ error: error.message }));
    return true;
  }

  if (msg?.type === "CONTEXT_UPDATE" && sender.tab?.id != null) {
    postContext(sender.tab.id, msg.context)
      .then(context => sendResponse({ context }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }

  if (msg?.type === "START_ACTION_POLLING" && sender.tab?.id != null) {
    startPolling(sender.tab.id);
  }

  if (msg?.type === "CONTEXTSWITCH_GET_STATUS") {
    sendResponse({
      connected: socket?.readyState === WebSocket.OPEN,
      api: API
    });
    return true;
  }

  if (msg?.type === "SUBMIT_VOICE_COMMAND") {
    (async () => {
      const res = await fetch(`${API}/voice/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: msg.text,
          tab_id: sender.tab?.id,
          auto_dispatch: true
        })
      });
      return await res.json();
    })().then(sendResponse).catch(err => sendResponse({ error: err.message }));
    return true;
  }

  if (msg?.type === "CALIBRATE_CV") {
    fetch(`${API}/cv/calibrate`, { method: "POST" })
      .then(r => r.json())
      .then(sendResponse)
      .catch(e => sendResponse({ error: e.message }));
    return true;
  }
});

async function refresh(tabId) {
  try {
    const tab = await chrome.tabs.get(tabId);
    if (!/^https?:/.test(tab.url || "")) return;
    startPolling(tabId);
    await chrome.tabs.sendMessage(tabId, { type: "REQUEST_CONTEXT" }).catch(() => {});
  } catch (_) {}
}

chrome.tabs.onActivated.addListener(({ tabId }) => refresh(tabId));
chrome.tabs.onUpdated.addListener((id, info, tab) => {
  if (info.status === "complete" && tab.active) refresh(id);
});
chrome.tabs.onRemoved.addListener(async (id) => {
  stopPolling(id);
  contexts.delete(id);
  try {
    await fetch(`${API}/context/remove/${id}`, { method: "DELETE" });
  } catch (_) {}
});

chrome.alarms.create("cv-reconnect", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "cv-reconnect") connectWebSocket();
});

chrome.runtime.onInstalled.addListener(async () => {
  const tabs = await chrome.tabs.query({});
  tabs.forEach(t => {
    if (t.id != null && /^https?:/.test(t.url || "")) startPolling(t.id);
  });
  connectWebSocket();
});

connectWebSocket();
