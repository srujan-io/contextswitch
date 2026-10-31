
const WS_URL = "ws://127.0.0.1:8000/ws/cv";

let socket = null;
let reconnectTimer = null;

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

function broadcastStatus(connected) {
  chrome.tabs.query(
    { url: ["https://kicanvas.org/*", "https://*.kicanvas.org/*"] },
    (tabs) => {
      for (const tab of tabs) {
        if (!tab.id) continue;

        chrome.tabs.sendMessage(
          tab.id,
          {
            type: "CONTEXTSWITCH_STATUS",
            connected
          }
        ).catch(() => {});
      }
    }
  );
}

function forwardEvent(event) {
  if (!ALLOWED_ACTIONS.has(event.action)) {
    return;
  }

  chrome.tabs.query(
    {
      active: true,
      currentWindow: true
    },
    (tabs) => {
      const tab = tabs[0];

      if (!tab?.id) return;

      if (
        !/^https:\/\/([a-z0-9-]+\.)*kicanvas\.org\//i
          .test(tab.url || "")
      ) {
        return;
      }

      chrome.tabs.sendMessage(
        tab.id,
        {
          type: "CONTEXTSWITCH_CV",
          event
        }
      ).catch(() => {});
    }
  );
}

function connectWebSocket() {
  if (
    socket &&
    (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    )
  ) {
    return;
  }

  console.log("[ContextSwitch] Connecting to CV server...");

  try {
    socket = new WebSocket(WS_URL);
  } catch (error) {
    console.error("[ContextSwitch] Connection error:", error);
    scheduleReconnect();
    return;
  }

  socket.onopen = () => {
    console.log("[ContextSwitch] CV server connected");

    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }

    broadcastStatus(true);
  };

  socket.onmessage = (message) => {
    try {
      const event = JSON.parse(message.data);
      forwardEvent(event);
    } catch (error) {
      console.error(
        "[ContextSwitch] Invalid CV event:",
        error
      );
    }
  };

  socket.onclose = () => {
    console.log("[ContextSwitch] CV disconnected");

    socket = null;
    broadcastStatus(false);
    scheduleReconnect();
  };

  socket.onerror = () => {
    console.warn("[ContextSwitch] WebSocket error");
  };
}

function scheduleReconnect() {
  if (reconnectTimer) return;

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWebSocket();
  }, 2000);
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("cv-reconnect", {
    periodInMinutes: 0.5
  });

  connectWebSocket();
});

chrome.runtime.onStartup.addListener(() => {
  connectWebSocket();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "cv-reconnect") {
    connectWebSocket();
  }
});

chrome.runtime.onMessage.addListener(
  (message, sender, sendResponse) => {
    if (message.type === "CONTEXTSWITCH_GET_STATUS") {
      sendResponse({
        connected: socket?.readyState === WebSocket.OPEN
      });
    }
  }
);

connectWebSocket();
