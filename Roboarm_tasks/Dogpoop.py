from task_runtime import (
    build_parser,
    clamp,
    find_dark_brown_blob,
    make_controller,
    resolve_mode,
)


MODES = {"scan", "bag_wrap", "pickup", "scan_pick", "demo"}


def scan(controller, args):
    controller.say("Scanning the danger zone.")
    controller.pose("open_hand", "open bag fingers", {"wrist_pitch": 8.0}, 0.45)
    for angle in (-35.0, 0.0, 35.0, 0.0):
        controller.move("visual scan sweep", {"yaw": angle}, 0.35)

    try:
        blob = find_dark_brown_blob(
            camera_index=args.camera,
            width=args.width,
            height=args.height,
            seconds=4.0,
            preview=not args.no_preview,
        )
    except RuntimeError as exc:
        print("[scan] {}".format(exc))
        blob = None

    if blob and blob.found:
        yaw = clamp(blob.x_offset * 48.0, -45.0, 45.0)
        print(
            "[scan] target found x_offset={:.2f} y_offset={:.2f} area={:.4f} yaw={:+.1f}".format(
                blob.x_offset,
                blob.y_offset,
                blob.area_ratio,
                yaw,
            )
        )
        controller.say("Target acquired.")
        controller.move("aim at target", {"yaw": yaw}, 0.45)
        return yaw

    print("[scan] no confident target; using center pickup path")
    controller.say("No confident camera lock. Using center pickup path.")
    return 0.0


def bag_wrap(controller, yaw=0.0):
    controller.say("Bag wrap ready.")
    controller.pose("open_hand", "spread bag open", {"yaw": yaw, "wrist_pitch": -4.0}, 0.45)
    controller.move("lower bag", {"wrist_pitch": -28.0, "wrist_roll": 6.0}, 0.45)
    controller.pose("closed_grab", "cinch plastic", {"yaw": yaw, "wrist_pitch": -30.0}, 0.45)
    controller.pose("open_hand", "reset bag mouth", {"yaw": yaw, "wrist_pitch": -18.0}, 0.3)
    controller.pose("closed_grab", "final bag pinch", {"yaw": yaw, "wrist_pitch": -28.0}, 0.35)


def pickup(controller, yaw=0.0):
    controller.say("Picking it up. Brave work from the robot.")
    controller.pose("open_hand", "approach open", {"yaw": yaw, "wrist_pitch": -8.0}, 0.5)
    controller.move("lower around target", {"yaw": yaw, "wrist_pitch": -42.0, "wrist_roll": 0.0}, 0.65)
    controller.pose("closed_grab", "grab through bag", {"yaw": yaw, "wrist_pitch": -38.0}, 0.65)
    controller.move("lift sealed bag", {"wrist_pitch": 20.0, "wrist_roll": 0.0}, 0.65)
    controller.move("carry to disposal side", {"yaw": 55.0, "wrist_pitch": 16.0}, 0.75)
    controller.pose("open_hand", "release into bin", {"yaw": 55.0, "wrist_pitch": -8.0}, 0.45)
    controller.reset()


def scan_pick(controller, args):
    yaw = scan(controller, args)
    bag_wrap(controller, yaw)
    pickup(controller, yaw)


def main():
    parser = build_parser("Dog poop pickup demo routines.", MODES, "scan_pick")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Dogpoop")
    if not args.skip_countdown:
        controller.countdown(mode)

    if mode == "scan":
        scan(controller, args)
    elif mode == "bag_wrap":
        bag_wrap(controller)
    elif mode == "pickup":
        pickup(controller)
    elif mode in ("scan_pick", "demo"):
        scan_pick(controller, args)


if __name__ == "__main__":
    main()
