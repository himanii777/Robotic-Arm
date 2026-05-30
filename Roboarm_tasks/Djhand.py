from task_runtime import build_parser, make_controller, resolve_mode


MODES = {"do_task", "default", "scratch", "button", "beat_drop", "wave", "party"}


def scratch(controller):
    controller.say("DJ arm is now with artificial rhythm.")
    controller.pose("open_hand", "palm-up turntable hover", {"wrist": 18.0}, 0.45)
    for _ in range(3):
        controller.move("scratch left", {"yaw": -24.0, "wrist": 24.0}, 0.22)
        controller.move("scratch right", {"yaw": 24.0, "wrist": 10.0}, 0.22)
    controller.move("center on record", {"yaw": 0.0, "wrist": 18.0}, 0.25)


def button(controller):
    controller.say("Dropping the beat.")
    controller.pose("point", "index over button", {"yaw": 28.0, "wrist": 10.0}, 0.4)
    controller.move("button press", {"wrist": 38.0}, 0.25)
    controller.move("button release", {"wrist": 10.0}, 0.25)


def beat_drop(controller):
    controller.play_audio(("dj", "beat", "party", "drop"))
    controller.pose("fist", "hold for beat drop", {"wrist": 6.0, "yaw": 0.0}, 0.35)
    controller.pause(0.8, "build tension")
    controller.pose("paper", "raise hand open", {"wrist": 42.0}, 0.45)
    for angle in (-18.0, 18.0, -14.0, 14.0, 0.0):
        controller.move("crowd pump", {"yaw": angle, "wrist": 42.0}, 0.26)


def wave(controller):
    controller.pose("open_hand", "wave at crowd", {"wrist": 28.0}, 0.45)
    for angle in (-28.0, 28.0, -24.0, 24.0, 0.0):
        controller.move("crowd wave", {"yaw": angle, "wrist": 28.0}, 0.26)


def party(controller):
    scratch(controller)
    button(controller)
    beat_drop(controller)
    wave(controller)
    controller.pause(0.7, "hold party pose")


def return_default(controller):
    controller.say("Returning to default.")
    controller.reset()


def main():
    parser = build_parser("DJ hand demo routines.", MODES, "do_task")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "DJ Hand")
    if not args.skip_countdown:
        controller.countdown(mode)

    actions = {
        "do_task": party,
        "scratch": scratch,
        "button": button,
        "beat_drop": beat_drop,
        "wave": wave,
        "party": party,
        "default": return_default,
    }
    actions[mode](controller)


if __name__ == "__main__":
    main()


# /*
# Undo/default code:
# def undo_task(controller):
#     controller.reset()
# Run it with:
# python Roboarm_tasks\Djhand.py --mode default --driver ble --no-preview
# */
