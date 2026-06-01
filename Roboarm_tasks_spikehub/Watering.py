from spike import PrimeHub, Motor
from spike.control import wait_for_seconds
from math import *


hub = PrimeHub()

# Wrist calibration from the demo:
#   degrees counted 0    = neutral/default, palm facing sideward
#   degrees counted -165 = palm facing downward
#   degrees counted 90   = palm facing upward
#   absolute position 260 = neutral correction at the end
DEFAULT_WRIST = 0
PALM_DOWN_WRIST = -165
PALM_UP_WRIST = 90
WRIST_ABSOLUTE_DEFAULT = 260
POUR_WRIST = -73
SHAKE_WRIST = -51

FULL_CLOSE = {
    "thumb": 240,
    "index": 520,
    "middle": 700,
    "ring": 540,
    "pinky": -240,
}

CUP_GRIP = {
    "thumb": 120,
    "index": 260,
    "middle": 350,
    "ring": 270,
    "pinky": -240,
}

MOTOR_PORTS = {
    "thumb": "A",
    "wrist": "B",
    "index": "C",
    "ring": "D",
    "pinky": "E",
    "middle": "F",
    # Set this to a port on a separate yaw hub copy if needed.
    "yaw": None,
}

MOTOR_SPEED = {
    "thumb": 40,
    "index": 40,
    "middle": 40,
    "ring": 40,
    "pinky": 40,
    "wrist": 20,
    "yaw": 30,
}

SAFE_LIMITS = {
    "thumb": (-20, 270),
    "index": (-20, 570),
    "middle": (-20, 750),
    "ring": (-20, 590),
    "pinky": (-270, 20),
    "wrist": (PALM_DOWN_WRIST, PALM_UP_WRIST),
    "yaw": (-180, 180),
}

POSES = {
    "default": {
        "thumb": 0,
        "index": 0,
        "middle": 0,
        "ring": 0,
        "pinky": 0,
        "wrist": DEFAULT_WRIST,
        "yaw": 0,
    },
    "pinky_closed": {
        "thumb": 0,
        "index": 0,
        "middle": 0,
        "ring": 0,
        "pinky": FULL_CLOSE["pinky"],
    },
    "cup_grip": CUP_GRIP,
}

CURRENT = dict(POSES["default"])
MOTORS = {}


def clamp(value, low, high):
    return max(low, min(high, value))


def setup_motors():
    for name, port_name in MOTOR_PORTS.items():
        if port_name is not None:
            motor = Motor(port_name)
            motor.set_stop_action("hold")
            motor.set_degrees_counted(0)
            MOTORS[name] = motor


def move_to(targets, duration=0.45):
    for name, value in targets.items():
        low, high = SAFE_LIMITS[name]
        target = clamp(float(value), low, high)
        if name in MOTORS:
            MOTORS[name].run_to_degrees_counted(int(target), MOTOR_SPEED[name])
        CURRENT[name] = target
    wait_for_seconds(duration)


def pose(name, overrides=None, duration=0.45):
    targets = dict(POSES[name])
    if overrides:
        targets.update(overrides)
    move_to(targets, duration)


def correct_wrist_default():
    wrist = MOTORS["wrist"]
    wrist.run_to_degrees_counted(DEFAULT_WRIST, MOTOR_SPEED["wrist"])
    wait_for_seconds(0.2)
    wrist.run_to_position(WRIST_ABSOLUTE_DEFAULT, MOTOR_SPEED["wrist"])
    wrist.set_degrees_counted(DEFAULT_WRIST)
    CURRENT["wrist"] = DEFAULT_WRIST


def return_default():
    pose("default", duration=0.85)
    correct_wrist_default()


def stop_all():
    for motor in MOTORS.values():
        motor.stop()


def grip_water_cup():
    pose("default", duration=0.55)
    wait_for_seconds(0.8)
    pose("pinky_closed", {"wrist": DEFAULT_WRIST}, 0.65)
    pose("cup_grip", {"wrist": DEFAULT_WRIST}, 0.85)


def pour_plant_water():
    move_to({"yaw": 0, "wrist": DEFAULT_WRIST}, 0.45)
    move_to({"wrist": POUR_WRIST}, 1.0)
    wait_for_seconds(1.6)
    move_to({"wrist": DEFAULT_WRIST}, 0.75)
    move_to({"wrist": SHAKE_WRIST}, 0.22)
    move_to({"wrist": DEFAULT_WRIST}, 0.25)


def do_task():
    hub.light_matrix.show_image("HAPPY")
    grip_water_cup()
    pour_plant_water()
    wait_for_seconds(0.8)


setup_motors()
do_task()
return_default()
stop_all()


# Undo/default-only code:
# Comment out do_task() above and use only this if you want to undo the task:
#
# setup_motors()
# return_default()
# stop_all()
