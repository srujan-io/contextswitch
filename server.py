
import asyncio
import json
import threading
import time
import traceback
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from vision.head_tracker import HeadTracker
from vision.hand_tracker import HandTracker
from vision.gestures import GestureRecognizer
from vision.events import EventTranslator


CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
SHOW_PREVIEW = True

clients = set()
clients_lock = threading.Lock()

event_queue = None
stop_event = threading.Event()
camera_thread = None
main_loop = None


def broadcast_event(event):
    if main_loop is None or event_queue is None:
        return

    def enqueue():
        try:
            event_queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    try:
        main_loop.call_soon_threadsafe(enqueue)
    except RuntimeError:
        pass


def get_angle(pose, name):
    if not isinstance(pose, dict):
        return None

    value = pose.get(name)

    if value is None:
        value = pose.get(f"{name}_deg")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def draw_text(frame, text, y, color=(255, 255, 255)):
    cv2.putText(
        frame,
        text,
        (15, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )


def diagnostic_head_events():
    actions = [
        "HEAD_UP",
        "HEAD_DOWN",
        "HEAD_LEFT",
        "HEAD_RIGHT",
        "HEAD_TILT_LEFT",
        "HEAD_TILT_RIGHT",
    ]

    for action in actions:
        yield {
            "source": "HEAD",
            "action": action,
            "parameters": {"diagnostic": True},
            "timestamp": int(time.time() * 1000),
        }


def camera_worker():
    cap = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW,
    )

    if not cap.isOpened():
        print("[CV] Camera failed to open")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    head = None
    hand = None

    try:
        head = HeadTracker()
        hand = HandTracker()
        gestures = GestureRecognizer()
        translator = EventTranslator(cursor_hz=25)

        last_head_action = "NONE"
        last_debug = 0.0

        print("[CV] Camera tracking started")
        print(
            "[CV] C=calibrate | R=reset | "
            "T=test WS | Q=quit"
        )

        while not stop_event.is_set():
            ok, frame = cap.read()

            if not ok:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)

            # -----------------------------
            # HEAD + HAND TRACKING
            # -----------------------------

            pose = head.process(frame)
            hand_data = hand.process(frame)

            pitch = get_angle(pose, "pitch")
            yaw = get_angle(pose, "yaw")
            roll = get_angle(pose, "roll")

            status = (
                pose.get("tracking_status", "UNKNOWN")
                if isinstance(pose, dict)
                else "NO FACE"
            )

            valid = bool(
                isinstance(pose, dict)
                and pose.get("valid_for_actions", False)
            )

            # -----------------------------
            # GESTURE RECOGNITION
            # -----------------------------

            gesture_event = gestures.process(pose)

            if gesture_event:
                print(
                    "[RAW HEAD GESTURE]",
                    gesture_event,
                    flush=True,
                )

            # -----------------------------
            # EVENT TRANSLATION
            # -----------------------------

            head_events = translator.process_head(
                pose,
                gesture_event,
            )

            hand_events = translator.process_hand(
                hand_data
            )

            for event in head_events:
                action = event.get("action")

                if action != "TRACKING_LOST":
                    last_head_action = action

                    print(
                        "[HEAD WS EVENT]",
                        event,
                        flush=True,
                    )

            for event in head_events + hand_events:
                broadcast_event(event)

            # -----------------------------
            # DEBUG LOG
            # -----------------------------

            now = time.monotonic()

            if now - last_debug >= 2.0:
                last_debug = now

                print(
                    "[HEAD STATUS]",
                    f"tracking={status}",
                    f"valid={valid}",
                    f"calibrated={gestures.neutral is not None}",
                    f"pitch={pitch}",
                    f"yaw={yaw}",
                    f"roll={roll}",
                    flush=True,
                )

            # -----------------------------
            # CAMERA PREVIEW
            # -----------------------------

            if SHOW_PREVIEW:
                draw_text(
                    frame,
                    f"HEAD: {status}",
                    30,
                    (0, 255, 0) if valid
                    else (0, 0, 255),
                )

                draw_text(
                    frame,
                    f"PITCH: {pitch:.1f}"
                    if pitch is not None
                    else "PITCH: N/A",
                    60,
                )

                draw_text(
                    frame,
                    f"YAW: {yaw:.1f}"
                    if yaw is not None
                    else "YAW: N/A",
                    90,
                )

                draw_text(
                    frame,
                    f"ROLL: {roll:.1f}"
                    if roll is not None
                    else "ROLL: N/A",
                    120,
                )

                calibrated = gestures.neutral is not None

                draw_text(
                    frame,
                    f"CALIBRATED: {calibrated}",
                    150,
                    (0, 255, 0) if calibrated
                    else (0, 165, 255),
                )

                draw_text(
                    frame,
                    f"LAST HEAD: {last_head_action}",
                    180,
                    (0, 255, 255),
                )

                hand_detected = bool(
                    hand_data
                    and hand_data.get("detected")
                )

                draw_text(
                    frame,
                    f"HAND: {'YES' if hand_detected else 'NO'}",
                    210,
                    (0, 255, 0) if hand_detected
                    else (0, 0, 255),
                )

                draw_text(
                    frame,
                    "C: Calibrate | R: Reset",
                    440,
                )

                draw_text(
                    frame,
                    "T: Test WS | Q: Quit",
                    465,
                )

                cv2.imshow(
                    "Beyond Touch CV Server",
                    frame,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("c"):
                    print("[HEAD] C pressed", flush=True)

                    success = gestures.calibrate(pose)

                    print(
                        "[HEAD] Manual calibration:",
                        "SUCCESS" if success else "FAILED",
                        flush=True,
                    )

                elif key == ord("r"):
                    gestures.reset()
                    last_head_action = "NONE"

                    print(
                        "[HEAD] Calibration reset",
                        flush=True,
                    )

                elif key == ord("t"):
                    print(
                        "[TEST] Sending six synthetic "
                        "head events",
                        flush=True,
                    )

                    for event in diagnostic_head_events():
                        broadcast_event(event)

                elif key == ord("q"):
                    stop_event.set()
                    break

    except Exception:
        print("[CV] Camera worker error")
        traceback.print_exc()

    finally:
        cap.release()
        cv2.destroyAllWindows()

        for tracker in (head, hand):
            if tracker is not None and hasattr(
                tracker, "close"
            ):
                tracker.close()

        print("[CV] Camera stopped")


async def event_dispatcher():
    while not stop_event.is_set():
        try:
            event = await asyncio.wait_for(
                event_queue.get(),
                timeout=0.5,
            )
        except asyncio.TimeoutError:
            continue

        with clients_lock:
            targets = list(clients)

        if not targets:
            continue

        message = json.dumps(event)
        disconnected = []

        for websocket in targets:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)

        if disconnected:
            with clients_lock:
                for websocket in disconnected:
                    clients.discard(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_queue, camera_thread, main_loop

    main_loop = asyncio.get_running_loop()
    event_queue = asyncio.Queue(maxsize=256)

    stop_event.clear()

    camera_thread = threading.Thread(
        target=camera_worker,
        daemon=True,
    )

    camera_thread.start()

    dispatcher_task = asyncio.create_task(
        event_dispatcher()
    )

    print(
        "[SERVER] WebSocket available at "
        "ws://127.0.0.1:8000/ws/cv"
    )

    try:
        yield

    finally:
        stop_event.set()
        await dispatcher_task

        if camera_thread:
            await asyncio.to_thread(
                camera_thread.join,
                3.0,
            )


app = FastAPI(
    title="Beyond Touch CV Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    with clients_lock:
        connected = len(clients)

    return {
        "status": "ok",
        "camera_running": (
            camera_thread is not None
            and camera_thread.is_alive()
            and not stop_event.is_set()
        ),
        "connected_clients": connected,
    }


@app.websocket("/ws/cv")
async def cv_websocket(websocket: WebSocket):
    if websocket.client and websocket.client.host not in (
        "127.0.0.1",
        "::1",
    ):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    with clients_lock:
        clients.add(websocket)

    print("[WS] Client connected")

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    except Exception as exc:
        print("[WS] Client error:", exc)

    finally:
        with clients_lock:
            clients.discard(websocket)

        print("[WS] Client disconnected")
