from task_runtime import (
    build_parser,
    make_controller,
    resolve_mode,
    sample_soil_dryness,
)


MODES = {"check", "pour", "check_pour", "demo"}


def check_soil(controller, args):
    controller.say("Checking soil color.")
    try:
        result = sample_soil_dryness(
            camera_index=args.camera,
            width=args.width,
            height=args.height,
            seconds=3.5,
            preview=not args.no_preview,
        )
    except RuntimeError as exc:
        print("[soil] {}".format(exc))
        result = None

    if result is None:
        controller.say("Camera check failed. Treating this as dry if a pour sequence follows.")
        return True

    print(
        "[soil] dry={} score={:.2f} mean_hsv=({:.1f}, {:.1f}, {:.1f})".format(
            result.is_dry,
            result.dry_score,
            result.mean_hsv[0],
            result.mean_hsv[1],
            result.mean_hsv[2],
        )
    )
    if result.is_dry:
        controller.say("Soil looks dry. Water GPT will help.")
    else:
        controller.say("Soil looks moist enough. No dramatic plant rescue needed.")
    return result.is_dry


def pour(controller):
    controller.say("Watering sequence.")
    controller.pose("closed_grab", "hold water container", {"wrist_pitch": 8.0, "wrist_roll": 0.0}, 0.5)
    controller.move("aim over plant", {"yaw": 0.0, "wrist_pitch": 12.0, "wrist_roll": 0.0}, 0.55)
    controller.move("tilt to pour", {"wrist_roll": 64.0, "wrist_pitch": -4.0}, 0.85)
    controller.pause(1.7, "water flow")
    controller.move("stop pour", {"wrist_roll": 0.0, "wrist_pitch": 10.0}, 0.65)
    controller.move("small shake off", {"wrist_roll": 12.0}, 0.22)
    controller.move("container upright", {"wrist_roll": 0.0}, 0.22)
    controller.reset()


def check_pour(controller, args):
    if check_soil(controller, args):
        pour(controller)
    else:
        controller.pose("thumbs_up", "plant is fine", {"wrist_pitch": 18.0}, 0.45)
        controller.reset()


def main():
    parser = build_parser("Plant watering demo routines.", MODES, "check_pour")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Watering")
    if not args.skip_countdown:
        controller.countdown(mode)

    if mode == "check":
        check_soil(controller, args)
    elif mode == "pour":
        pour(controller)
    elif mode in ("check_pour", "demo"):
        check_pour(controller, args)


if __name__ == "__main__":
    main()
