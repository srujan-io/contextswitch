
import time
import math

import cv2
import pyautogui

from vision.hand_tracker import HandTracker


# ---------------- CONFIGURATION ----------------

CAMERA_INDEX = 0

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Active tracking area inside webcam frame
MARGIN_X = 0.12
MARGIN_Y = 0.12

# Adaptive smoothing
# Slow movement = stable cursor
# Fast movement = responsive cursor
MIN_SMOOTHING = 0.18
MAX_SMOOTHING = 0.85
SPEED_THRESHOLD = 90

# Ignore very tiny cursor movements
DEADZONE_PX = 2

# Pinch and drag settings
DRAG_HOLD_SECONDS = 0.45
DRAG_DISTANCE_PX = 25
PINCH_DEBOUNCE_SECONDS = 0.06

# ------------------------------------------------

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

SCREEN_W, SCREEN_H = pyautogui.size()


def clamp(value, low, high):
    return max(low, min(high, value))


def map_to_screen(x, y):
    x = (x - MARGIN_X) / (1 - 2 * MARGIN_X)
    y = (y - MARGIN_Y) / (1 - 2 * MARGIN_Y)

    x = clamp(x, 0, 1)
    y = clamp(y, 0, 1)

    return (
        5 + x * (SCREEN_W - 10),
        5 + y * (SCREEN_H - 10),
    )


def main():
    tracker = HandTracker()

    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():
        tracker.close()
        raise RuntimeError("Could not open webcam")

    # Attempt to reduce camera buffering
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )
    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    enabled = False

    smoothed_x = None
    smoothed_y = None

    pinch_started_at = None
    pinch_origin = None
    pinch_pending = False

    dragging = False
    last_status = "PAUSED"

    previous_frame_time = time.monotonic()
    fps = 0.0

    print("Beyond Touch - Windows Cursor")
    print("--------------------------------")
    print("P = Pause / Resume")
    print("Q = Quit")
    print("Quick pinch = Left click")
    print("Hold pinch and move = Drag")
    print("Top-left corner = Emergency failsafe")

    def release_drag():
        nonlocal dragging

        if dragging:
            pyautogui.mouseUp(button="left")
            dragging = False

    def reset_pinch():
        nonlocal pinch_started_at
        nonlocal pinch_origin
        nonlocal pinch_pending

        pinch_started_at = None
        pinch_origin = None
        pinch_pending = False

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("Camera frame unavailable")
                break

            # Mirror camera for intuitive movement
            frame = cv2.flip(frame, 1)

            hand = tracker.process(frame)

            now = time.monotonic()

            # ---------------- FPS ----------------

            dt = now - previous_frame_time
            previous_frame_time = now

            if dt > 0:
                instant_fps = 1.0 / dt

                if fps == 0:
                    fps = instant_fps
                else:
                    fps = (
                        0.85 * fps
                        + 0.15 * instant_fps
                    )

            # ------------ CURSOR CONTROL ------------

            if enabled and hand["detected"]:

                target_x, target_y = map_to_screen(
                    hand["index_x"],
                    hand["index_y"]
                )

                # Initialize cursor position
                if smoothed_x is None:
                    smoothed_x = target_x
                    smoothed_y = target_y

                else:
                    distance = math.hypot(
                        target_x - smoothed_x,
                        target_y - smoothed_y
                    )

                    # Adaptive smoothing
                    speed_factor = min(
                        distance / SPEED_THRESHOLD,
                        1.0
                    )

                    alpha = (
                        MIN_SMOOTHING
                        + (
                            MAX_SMOOTHING
                            - MIN_SMOOTHING
                        ) * speed_factor
                    )

                    smoothed_x += alpha * (
                        target_x - smoothed_x
                    )

                    smoothed_y += alpha * (
                        target_y - smoothed_y
                    )

                cursor_x = int(smoothed_x)
                cursor_y = int(smoothed_y)

                # Avoid unnecessary mouse updates
                current_x, current_y = pyautogui.position()

                movement = math.hypot(
                    cursor_x - current_x,
                    cursor_y - current_y
                )

                if movement >= DEADZONE_PX:
                    pyautogui.moveTo(
                        cursor_x,
                        cursor_y,
                        duration=0
                    )

                # ---------------- PINCH ----------------

                pinching = hand["pinching"]

                if pinching:

                    if pinch_started_at is None:
                        pinch_started_at = now

                        pinch_origin = (
                            cursor_x,
                            cursor_y
                        )

                        pinch_pending = True

                    held_time = (
                        now - pinch_started_at
                    )

                    if (
                        pinch_pending
                        and held_time
                        >= PINCH_DEBOUNCE_SECONDS
                    ):
                        pinch_pending = False

                    # Start dragging after sustained pinch
                    if (
                        not dragging
                        and not pinch_pending
                        and held_time
                        >= DRAG_HOLD_SECONDS
                    ):

                        distance = math.hypot(
                            cursor_x - pinch_origin[0],
                            cursor_y - pinch_origin[1]
                        )

                        if distance >= DRAG_DISTANCE_PX:

                            # Start drag at pinch origin
                            pyautogui.moveTo(
                                *pinch_origin,
                                duration=0
                            )

                            pyautogui.mouseDown(
                                button="left"
                            )

                            dragging = True

                            pyautogui.moveTo(
                                cursor_x,
                                cursor_y,
                                duration=0
                            )

                            print("DRAG_START")

                else:

                    if pinch_started_at is not None:

                        duration = (
                            now - pinch_started_at
                        )

                        if dragging:

                            release_drag()
                            print("DRAG_END")

                        elif (
                            duration
                            >= PINCH_DEBOUNCE_SECONDS
                            and duration
                            < DRAG_HOLD_SECONDS
                        ):

                            pyautogui.click(
                                button="left"
                            )

                            print("CLICK")

                        reset_pinch()

                # -------------- STATUS --------------

                if dragging:
                    last_status = "DRAGGING"

                elif pinching:
                    last_status = "PINCHING"

                else:
                    last_status = "TRACKING"

            else:

                # Stop safely when hand disappears
                release_drag()
                reset_pinch()

                smoothed_x = None
                smoothed_y = None

                last_status = (
                    "NO HAND"
                    if enabled
                    else "PAUSED"
                )

            # ---------------- DISPLAY ----------------

            status_color = (
                (0, 255, 0)
                if enabled
                else (0, 0, 255)
            )

            cv2.putText(
                frame,
                f"CONTROL: {'ON' if enabled else 'OFF'}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                status_color,
                2
            )

            cv2.putText(
                frame,
                f"STATUS: {last_status}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "P: Pause/Resume | Q: Quit",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1
            )

            cv2.imshow(
                "Beyond Touch - Cursor Control",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("p"):

                enabled = not enabled

                release_drag()
                reset_pinch()

                smoothed_x = None
                smoothed_y = None

                print(
                    "CONTROL ENABLED"
                    if enabled
                    else "CONTROL PAUSED"
                )

            elif key == ord("q"):
                break

    except pyautogui.FailSafeException:
        print("Emergency failsafe activated")

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        release_drag()

        camera.release()
        tracker.close()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
