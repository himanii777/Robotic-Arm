from spike import PrimeHub, Motor
from spike.control import wait_for_seconds


hub = PrimeHub()

# ROBOT_MOVE = "scissors"
ROBOT_MOVE = "rock"

FULL_CLOSE = {
    "thumb": -650,
    "index": 520,
    "middle": 700,
    "ring": 540,
    "pinky": -240,
}

MOTOR_PORTS = {
    "thumb": "B",
    "index": "F",
    "ring": "C",
    "pinky": "A",
    "middle": "E",
}

MOTOR_SPEED = {
    "thumb": 50,
    "index": 50,
    "middle": 50,
    "ring": 50,
    "pinky": 50,
}

SAFE_LIMITS = {
    "thumb": (-700, 20),
    "index": (-20, 570),
    "middle": (-20, 750),
    "ring": (-20, 590),
    "pinky": (-270, 20),
}

DEFAULT_POSE = {
    "thumb": 0,
    "index": 0,
    "middle": 0,
    "ring": 0,
    "pinky": 0,
}

ROCK_CLOSE = {
    "thumb": FULL_CLOSE["thumb"],
    "index": FULL_CLOSE["index"],
    "middle": FULL_CLOSE["middle"],
    "ring": FULL_CLOSE["ring"],
    "pinky": FULL_CLOSE["pinky"],
}

SCISSORS_CLOSE = {
    "thumb": FULL_CLOSE["thumb"],
    "index": 0,
    "middle": 0,
    "ring": FULL_CLOSE["ring"],
    "pinky": FULL_CLOSE["pinky"],
}

MOTORS = {}


def clamp(value, low, high):
    return max(low, min(high, value))


def setup_motors():
    for name, port_name in MOTOR_PORTS.items():
        m = Motor(port_name)
        m.set_stop_action("hold")

        # Start with the hand physically open.
        # This marks open/default as 0.
        m.set_degrees_counted(0)

        MOTORS[name] = m


def move_to_all_at_once(targets, duration=2.0):
    active = {}

    for name, value in targets.items():
        low, high = SAFE_LIMITS[name]
        target = clamp(value, low, high)

        current = MOTORS[name].get_degrees_counted()
        difference = target - current

        if abs(difference) > 5:
            speed = MOTOR_SPEED[name]

            if difference < 0:
                speed = -speed

            MOTORS[name].start(speed)
            active[name] = target

    timer = 0

    while len(active) > 0 and timer < duration:
        finished = []

        for name in active:
            target = active[name]
            current = MOTORS[name].get_degrees_counted()

            if target >= 0:
                if current >= target:
                    MOTORS[name].stop()
                    finished.append(name)
            else:
                if current <= target:
                    MOTORS[name].stop()
                    finished.append(name)

        for name in finished:
            del active[name]

        wait_for_seconds(0.02)
        timer = timer + 0.02

    for name in active:
        MOTORS[name].stop()

    wait_for_seconds(0.1)


def move_to_one_at_a_time(targets, duration=0.45):
    for name, value in targets.items():
        low, high = SAFE_LIMITS[name]
        target = clamp(value, low, high)

        MOTORS[name].run_to_degrees_counted(
            int(target),
            MOTOR_SPEED[name]
        )

    wait_for_seconds(duration)


def return_default():
    move_to_one_at_a_time(DEFAULT_POSE, duration=0.85)


def rock():
    move_to_all_at_once(ROCK_CLOSE, duration=3.0)


def scissors():
    move_to_all_at_once(SCISSORS_CLOSE, duration=3.0)


def countdown():
    for _ in range(4):
        wait_for_seconds(0.32)


def stop_all():
    for m in MOTORS.values():
        m.stop()


def robot_show(move):
    if move == "rock":
        rock()
    elif move == "scissors":
        scissors()
    else:
        scissors()


def main():
    hub.light_matrix.show_image("HAPPY")

    countdown()

    robot_show(ROBOT_MOVE)

    wait_for_seconds(5)

    return_default()
    stop_all()


setup_motors()
main()