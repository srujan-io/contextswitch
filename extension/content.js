// ContextSwitch Unified Content Script
// KiCanvas Context Detection + CV Virtual Cursor + Head Gestures + Voice HUD Overlay
(() => {
  if (window.__contextSwitchLoaded) return;
  window.__contextSwitchLoaded = true;

  const CONFIG = {
    panStep: 160,
    zoomStep: 140,
    clickTolerance: 30
  };

  // ==================================================
  // 1. CONTEXT DETECTION (Module A)
  // ==================================================

  function clean(val, max = 200) {
    return String(val || "").replace(/\s+/g, " ").trim().slice(0, max);
  }

  function websiteId() {
    const h = location.hostname.toLowerCase();
    if (h === "kicanvas.org" || h.endsWith(".kicanvas.org")) return "kicanvas";
    if (h === "youtube.com" || h.endsWith(".youtube.com") || h === "youtu.be") return "youtube";
    return "unknown";
  }

  function pageType() {
    const h = location.hostname.toLowerCase(), p = location.pathname.toLowerCase();
    if (websiteId() === "kicanvas") {
      if (document.querySelector("kc-schematic-app, kicanvas-embed, canvas") || p.includes(".kicad_sch")) {
        return "schematic_viewer";
      }
      return "schematic_viewer";
    }
    return "unknown";
  }

  function selectedElement() {
    const sel = window.getSelection()?.toString().trim();
    const el = document.activeElement;
    const chosen = document.querySelector('[aria-selected="true"],[aria-pressed="true"],[data-selected="true"],.selected');
    if (sel) return { type: "text", text: clean(sel, 200) };
    if (chosen) return { type: "element", tag: chosen.tagName.toLowerCase(), label: clean(chosen.innerText || chosen.textContent, 100) };
    if (el && el !== document.body && el !== document.documentElement) {
      return { type: "focused_element", tag: el.tagName.toLowerCase(), label: clean(el.getAttribute("placeholder") || el.innerText, 100) };
    }
    return null;
  }

  function relevantElements() {
    const selectors = ["canvas", "kc-schematic-app", "button", "input", "[role='button']"];
    const out = [];
    for (const s of selectors) {
      for (const el of document.querySelectorAll(s)) {
        if (out.length >= 25) break;
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        const label = clean(el.getAttribute("aria-label") || el.innerText || el.tagName, 80);
        out.push({ tag: el.tagName.toLowerCase(), label });
      }
    }
    return out;
  }

  function collectContext(reason) {
    return {
      url: location.href,
      hostname: location.hostname.toLowerCase(),
      title: clean(document.title, 200),
      website_id: websiteId(),
      page_type: pageType(),
      selected_component: selectedElement(),
      available_elements: relevantElements(),
      event_reason: reason,
      captured_at: new Date().toISOString()
    };
  }

  let updateTimer;
  function sendUpdate(reason) {
    clearTimeout(updateTimer);
    updateTimer = setTimeout(() => {
      chrome.runtime.sendMessage({
        type: "CONTEXT_UPDATE",
        context: collectContext(reason)
      }).catch(() => {});
    }, 250);
  }

  // ==================================================
  // 2. KICANVAS ACTION EXECUTION (Module E)
  // ==================================================

  function schematicSurface() {
    for (const selector of ["canvas", "kc-schematic-app", "kicanvas-embed", "[role='application']"]) {
      const el = document.querySelector(selector);
      if (el && el.getBoundingClientRect().width > 0) return el;
    }
    return document.body;
  }

  async function executeAction(action) {
    const name = action.action;
    const p = action.parameters || {};

    if (name === "search_component" || name === "locate_component") {
      const query = p.query || p.component_ref;
      showToast(`Locating Component: ${query}...`);
      if (window.BeyondTouchKiCanvas && window.BeyondTouchKiCanvas.searchComponent) {
        const result = await window.BeyondTouchKiCanvas.searchComponent(query);
        sendUpdate("component_search");
        showToast(result.verified ? `✓ Focused on ${query}` : `Notice: ${result.error || 'Check schematic'}`);
        return result;
      }
      return { status: "FAILED", verified: false, error: "KiCanvas adapter not ready" };
    }

    if (name === "zoom_in" || name === "zoom_out") {
      const el = schematicSurface();
      const r = el.getBoundingClientRect();
      const deltaY = name === "zoom_in" ? -CONFIG.zoomStep : CONFIG.zoomStep;
      el.dispatchEvent(new WheelEvent("wheel", {
        bubbles: true, cancelable: true, view: window,
        clientX: r.left + r.width / 2, clientY: r.top + r.height / 2,
        deltaY: deltaY, ctrlKey: true
      }));
      showToast(name === "zoom_in" ? "🔎 Zoom In" : "🔍 Zoom Out");
      return { status: "SUCCESS", verified: true, result: { action: name } };
    }

    if (name === "pan") {
      const el = schematicSurface();
      const r = el.getBoundingClientRect();
      const dir = p.direction || "up";
      const d = { up: [0, -CONFIG.panStep], down: [0, CONFIG.panStep], left: [-CONFIG.panStep, 0], right: [CONFIG.panStep, 0] }[dir] || [0, -CONFIG.panStep];
      el.dispatchEvent(new WheelEvent("wheel", {
        bubbles: true, cancelable: true, view: window,
        clientX: r.left + r.width / 2, clientY: r.top + r.height / 2,
        deltaX: d[0], deltaY: d[1]
      }));
      showToast(`↔️ Pan ${dir.toUpperCase()}`);
      return { status: "SUCCESS", verified: true, result: { panned: dir } };
    }

    if (name === "view_component_details") {
      const ref = p.reference || p.component_ref;
      showToast(`ℹ️ Details for ${ref}`);
      return { status: "SUCCESS", verified: true, result: { reference: ref } };
    }

    if (name === "trace_signal") {
      const sig = p.signal_name;
      showToast(`⚡ Tracing Signal: ${sig}`);
      return { status: "SUCCESS", verified: true, result: { signal: sig } };
    }

    return { status: "FAILED", verified: false, error: `Unsupported action: ${name}` };
  }

  // ==================================================
  // 3. COMPUTER VISION: VIRTUAL CURSOR & PINCH
  // ==================================================

  let cursorX = window.innerWidth / 2;
  let cursorY = window.innerHeight / 2;
  let cursorVisible = false;
  let pinching = false;
  let pointerDownTarget = null;
  let pointerDownX = 0;
  let pointerDownY = 0;

  // Virtual Cursor Elements
  const cursor = document.createElement("div");
  cursor.id = "contextswitch-cursor";
  Object.assign(cursor.style, {
    position: "fixed",
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    border: "2.5px solid #0284c7",
    background: "rgba(2, 132, 199, 0.2)",
    pointerEvents: "none",
    zIndex: "2147483647",
    transform: "translate(-50%, -50%)",
    display: "none",
    transition: "background 0.1s, transform 0.1s"
  });

  const cursorDot = document.createElement("div");
  Object.assign(cursorDot.style, {
    position: "absolute",
    width: "6px",
    height: "6px",
    background: "#0284c7",
    borderRadius: "50%",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)"
  });
  cursor.appendChild(cursorDot);
  document.documentElement.appendChild(cursor);

  function getTarget() {
    return document.elementFromPoint(cursorX, cursorY);
  }

  function moveCursor(coords) {
    if (!coords || typeof coords.x !== "number" || typeof coords.y !== "number") return;
    cursorX = coords.x * window.innerWidth;
    cursorY = coords.y * window.innerHeight;

    cursor.style.left = `${cursorX}px`;
    cursor.style.top = `${cursorY}px`;

    if (!cursorVisible) {
      cursorVisible = true;
      cursor.style.display = "block";
    }

    const target = getTarget();
    if (target) {
      target.dispatchEvent(new MouseEvent("mousemove", {
        bubbles: true, cancelable: true, view: window,
        clientX: cursorX, clientY: cursorY
      }));
    }
  }

  function pinchStart() {
    if (pinching || !cursorVisible) return;
    pinching = true;
    cursor.style.background = "rgba(220, 38, 38, 0.4)";
    cursor.style.borderColor = "#dc2626";
    cursorDot.style.background = "#dc2626";

    pointerDownTarget = getTarget();
    pointerDownX = cursorX;
    pointerDownY = cursorY;

    if (pointerDownTarget) {
      pointerDownTarget.dispatchEvent(new PointerEvent("pointerdown", {
        bubbles: true, cancelable: true, view: window,
        clientX: cursorX, clientY: cursorY, button: 0, buttons: 1
      }));
      pointerDownTarget.dispatchEvent(new MouseEvent("mousedown", {
        bubbles: true, cancelable: true, view: window,
        clientX: cursorX, clientY: cursorY, button: 0, buttons: 1
      }));
    }
    showToast("👆 PINCH");
  }

  function pinchEnd() {
    if (!pinching) return;
    pinching = false;
    cursor.style.background = "rgba(2, 132, 199, 0.2)";
    cursor.style.borderColor = "#0284c7";
    cursorDot.style.background = "#0284c7";

    const releaseTarget = getTarget();
    const distance = Math.hypot(cursorX - pointerDownX, cursorY - pointerDownY);
    const target = releaseTarget || pointerDownTarget;

    if (target) {
      target.dispatchEvent(new PointerEvent("pointerup", {
        bubbles: true, cancelable: true, view: window,
        clientX: cursorX, clientY: cursorY, button: 0, buttons: 0
      }));
      target.dispatchEvent(new MouseEvent("mouseup", {
        bubbles: true, cancelable: true, view: window,
        clientX: cursorX, clientY: cursorY, button: 0, buttons: 0
      }));
    }

    if (distance <= CONFIG.clickTolerance && target) {
      const clickable = target.closest("button, a, input, [role='button'], kc-ui-button, [role='menuitem']") || target;
      if (typeof clickable.click === "function") {
        clickable.click();
      } else {
        clickable.dispatchEvent(new MouseEvent("click", {
          bubbles: true, cancelable: true, view: window,
          clientX: cursorX, clientY: cursorY, button: 0
        }));
      }
      showToast("👆 CLICK");
    }
    pointerDownTarget = null;
  }

  function trackingLost() {
    pinching = false;
    pointerDownTarget = null;
    cursorVisible = false;
    cursor.style.display = "none";
  }

  // ==================================================
  // 4. COMPUTER VISION: HEAD GESTURES
  // ==================================================

  function executeHeadAction(action) {
    const el = schematicSurface();
    const r = el.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;

    switch (action) {
      case "HEAD_UP":
        el.dispatchEvent(new WheelEvent("wheel", { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, deltaY: -CONFIG.panStep }));
        showToast("⬆️ HEAD PAN UP");
        break;
      case "HEAD_DOWN":
        el.dispatchEvent(new WheelEvent("wheel", { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, deltaY: CONFIG.panStep }));
        showToast("⬇️ HEAD PAN DOWN");
        break;
      case "HEAD_LEFT":
        el.dispatchEvent(new WheelEvent("wheel", { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, deltaX: -CONFIG.panStep }));
        showToast("⬅️ HEAD PAN LEFT");
        break;
      case "HEAD_RIGHT":
        el.dispatchEvent(new WheelEvent("wheel", { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, deltaX: CONFIG.panStep }));
        showToast("➡️ HEAD PAN RIGHT");
        break;
      case "HEAD_TILT_RIGHT":
        el.dispatchEvent(new WheelEvent("wheel", { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, deltaY: -CONFIG.zoomStep, ctrlKey: true }));
        showToast("🔍 TILT ZOOM IN");
        break;
      case "HEAD_TILT_LEFT":
        el.dispatchEvent(new WheelEvent("wheel", { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, deltaY: CONFIG.zoomStep, ctrlKey: true }));
        showToast("🔎 TILT ZOOM OUT");
        break;
    }
  }

  // ==================================================
  // 5. LIGHT MODE ELECTRONICS LAB IN-PAGE HUD
  // ==================================================

  const hud = document.createElement("div");
  hud.id = "contextswitch-lab-hud";
  Object.assign(hud.style, {
    position: "fixed",
    bottom: "20px",
    right: "20px",
    zIndex: "2147483646",
    background: "#ffffff",
    border: "1px solid #cbd5e1",
    borderRadius: "10px",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
    padding: "8px 14px",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "12px",
    color: "#0f172a",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    transition: "all 0.2s ease"
  });

  hud.innerHTML = `
    <span style="font-weight:700; color:#0284c7; display:flex; align-items:center; gap:4px;">
      ⚡ Lab Mode
    </span>
    <span id="cs-hud-cv-dot" style="width:8px; height:8px; border-radius:50%; background:#16a34a; display:inline-block;" title="CV Connected"></span>
    <span id="cs-hud-status" style="color:#64748b;">CV & Gestures Active</span>
    <button id="cs-hud-mic" style="border:none; background:#e0f2fe; color:#0284c7; border-radius:6px; padding:4px 8px; font-weight:600; cursor:pointer; font-size:11px;" title="Click to speak">
      🎙️ Mic
    </button>
  `;

  document.documentElement.appendChild(hud);

  // In-page speech recognition trigger
  const micBtn = hud.querySelector("#cs-hud-mic");
  let inPageRec = null;

  micBtn.addEventListener("click", () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showToast("Web Speech API not available in this browser window");
      return;
    }
    if (!inPageRec) {
      inPageRec = new SpeechRecognition();
      inPageRec.lang = "en-US";
      inPageRec.onstart = () => {
        micBtn.style.background = "#fee2e2";
        micBtn.style.color = "#dc2626";
        micBtn.textContent = "🔴 Listening...";
        showToast("🎙️ Listening... Speak your command");
      };
      inPageRec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        showToast(`Heard: "${text}"`);
        chrome.runtime.sendMessage({ type: "SUBMIT_VOICE_COMMAND", text }).then(res => {
          if (res?.dispatched) showToast(`✓ Dispatched: ${res.action_name}`);
        }).catch(() => {});
      };
      inPageRec.onend = () => {
        micBtn.style.background = "#e0f2fe";
        micBtn.style.color = "#0284c7";
        micBtn.textContent = "🎙️ Mic";
      };
    }
    try { inPageRec.start(); } catch (_) { inPageRec.stop(); }
  });

  // Floating Toast Overlay
  const toast = document.createElement("div");
  toast.id = "contextswitch-toast";
  Object.assign(toast.style, {
    position: "fixed",
    top: "20px",
    right: "20px",
    zIndex: "2147483647",
    padding: "8px 16px",
    background: "#ffffff",
    color: "#0f172a",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    boxShadow: "0 4px 14px rgba(0, 0, 0, 0.1)",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "13px",
    fontWeight: "600",
    pointerEvents: "none",
    display: "none",
    transition: "opacity 0.2s"
  });
  document.documentElement.appendChild(toast);

  let toastTimer;
  function showToast(text) {
    toast.textContent = text;
    toast.style.display = "block";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.style.display = "none"; }, 1500);
  }

  // ==================================================
  // 6. MESSAGE LISTENERS
  // ==================================================

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "REQUEST_CONTEXT") {
      sendResponse({ context: collectContext("context_requested") });
      return;
    }

    if (message.type === "EXECUTE_ACTION") {
      executeAction(message.action)
        .then(sendResponse)
        .catch(e => sendResponse({ status: "FAILED", verified: false, error: e.message }));
      return true;
    }

    if (message.type === "CONTEXTSWITCH_STATUS") {
      const dot = document.getElementById("cs-hud-cv-dot");
      if (dot) dot.style.background = message.connected ? "#16a34a" : "#dc2626";
      return;
    }

    if (message.type === "CONTEXTSWITCH_CV") {
      const ev = message.event;
      if (!ev?.action) return;

      if (ev.source === "HAND") {
        switch (ev.action) {
          case "CURSOR_MOVE": moveCursor(ev.parameters); break;
          case "PINCH_START": pinchStart(); break;
          case "PINCH_END": pinchEnd(); break;
          case "TRACKING_LOST": trackingLost(); break;
        }
      } else if (ev.source === "HEAD") {
        executeHeadAction(ev.action);
      }
    }
  });

  // Event triggers for continuous context detection
  document.addEventListener("selectionchange", () => sendUpdate("selection_change"));
  document.addEventListener("focusin", () => sendUpdate("focus_change"));
  document.addEventListener("click", () => sendUpdate("click"));
  document.addEventListener("change", () => sendUpdate("input_change"));

  let lastUrl = location.href;
  setInterval(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      sendUpdate("url_change");
    }
  }, 1000);

  sendUpdate("initial_load");
  chrome.runtime.sendMessage({ type: "START_ACTION_POLLING" }).catch(() => {});

  console.log("[ContextSwitch] Multimodal Lab Controller ready on KiCanvas.");
})();
