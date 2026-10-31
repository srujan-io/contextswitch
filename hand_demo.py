
import cv2
from vision.hand_tracker import HandTracker


def main():
    tracker = HandTracker()

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        tracker.close()
        raise RuntimeError("Could not open webcam")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Beyond Touch - Hand Tracking")
    print("Move your index finger to track its coordinates.")
    print("Pinch thumb + index finger to test clicking.")
    print("Press Q to quit.")

    try:
        while True:
            ret, frame = camera.read()

            if not ret:
                print("Camera frame unavailable")
                break

            # Mirror preview for intuitive movement
            frame = cv2.flip(frame, 1)

            hand = tracker.process(frame)

            if hand["detected"]:
                x = hand["index_x"]
                y = hand["index_y"]

                cv2.putText(
                    frame,
                    f"INDEX: ({x:.2f}, {y:.2f})",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2
                )

                status = (
                    "PINCHING" if hand["pinching"]
                    else "HAND TRACKING"
                )

                color = (
                    (0, 0, 255) if hand["pinching"]
                    else (0, 255, 0)
                )

                cv2.putText(
                    frame,
                    status,
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    f"Pinch ratio: {hand['pinch_ratio']:.2f}",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1
                )

                if hand["pinch_event"]:
                    print(
                        f"{hand['pinch_event']} "
                        f"at ({x:.2f}, {y:.2f})"
                    )

            else:
                cv2.putText(
                    frame,
                    "NO HAND DETECTED",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            cv2.imshow("Beyond Touch - Hand Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
