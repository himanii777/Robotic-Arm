from task_runtime import (
    MotionStep,
    build_parser,
    camera_alignment_preview,
    make_controller,
    resolve_mode,
)


MODES = {
    "fist_bump",
    "handshake",
    "side_dap",
    "finger_point",
    "exploding_fist_bump",
    "combo",
}


def prepare_shot(args):
    camera_alignment_preview(
        args.camera,
        args.width,
        args.height,
        seconds=2.0,
        preview=not args.no_preview,
        label="align hand for handshake shot",
    )


def fist_bump(controller):
    controller.say("Fist bump detected.")
    controller.run(
        [
            MotionStep("make fist", "fist", {"wrist_pitch": 6.0}, 0.45),
            MotionStep("offer fist", targets={"wrist_pitch": -12.0, "yaw": 0.0}, duration=0.5),
            MotionStep("bump forward", targets={"wrist_pitch": -28.0}, duration=0.32, hold=0.18),
            MotionStep("bounce back", targets={"wrist_pitch": -8.0}, duration=0.35),
        ]
    )
    controller.reset()


def handshake(controller):
    controller.say("Never left hanging again.")
    controller.run(
        [
            MotionStep("open handshake", "open_hand", {"wrist_roll": 52.0, "wrist_pitch": -8.0}, 0.55),
            MotionStep("close on hand", "closed_grab", {"wrist_roll": 50.0, "wrist_pitch": -10.0}, 0.45),
        ]
    )
    for pitch in (-24.0, 2.0, -22.0, 0.0):
        controller.move("handshake pump", {"wrist_pitch": pitch, "wrist_roll": 50.0}, 0.32)
    controller.pose("open_hand", "release handshake", {"wrist_roll": 45.0, "wrist_pitch": -4.0}, 0.4)
    controller.reset()


def side_dap(controller):
    controller.say("Side dap mode.")
    controller.pose("open_hand", "side hand ready", {"wrist_roll": 72.0, "wrist_pitch": -6.0}, 0.5)
    controller.move("slide left", {"yaw": -20.0, "wrist_roll": 72.0}, 0.35)
    controller.move("slide right", {"yaw": 18.0, "wrist_roll": 72.0}, 0.35)
    controller.pose("closed_grab", "quick clasp", {"yaw": 10.0, "wrist_roll": 72.0}, 0.35)
    controller.pose("open_hand", "release dap", {"yaw": 0.0, "wrist_roll": 72.0}, 0.35)
    controller.reset()


def finger_point(controller):
    controller.say("Cool kid arm selects you.")
    controller.pose("point", "finger point", {"wrist_pitch": -4.0}, 0.45)
    for angle in (-28.0, 0.0, 28.0, 0.0):
        controller.move("point sweep", {"yaw": angle}, 0.35)
    controller.reset()


def exploding_fist_bump(controller):
    controller.say("Exploding fist bump.")
    controller.pose("fist", "fist ready", {"wrist_pitch": -10.0}, 0.45)
    controller.move("contact", {"wrist_pitch": -30.0}, 0.32, note="film this as the fist bump contact")
    controller.pose("paper", "explode open", {"wrist_pitch": -18.0, "wrist_roll": 0.0}, 0.32)
    for angle in (-22.0, 22.0, -16.0, 16.0, 0.0):
        controller.move("explosion wiggle", {"yaw": angle, "wrist_roll": -angle * 0.8}, 0.22)
    controller.reset()


def combo(controller):
    fist_bump(controller)
    controller.pause(0.8, "next shot")
    handshake(controller)
    controller.pause(0.8, "next shot")
    side_dap(controller)
    controller.pause(0.8, "next shot")
    finger_point(controller)
    controller.pause(0.8, "next shot")
    exploding_fist_bump(controller)


def main():
    parser = build_parser("Handshake and dap demo routines.", MODES, "combo")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    prepare_shot(args)
    controller = make_controller(args, "Handshake")
    if not args.skip_countdown:
        controller.countdown(mode)

    actions = {
        "fist_bump": fist_bump,
        "handshake": handshake,
        "side_dap": side_dap,
        "finger_point": finger_point,
        "exploding_fist_bump": exploding_fist_bump,
        "combo": combo,
    }
    actions[mode](controller)


if __name__ == "__main__":
    main()
