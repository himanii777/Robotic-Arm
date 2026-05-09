import argparse
import sys
import time

import cv2
import mediapipe as mp


def parse_args():
    parser = argparse.ArgumentParser(description="Live webcam hand tracking demo.")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index.")
    parser.add_argument("--width", type=int, default=960, help="Requested camera width.")
    parser.add_argument("--height", type=int, default=540, help="Requested camera height.")
    parser.add_argument("--max-hands", type=int, default=2, help="Maximum hands to track.")
    parser.add_argument(
        "--model-complexity",
        type=int,
        default=0,
        choices=(0, 1),
        help="0 is faster; 1 may be more accurate.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        message = f"Could not open camera index {args.camera}."
        if sys.platform == "darwin":
            message += (
                " macOS is blocking camera access for this terminal/app. "
                "Enable Camera permission in System Settings > Privacy & Security > Camera, "
                "then restart the terminal and rerun this script."
            )
        else:
            message += " Try --camera 1 or check camera permissions."
        raise RuntimeError(message)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    prev_time = time.perf_counter()
    fps = 0.0

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=args.max_hands,
        model_complexity=args.model_complexity,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera frame read failed.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style(),
                    )

            now = time.perf_counter()
            dt = now - prev_time
            prev_time = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps else 1.0 / dt

            cv2.putText(
                frame,
                f"FPS: {fps:4.1f}  Press q/Esc to quit",
                (16, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (30, 220, 30),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Local Hand Tracking", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
