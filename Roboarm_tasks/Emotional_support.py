from task_runtime import build_parser, make_controller, resolve_mode


MODES = {"do_task", "default"}


def grip_cup(controller):
    controller.pose("default", "open palm upward", duration=0.55)
    controller.pause(0.8, "place cup in palm")
    controller.pose("pinky_closed", "pinky locks cup first", {"wrist": 0.0}, 0.65)
    controller.pose("cup_grip", "half close cup grip", {"wrist": 0.0}, 0.85)


def pour_support_drink(controller):
    controller.say("Here you go. A drink will always make you feel better.")
    controller.move("offer cup", {"yaw": 8.0, "wrist": 0.0}, 0.45)
    controller.move("pour drink", {"wrist": 72.0}, 1.0)
    controller.pause(1.15, "drink pour")
    controller.move("cup upright", {"wrist": 0.0}, 0.75)
    controller.play_audio(("comfort", "support", "happy", "drink", "song"))
    for angle in (-10.0, 10.0, 0.0):
        controller.move("gentle comfort sway", {"yaw": angle}, 0.35)


def do_task(controller):
    controller.say("Emotional support mode activated.")
    grip_cup(controller)
    pour_support_drink(controller)
    controller.pause(0.8, "hold cup for camera")


def return_default(controller):
    controller.say("Returning to default.")
    controller.reset()


def main():
    parser = build_parser(
        "Emotional support cup-grab and drink-pour routine.",
        MODES,
        "do_task",
    )
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Emotional Support")
    if not args.skip_countdown:
        controller.countdown(mode)

    if mode == "do_task":
        do_task(controller)
    elif mode == "default":
        return_default(controller)


if __name__ == "__main__":
    main()


# /*
# Undo/default code:
# def undo_task(controller):
#     controller.reset()
# Run it with:
# python Roboarm_tasks\Emotional_support.py --mode default --driver ble --no-preview
# */
