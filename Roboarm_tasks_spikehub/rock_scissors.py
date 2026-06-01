from spike import PrimeHub, Motor
from spike.control import wait_for_seconds
from math import *


hub = PrimeHub()

# Change this to "rock", "paper", or "scissors" before running.
ROBOT_MOVE = "scissors"

# Wrist calibration from the demo:
#   degrees counted 0    = neutral/default, palm facing sideward
#   degrees counted -165 = palm facing downward
#   degrees counted 90   = palm facing upward
#   absolute position 260 = neutral correction at the end
DEFAULT_WRIST = 0
PALM_DOWN_WRIST = -165
PALM_UP_WRIST = 90
WRIST_ABSOLUTE_DEFAULT = 260

FULL_CLOSE = {
    "thumb": 240,
    "index": 520,
    "middle": 700,
    "ring": 540,
    "pinky": -240,
}

# This follows your wrist calibration demo: wrist motor on port B.
# Change only these letters if the final wiring is different.
MOTOR_PORTS = {
    "thumb": "A",
    "wrist": "B",
    "index": "C",
    "ring": "D",
    "pinky": "E",
    "middle": "F",
}

MOTOR_SPEED = {
    "thumb": 40,
    "index": 40,
    "middle": 40,
    "ring": 40,
    "pinky": 40,
    "wrist": 20,
}

SAFE_LIMITS = {
    "thumb": (-20, 270),
    "index": (-20, 570),
    "middle": (-20, 750),
    "ring": (-20, 590),
    "pinky": (-270, 20),
    "wrist": (PALM_DOWN_WRIST, PALM_UP_WRIST),
}

POSES = {
    "default": {
        "thumb": 0,
        "index": 0,
        "middle": 0,
        "ring": 0,
        "pinky": 0,
        "wrist": DEFAULT_WRIST,
    },
    "rock": {
        "thumb": FULL_CLOSE["thumb"],
        "index": FULL_CLOSE["index"],
        "middle": FULL_CLOSE["middle"],
        "ring": FULL_CLOSE["ring"],
        "pinky": FULL_CLOSE["pinky"],
        "wrist": DEFAULT_WRIST,
    },
    "paper": {
        "thumb": 0,
        "index": 0,
        "middle": 0,
        "ring": 0,
        "pinky": 0,
        "wrist": DEFAULT_WRIST,
    },
    "scissors": {
        "thumb": FULL_CLOSE["thumb"],
        "index": 0,
        "middle": 0,
        "ring": FULL_CLOSE["ring"],
        "pinky": FULL_CLOSE["pinky"],
        "wrist": DEFAULT_WRIST,
    },
}

CURRENT = dict(POSES["default"])
MOTORS = {}


def clamp(value, low, high):
    return max(low, min(high, value))


def setup_motors():
    for name, port_name in MOTOR_PORTS.items():
        motor = Motor(port_name)
        motor.set_stop_action("hold")
        motor.set_degrees_counted(0)
        MOTORS[name] = motor


def move_to(targets, duration=0.45):
    for name, value in targets.items():
        low, high = SAFE_LIMITS[name]
        target = clamp(float(value), low, high)
        MOTORS[name].run_to_degrees_counted(int(target), MOTOR_SPEED[name])
        CURRENT[name] = target
    wait_for_seconds(duration)


def pose(name, duration=0.45):
    move_to(dict(POSES[name]), duration)


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


def countdown():
    for _ in range(4):
        wait_for_seconds(0.32)


def robot_show(move):
    if move not in POSES:
        move = "scissors"
    pose(move, duration=0.75)


def do_task():
    hub.light_matrix.show_image("HAPPY")
    pose("default", duration=0.5)
    countdown()
    robot_show(ROBOT_MOVE)
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
