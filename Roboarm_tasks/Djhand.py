from task_runtime import (
    build_parser,
    camera_alignment_preview,
    make_controller,
    resolve_mode,
)


MODES = {"scratch", "button", "beat_drop", "wave", "party"}


def scratch(controller):
    controller.say("DJ arm is now with artificial rhythm.")
    controller.pose("open_hand", "hover over turntable", {"wrist_pitch": -12.0, "wrist_roll": 0.0}, 0.45)
    for _ in range(3):
        controller.move("scratch left", {"yaw": -24.0, "wrist_roll": -12.0}, 0.22)
        controller.move("scratch right", {"yaw": 24.0, "wrist_roll": 12.0}, 0.22)
    controller.move("center on record", {"yaw": 0.0, "wrist_roll": 0.0}, 0.25)


def button(controller):
    controller.say("Dropping the beat.")
    controller.pose("point", "index over button", {"yaw": 28.0, "wrist_pitch": -8.0}, 0.4)
    controller.move("button press", {"wrist_pitch": -34.0}, 0.25)
    controller.move("button release", {"wrist_pitch": -8.0}, 0.25)


def beat_drop(controller):
    controller.play_audio(("dj", "beat", "party", "drop"))
    controller.pose("fist", "hold for beat drop", {"wrist_pitch": -6.0, "yaw": 0.0}, 0.35)
    controller.pause(0.8, "build tension")
    controller.pose("paper", "raise hand open", {"wrist_pitch": 36.0, "wrist_roll": 0.0}, 0.45)
    for angle in (-18.0, 18.0, -14.0, 14.0, 0.0):
        controller.move("crowd pump", {"yaw": angle, "wrist_pitch": 32.0}, 0.26)


def wave(controller):
    controller.pose("open_hand", "wave at crowd", {"wrist_pitch": 18.0}, 0.45)
    for angle in (-28.0, 28.0, -24.0, 24.0, 0.0):
        controller.move("crowd wave", {"yaw": angle, "wrist_roll": angle * 0.4}, 0.26)
    controller.reset()


def party(controller):
    scratch(controller)
    button(controller)
    beat_drop(controller)
    wave(controller)


def main():
    parser = build_parser("DJ hand demo routines.", MODES, "party")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    camera_alignment_preview(
        args.camera,
        args.width,
        args.height,
        seconds=1.6,
        preview=not args.no_preview,
        label="align fake turntable",
    )
    controller = make_controller(args, "DJ Hand")
    if not args.skip_countdown:
        controller.countdown(mode)

    actions = {
        "scratch": scratch,
        "button": button,
        "beat_drop": beat_drop,
        "wave": wave,
        "party": party,
    }
    actions[mode](controller)


if __name__ == "__main__":
    main()
