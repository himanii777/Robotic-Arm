from task_runtime import (
    build_parser,
    camera_alignment_preview,
    clamp,
    make_controller,
    resolve_mode,
)


MODES = {"scratch", "left", "right", "interactive", "demo"}


def scratch_at(controller, yaw=0.0, cycles=5):
    controller.pose("closed_grab", "scratch fingers ready", {"yaw": yaw, "wrist_roll": 0.0}, 0.45)
    for _ in range(cycles):
        controller.move("scratch down", {"yaw": yaw, "wrist_pitch": -30.0}, 0.22)
        controller.move("scratch up", {"yaw": yaw, "wrist_pitch": 4.0}, 0.22)


def left(controller):
    controller.say("More left.")
    scratch_at(controller, yaw=-30.0, cycles=4)
    controller.reset()


def right(controller):
    controller.say("More right.")
    scratch_at(controller, yaw=30.0, cycles=4)
    controller.reset()


def scratch(controller):
    controller.say("Back scratch bot engaged.")
    scratch_at(controller, yaw=0.0, cycles=6)
    controller.reset()


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
        scratch_at(controller, yaw=yaw, cycles=3)
    controller.reset()


def demo(controller):
    scratch(controller)
    controller.pause(0.6, "user says more left")
    left(controller)
    controller.pause(0.6, "user says more right")
    right(controller)


def main():
    parser = build_parser("Back scratcher demo routines.", MODES, "interactive")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    camera_alignment_preview(
        args.camera,
        args.width,
        args.height,
        seconds=2.0,
        preview=not args.no_preview,
        label="align back scratch shot",
    )
    controller = make_controller(args, "Scratcher")
    if not args.skip_countdown:
        controller.countdown(mode)

    actions = {
        "scratch": scratch,
        "left": left,
        "right": right,
        "interactive": interactive,
        "demo": demo,
    }
    actions[mode](controller)


if __name__ == "__main__":
    main()
