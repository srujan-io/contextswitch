"""
Computer Vision Service for ContextSwitch
Integrates MediaPipe face & hand landmarkers, head gesture recognition,
virtual cursor tracking, pinch-to-click, and WebSocket broadcast.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import traceback
from pathlib import Path
from typing import Any

import cv2
from fastapi import WebSocket, WebSocketDisconnect

# Ensure vision module is importable
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from vision.head_tracker import HeadTracker
    from vision.hand_tracker import HandTracker
    from vision.gestures import GestureRecognizer
    from vision.events import EventTranslator
except ImportError as exc:
    print(f"[CV] Vision module import error: {exc}")
    HeadTracker = None
    HandTracker = None
    GestureRecognizer = None
    EventTranslator = None


class CVService:
    def __init__(self, camera_index: int = 0, show_preview: bool = False):
        self.camera_index = camera_index
        self.show_preview = show_preview
        self.clients = set()
        self.clients_lock = threading.Lock()
        self.event_queue: asyncio.Queue | None = None
        self.stop_event = threading.Event()
        self.camera_thread: threading.Thread | None = None
        self.main_loop: asyncio.AbstractEventLoop | None = None

        self.head_tracker = None
        self.hand_tracker = None
        self.gestures = None
        self.translator = None

        self.last_pose = {}
        self.last_hand = {}
        self.last_head_action = "NONE"
        self.camera_running = False
        self.camera_error = None
        self.event_history = []

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.main_loop = loop
        self.event_queue = asyncio.Queue(maxsize=512)

    def broadcast_event(self, event: dict[str, Any]):
        """Queue event for async broadcast to WebSocket clients."""
        if not self.main_loop or not self.event_queue:
            return

        self.event_history.append(event)
        if len(self.event_history) > 50:
            self.event_history.pop(0)

        def enqueue():
            try:
                self.event_queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

        try:
            self.main_loop.call_soon_threadsafe(enqueue)
        except RuntimeError:
            pass

    def start_camera(self):
        """Starts the CV camera worker thread."""
        if self.camera_thread and self.camera_thread.is_alive():
            return

        self.stop_event.clear()
        self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.camera_thread.start()
        print("[CV] Camera worker thread started.")

    def stop_camera(self):
        """Stops the camera worker thread."""
        self.stop_event.set()
        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)
            self.camera_thread = None
        self.camera_running = False
        print("[CV] Camera worker thread stopped.")

    def calibrate_neutral(self) -> bool:
        """Calibrate the neutral head pose using the current head pose."""
        if self.gestures and self.last_pose:
            success = self.gestures.calibrate(self.last_pose)
            print(f"[CV] Manual neutral pose calibration: {'SUCCESS' if success else 'FAILED'}")
            return bool(success)
        return False

    def reset_neutral(self):
        """Reset head gesture calibration."""
        if self.gestures:
            self.gestures.reset()
            self.last_head_action = "NONE"
            print("[CV] Head gesture calibration reset.")

    def inject_event(self, source: str, action: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Inject a synthetic CV event (used for UI testing or labs without webcams)."""
        event = {
            "source": source.upper(),
            "action": action.upper(),
            "parameters": parameters or {},
            "timestamp": int(time.time() * 1000)
        }
        self.broadcast_event(event)
        return event

    def get_status(self) -> dict[str, Any]:
        with self.clients_lock:
            client_count = len(self.clients)

        calibrated = False
        if self.gestures and getattr(self.gestures, "neutral", None) is not None:
            calibrated = True

        return {
            "camera_running": self.camera_running,
            "camera_error": self.camera_error,
            "connected_clients": client_count,
            "calibrated": calibrated,
            "last_head_action": self.last_head_action,
            "latest_pose": self.last_pose,
            "latest_hand": {
                "detected": self.last_hand.get("detected", False),
                "index_x": self.last_hand.get("index_x"),
                "index_y": self.last_hand.get("index_y"),
                "pinching": self.last_hand.get("pinching", False),
                "pinch_ratio": self.last_hand.get("pinch_ratio")
            } if self.last_hand else None,
            "recent_events": self.event_history[-10:]
        }

    def _camera_worker(self):
        """Worker loop that captures frames, runs vision models, and emits events."""
        if not HeadTracker or not HandTracker or not GestureRecognizer or not EventTranslator:
            self.camera_error = "Vision dependencies not available"
            self.camera_running = False
            return

        try:
            self.head_tracker = HeadTracker()
            self.hand_tracker = HandTracker()
            self.gestures = GestureRecognizer()
            self.translator = EventTranslator()
        except Exception as e:
            self.camera_error = f"Model load error: {e}"
            print(f"[CV] Error loading MediaPipe models: {e}")
            self.camera_running = False
            return

        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            self.camera_error = f"Could not open webcam index {self.camera_index}"
            print(f"[CV] Webcam index {self.camera_index} unavailable. Simulation/WebSocket active.")
            self.camera_running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera_running = True
        self.camera_error = None
        print(f"[CV] Camera opened successfully at 640x480.")

        try:
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.02)
                    continue

                # Mirror preview horizontally for intuitive cursor control
                frame = cv2.flip(frame, 1)

                # 1. Head pose & gesture recognition
                pose = self.head_tracker.process(frame)
                self.last_pose = pose
                gesture_event = self.gestures.process(pose)

                # 2. Hand tracking & pinch
                hand_data = self.hand_tracker.process(frame)
                self.last_hand = hand_data

                # 3. Translate to browser events
                head_events = self.translator.process_head(pose, gesture_event)
                hand_events = self.translator.process_hand(hand_data)

                for ev in head_events:
                    action = ev.get("action")
                    if action != "TRACKING_LOST":
                        self.last_head_action = action
                    self.broadcast_event(ev)

                for ev in hand_events:
                    self.broadcast_event(ev)

                if self.show_preview:
                    cv2.imshow("ContextSwitch CV Debug", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                time.sleep(0.01)

        except Exception as exc:
            self.camera_error = str(exc)
            print(f"[CV] Camera worker exception: {exc}")
            traceback.print_exc()

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.camera_running = False
            if self.head_tracker:
                self.head_tracker.close()
            if self.hand_tracker:
                self.hand_tracker.close()
            print("[CV] Camera worker exited.")

    async def event_dispatcher(self):
        """Asynchronously dispatch events from the queue to all connected WebSockets."""
        while not self.stop_event.is_set():
            if not self.event_queue:
                await asyncio.sleep(0.1)
                continue

            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            with self.clients_lock:
                targets = list(self.clients)

            if not targets:
                continue

            payload = json.dumps(event)
            disconnected = []

            for ws in targets:
                try:
                    await ws.send_text(payload)
                except Exception:
                    disconnected.append(ws)

            if disconnected:
                with self.clients_lock:
                    for ws in disconnected:
                        self.clients.discard(ws)

    async def handle_websocket(self, websocket: WebSocket):
        """Handles new WebSocket connection at /ws/cv."""
        await websocket.accept()
        with self.clients_lock:
            self.clients.add(websocket)
        print(f"[CV WS] Client connected (Total clients: {len(self.clients)})")

        try:
            while True:
                # Keep connection alive & handle incoming client messages if any
                text = await websocket.receive_text()
                try:
                    data = json.loads(text)
                    if data.get("type") == "CALIBRATE":
                        self.calibrate_neutral()
                    elif data.get("type") == "RESET":
                        self.reset_neutral()
                    elif data.get("type") == "INJECT_EVENT":
                        ev = data.get("event", {})
                        self.broadcast_event(ev)
                except Exception:
                    pass
        except WebSocketDisconnect:
            pass
        finally:
            with self.clients_lock:
                self.clients.discard(websocket)
            print(f"[CV WS] Client disconnected (Remaining: {len(self.clients)})")
