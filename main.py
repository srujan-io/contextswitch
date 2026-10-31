
import cv2

from vision.head_tracker import HeadTracker


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError("Could not access webcam")

    tracker = HeadTracker()

    print("Beyond Touch - Head Tracking")
    print("Press Q to quit")

    try:
        while True:
            success, frame = cap.read()

            if not success:
                print("Failed to read webcam frame")
                break

            result = tracker.process(frame)
            status = result["tracking_status"]

            if status == "TRACKING":
                color = (0, 255, 0)
                message = "TRACKING ACTIVE"

            elif status == "RECOVERING":
                color = (0, 255, 255)
                message = "REACQUIRING FACE..."

            elif status == "TEMPORARILY_LOST":
                color = (0, 255, 255)
                message = "TEMPORARY OCCLUSION - ACTIONS DISABLED"

            else:
                color = (0, 0, 255)
                message = "FACE LOST - HEAD CONTROL PAUSED"

            cv2.putText(
                frame,
                message,
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

            if "pitch" in result:
                cv2.putText(
                    frame,
                    f"Pitch: {result['pitch']:.1f}",
                    (15, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Yaw: {result['yaw']:.1f}",
                    (15, 115),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Roll: {result['roll']:.1f}",
                    (15, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )

            cv2.putText(
                frame,
                "Q = Quit",
                (15, 195),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (200, 200, 200),
                1,
            )

            cv2.imshow(
                "Beyond Touch - Head Tracking",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
