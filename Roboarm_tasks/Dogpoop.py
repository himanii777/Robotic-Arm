from task_runtime import build_parser, make_controller, resolve_mode


MODES = {"do_task", "default"}


def do_task(controller):
    controller.say("Plastic barrier ready.")
    controller.pose("default", "open palm with plastic", duration=0.55)
    controller.pause(1.4, "dog poop lands on plastic")
    controller.say("Containment mode.")
    controller.pose("pinky_closed", "pinky closes plastic edge", {"wrist": 0.0}, 0.6)
    controller.pose("half_close", "semi close around poop", {"wrist": 0.0}, 0.75)

    for angle in (-18.0, 18.0, -10.0, 10.0, 0.0):
        controller.move("sealed bag yaw motion", {"yaw": angle, "wrist": 4.0}, 0.32)

    controller.pose("cup_grip", "secure plastic bundle", {"yaw": 0.0, "wrist": 8.0}, 0.6)
    controller.pause(0.9, "hold wrapped poop for camera")


def return_default(controller):
    controller.say("Returning to default.")
    controller.reset()


def main():
    parser = build_parser("Dog poop staged plastic-grab routine.", MODES, "do_task")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Dogpoop")
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
# python Roboarm_tasks\Dogpoop.py --mode default --driver ble --no-preview
# */
