
import time
import cv2

from vision.head_tracker import HeadTracker
from vision.gestures import GestureRecognizer


def main():
    tracker = HeadTracker()
    gestures = GestureRecognizer()

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        tracker.close()
        raise RuntimeError("Could not open webcam")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    last_action = "NONE"
    last_action_time = 0.0

    print("Beyond Touch - Head Gesture Test")
    print("C = Calibrate neutral pose")
    print("R = Reset calibration")
    print("Q = Quit")

    try:
        while True:
            success, frame = camera.read()

            if not success:
                break

            frame = cv2.flip(frame, 1)

            pose = tracker.process(frame)
            event = gestures.process(pose)

            if event:
                last_action = event["action"]
                last_action_time = time.monotonic()
                print("HEAD EVENT:", event)

            tracking_status = pose.get(
                "tracking_status", "UNKNOWN"
            )

            cv2.putText(
                frame,
                f"TRACKING: {tracking_status}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0)
                if pose.get("valid_for_actions")
                else (0, 0, 255),
                2
            )

            if gestures.neutral is None:
                message = "PRESS C TO CALIBRATE"
                color = (0, 255, 255)
            else:
                message = (
                    "READY"
                    if gestures.armed
                    else "RETURN TO NEUTRAL"
                )
                color = (0, 255, 0)

            cv2.putText(
                frame,
                message,
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

            if pose.get("valid_for_actions"):
                cv2.putText(
                    frame,
                    (
                        f"P:{pose['pitch']:.1f} "
                        f"Y:{pose['yaw']:.1f} "
                        f"R:{pose['roll']:.1f}"
                    ),
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1
                )

            if time.monotonic() - last_action_time < 2:
                cv2.putText(
                    frame,
                    f"ACTION: {last_action}",
                    (20, 145),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 0),
                    2
                )

            cv2.putText(
                frame,
                "C: Calibrate | R: Reset | Q: Quit",
                (20, 450),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

            cv2.imshow(
                "Beyond Touch - Head Gestures",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("c"):
                if gestures.calibrate(pose):
                    print("Neutral pose calibrated")
                else:
                    print("Calibration failed: face not stable")

            elif key == ord("r"):
                gestures.reset()
                print("Calibration reset")

            elif key == ord("q"):
                break

    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
