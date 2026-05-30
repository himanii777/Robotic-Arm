from task_runtime import build_parser, clamp, make_controller, resolve_mode


MODES = {"do_task", "default", "interactive"}


def scratch_motion(controller, center_yaw=0.0, cycles=6):
    center_yaw = clamp(center_yaw, -55.0, 55.0)
    controller.pose("half_close", "scratch fingers ready", {"wrist": 90.0, "yaw": center_yaw}, 0.75)
    for _ in range(cycles):
        controller.move("scratch yaw left", {"yaw": clamp(center_yaw - 18.0, -70.0, 70.0), "wrist": 90.0}, 0.24)
        controller.move("scratch yaw right", {"yaw": clamp(center_yaw + 18.0, -70.0, 70.0), "wrist": 90.0}, 0.24)
    controller.move("center scratch", {"yaw": center_yaw, "wrist": 90.0}, 0.28)


def do_task(controller):
    controller.say("Back scratch bot engaged.")
    scratch_motion(controller, center_yaw=0.0, cycles=7)
    controller.pause(0.7, "hold scratch position")


def interactive(controller):
    controller.say("Back scratch bot ready. Type left, right, scratch, center, or done.")
    yaw = 0.0
    while True:
        command = input("scratcher command [scratch/left/right/center/done]: ").strip().lower()
        if command in ("done", "stop", "q", "quit"):
            break
        if command in ("left", "more left"):
            yaw = clamp(yaw - 18.0, -55.0, 55.0)
            controller.say("Moving left.")
        elif command in ("right", "more right"):
            yaw = clamp(yaw + 18.0, -55.0, 55.0)
            controller.say("Moving right.")
        elif command == "center":
            yaw = 0.0
            controller.say("Centering.")
        elif command not in ("", "scratch"):
            print("Commands: scratch, left, right, center, done")
            continue
        scratch_motion(controller, center_yaw=yaw, cycles=3)


def return_default(controller):
    controller.say("Returning to default.")
    controller.reset()


def main():
    parser = build_parser("Wrist-rotated yaw scratcher routine.", MODES, "do_task")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Scratcher")
    if not args.skip_countdown:
        controller.countdown(mode)

    if mode == "do_task":
        do_task(controller)
    elif mode == "interactive":
        interactive(controller)
    elif mode == "default":
        return_default(controller)


if __name__ == "__main__":
    main()


# /*
# Undo/default code:
# def undo_task(controller):
#     controller.reset()
# Run it with:
# python Roboarm_tasks\Scratcher.py --mode default --driver ble --no-preview
# */
