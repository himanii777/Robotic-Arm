import random
import time

from task_runtime import (
    build_parser,
    make_controller,
    most_common_stable,
    resolve_mode,
)


MODES = {"play", "gesture", "robot_rock", "robot_paper", "robot_scissors"}
MOVES = ("rock", "paper", "scissors")


def distance(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def classify_rps(hand_landmarks, hand_enum):
    lm = hand_landmarks.landmark
    wrist = lm[hand_enum.WRIST]
    fingers = {
        "index": (hand_enum.INDEX_FINGER_TIP, hand_enum.INDEX_FINGER_PIP),
        "middle": (hand_enum.MIDDLE_FINGER_TIP, hand_enum.MIDDLE_FINGER_PIP),
        "ring": (hand_enum.RING_FINGER_TIP, hand_enum.RING_FINGER_PIP),
        "pinky": (hand_enum.PINKY_TIP, hand_enum.PINKY_PIP),
    }
    open_state = {}
    for name, (tip_id, pip_id) in fingers.items():
        tip = lm[tip_id]
        pip = lm[pip_id]
        open_state[name] = distance(tip, wrist) > distance(pip, wrist) * 1.10

    open_count = sum(1 for is_open in open_state.values() if is_open)
    if open_state["index"] and open_state["middle"] and not open_state["ring"] and not open_state["pinky"]:
        return "scissors"
    if open_count >= 3:
        return "paper"
    if open_count <= 1:
        return "rock"
    return None


def detect_player_move(args, seconds=4.0):
    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError("MediaPipe and OpenCV are required for play mode.") from exc

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera index {}.".format(args.camera))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    readings = []
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    start = time.perf_counter()
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        while time.perf_counter() - start < seconds:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True
            gesture = None
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                gesture = classify_rps(hand, mp_hands.HandLandmark)
                if gesture:
                    readings.append(gesture)
                if not args.no_preview:
                    mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            if not args.no_preview:
                label = gesture or "show rock/paper/scissors"
                cv2.putText(
                    frame,
                    label,
                    (18, 34),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (80, 220, 80),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow("Rock paper scissors", frame)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break

    cap.release()
    if not args.no_preview:
        cv2.destroyWindow("Rock paper scissors")

    stable = most_common_stable(readings, minimum_count=5)
    if stable:
        return stable
    return readings[-1] if readings else None


def robot_show(controller, move):
    if move == "rock":
        controller.pose("rock", "robot shows rock", {"wrist_pitch": 4.0}, 0.45)
    elif move == "paper":
        controller.pose("paper", "robot shows paper", {"wrist_pitch": 4.0}, 0.45)
    elif move == "scissors":
        controller.pose("scissors", "robot shows scissors", {"wrist_pitch": 4.0}, 0.45)


def winner(player, robot):
    if player == robot:
        return "tie"
    wins = {
        ("rock", "scissors"),
        ("scissors", "paper"),
        ("paper", "rock"),
    }
    return "player" if (player, robot) in wins else "robot"


def play(controller, args):
    controller.say("Rock paper scissors. Shoot.")
    for label in ("rock", "paper", "scissors", "shoot"):
        print("[game] {}".format(label))
        controller.beep(520 if label != "shoot" else 760, 120)
        controller.pause(0.35, label)

    try:
        player = detect_player_move(args)
    except RuntimeError as exc:
        print("[game] {}".format(exc))
        player = None

    robot = random.choice(MOVES)
    robot_show(controller, robot)
    if player is None:
        controller.say("I could not read your hand. Robot picked {}.".format(robot))
        controller.reset()
        return

    result = winner(player, robot)
    print("[game] player={} robot={} result={}".format(player, robot, result))
    if result == "tie":
        controller.say("Tie. Great minds choose {}.".format(robot))
    elif result == "player":
        controller.say("You win. I respect the strategy.")
    else:
        controller.say("Robot wins this round.")
        controller.pose("thumbs_up", "robot victory thumbs up", {"wrist_pitch": 18.0}, 0.45)
    controller.reset()


def gesture_only(args):
    try:
        player = detect_player_move(args)
    except RuntimeError as exc:
        print("[gesture] {}".format(exc))
        return
    print("[gesture] {}".format(player or "unknown"))


def main():
    parser = build_parser("Rock paper scissors demo.", MODES, "play")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)

    if mode == "gesture":
        gesture_only(args)
        return

    controller = make_controller(args, "Rock Paper Scissors")
    if not args.skip_countdown:
        controller.countdown(mode)

    if mode == "play":
        play(controller, args)
    elif mode == "robot_rock":
        robot_show(controller, "rock")
    elif mode == "robot_paper":
        robot_show(controller, "paper")
    elif mode == "robot_scissors":
        robot_show(controller, "scissors")
    controller.reset()


if __name__ == "__main__":
    main()
