from task_runtime import build_parser, make_controller, resolve_mode


MODES = {"do_task", "default"}


def do_task(controller):
    controller.say("Palm up handshake. No awkward handshakes today.")
    controller.pose("default", "open palm upward", duration=0.5)
    controller.pause(0.5, "person reaches in")
    controller.pose("half_close", "soft handshake grip", {"wrist": 6.0}, 0.65)

    for angle in (-18.0, 18.0, -14.0, 14.0, 0.0):
        controller.move("palm-up shake", {"yaw": angle, "wrist": 8.0}, 0.32)

    controller.pose("open_hand", "release hand", {"yaw": 0.0, "wrist": 0.0}, 0.45)
    controller.pose("thumbs_up", "friendly thumbs up", {"wrist": 18.0}, 0.55)
    for angle in (-12.0, 12.0, 0.0):
        controller.move("small celebration", {"yaw": angle}, 0.28)
    controller.pause(0.8, "hold friendly finish")


def return_default(controller):
    controller.say("Returning to default.")
    controller.reset()


def main():
    parser = build_parser("Palm-up handshake routine.", MODES, "do_task")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Handshake")
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
# python Roboarm_tasks\Handshake.py --mode default --driver ble --no-preview
# */
