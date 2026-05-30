from task_runtime import build_parser, make_controller, resolve_mode


MODES = {"do_task", "default"}


def grip_water_cup(controller):
    controller.pose("default", "open palm upward", duration=0.55)
    controller.pause(0.8, "place water cup")
    controller.pose("pinky_closed", "pinky locks cup first", {"wrist": 0.0}, 0.65)
    controller.pose("cup_grip", "half close water grip", {"wrist": 0.0}, 0.85)


def pour_plant_water(controller):
    controller.say("Dryness detected.")
    controller.move("aim over plant", {"yaw": 0.0, "wrist": 0.0}, 0.45)
    controller.move("tilt cup to pour", {"wrist": 76.0}, 1.0)
    controller.pause(1.6, "water flow")
    controller.move("cup upright", {"wrist": 0.0}, 0.75)
    controller.move("tiny shake", {"wrist": 12.0}, 0.22)
    controller.move("steady cup", {"wrist": 0.0}, 0.25)


def do_task(controller):
    controller.say("Water GPT plant rescue mode.")
    grip_water_cup(controller)
    pour_plant_water(controller)
    controller.pause(0.8, "hold watering finish")


def return_default(controller):
    controller.say("Returning to default.")
    controller.reset()


def main():
    parser = build_parser("Plant watering cup-grab and pour routine.", MODES, "do_task")
    args = parser.parse_args()
    mode = resolve_mode(args, MODES)
    controller = make_controller(args, "Watering")
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
# python Roboarm_tasks\Watering.py --mode default --driver ble --no-preview
# */
