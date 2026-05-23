from task_runtime import (
    MotionStep,
    build_parser,
    make_controller,
    resolve_mode,
    sample_smile_expression,
)


MODES = {"head_pat", "song", "thumbs_up", "comfort", "all"}


def head_pat(controller):
    controller.say("Good Boy! You did well!")
    controller.run(
        [
            MotionStep("soft hand ready", "loose_open", {"wrist_pitch": -12.0}, 0.55),
            MotionStep("hover above head", targets={"wrist_pitch": -22.0, "wrist_roll": 0.0}, duration=0.45),
        ]
    )
    for _ in range(3):
        controller.move("pat down", {"wrist_pitch": -38.0, "wrist_roll": -4.0}, 0.42)
        controller.move("pat lift", {"wrist_pitch": -16.0, "wrist_roll": 4.0}, 0.42)
    controller.say("Seriously. Nice work.")
    controller.pose("thumbs_up", "thumbs up finish", {"wrist_pitch": 18.0}, 0.55)
    controller.pause(0.6, "camera beat")
    controller.reset()


def thumbs_up(controller):
    controller.say("You got this.")
    controller.pose("thumbs_up", "thumbs up", {"wrist_pitch": 20.0, "wrist_roll": 0.0}, 0.55)
    for angle in (-12.0, 12.0, -8.0, 8.0, 0.0):
        controller.move("tiny support wave", {"yaw": angle}, 0.28)
    controller.reset()


def song(controller, args):
    controller.say("Let me check the vibe.")
    try:
        result = sample_smile_expression(
            camera_index=args.camera,
            width=args.width,
            height=args.height,
            seconds=4.0,
            preview=not args.no_preview,
        )
        print(
            "[expression] label={} confidence={:.2f} face_frames={} smile_frames={}".format(
                result.label,
                result.confidence,
                result.face_frames,
                result.smile_frames,
            )
        )
    except RuntimeError as exc:
        print("[expression] {}".format(exc))
        result = None

    label = result.label if result else "unknown"
    if label == "happy":
        controller.say("The smile is back. I am upgrading the soundtrack.")
        tags = ("happy", "fly", "better", "upbeat")
    else:
        controller.say("Do not worry. The emotional support arm is on duty.")
        tags = ("comfort", "sad", "support", "never", "rick")

    controller.pose("thumbs_up", "encouraging thumbs up", {"wrist_pitch": 16.0}, 0.6)
    controller.play_audio(tags)
    controller.pause(1.2, "song reaction")
    for angle in (-16.0, 16.0, -10.0, 10.0, 0.0):
        controller.move("gentle song sway", {"yaw": angle}, 0.35)
    controller.reset()


def comfort(controller, args):
    song(controller, args)
    head_pat(controller)


def main():
    parser = build_parser(
        "Emotional support routines: head pats, expression-based song, and encouragement.",
        MODES,
        "head_pat",
    )
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Emotional Support")
    if not args.skip_countdown:
        controller.countdown(mode)

    if mode == "head_pat":
        head_pat(controller)
    elif mode == "song":
        song(controller, args)
    elif mode == "thumbs_up":
        thumbs_up(controller)
    elif mode == "comfort":
        comfort(controller, args)
    elif mode == "all":
        head_pat(controller)
        song(controller, args)


if __name__ == "__main__":
    main()
