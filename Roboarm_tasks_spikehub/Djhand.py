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

# DJ only needs wrist and yaw.
MOTOR_PORTS = {
    "yaw": "A",
    "wrist": "B",
}

MOTOR_SPEED = {
    "wrist": 20,
    "yaw": 30,
}

SAFE_LIMITS = {
    "wrist": (PALM_DOWN_WRIST, PALM_UP_WRIST),
    "yaw": (-180, 180),
}

CURRENT = {
    "wrist": DEFAULT_WRIST,
    "yaw": 0,
}
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


def correct_wrist_default():
    wrist = MOTORS["wrist"]
    wrist.run_to_degrees_counted(DEFAULT_WRIST, MOTOR_SPEED["wrist"])
    wait_for_seconds(0.2)
    wrist.run_to_position(WRIST_ABSOLUTE_DEFAULT, MOTOR_SPEED["wrist"])
    wrist.set_degrees_counted(DEFAULT_WRIST)
    CURRENT["wrist"] = DEFAULT_WRIST


def return_default():
    move_to({"wrist": DEFAULT_WRIST, "yaw": 0}, 0.75)
    correct_wrist_default()


def stop_all():
    for motor in MOTORS.values():
        motor.stop()


def do_task():
    hub.light_matrix.show_image("HAPPY")

    move_to({"wrist": PALM_DOWN_WRIST, "yaw": 0}, 0.7)

    for _ in range(4):
        move_to({"yaw": -26, "wrist": -150}, 0.24)
        move_to({"yaw": 26, "wrist": PALM_DOWN_WRIST}, 0.24)

    move_to({"yaw": 28, "wrist": -143}, 0.28)
    move_to({"yaw": 28, "wrist": PALM_DOWN_WRIST}, 0.22)
    move_to({"yaw": 0, "wrist": -136}, 0.32)

    for angle in (-24, 24, -18, 18, 0):
        move_to({"yaw": angle, "wrist": -128}, 0.25)

    wait_for_seconds(0.7)


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
