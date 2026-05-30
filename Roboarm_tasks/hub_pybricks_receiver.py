"""
Pybricks receiver for the LEGO SPIKE Prime hub.

Load this file onto the hub with https://code.pybricks.com, disconnect Pybricks
Code, start the program with the hub button, then run a task script with:

    python Roboarm_tasks/Handshake.py --mode fist-bump --driver ble

This default mapping matches the calibrated build:

- wrist: Port A
- thumb: Port B
- index: Port C
- ring: Port D
- pinky: Port E
- middle: Port F

That uses all six SPIKE Prime ports. Yaw commands are still accepted from the
laptop timeline, but this receiver ignores them unless you add a second hub or
remap one port to yaw.
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop
from pybricks.tools import wait

from usys import stdin, stdout
from uselect import poll


hub = PrimeHub()

MOTOR_PORTS = {
    "wrist": Port.A,
    "thumb": Port.B,
    "index": Port.C,
    "ring": Port.D,
    "pinky": Port.E,
    "middle": Port.F,
    # "yaw": Port.A,  # Use this on a second hub/box if yaw has its own hub.
}

MOTOR_ORDER = (
    "thumb",
    "index",
    "middle",
    "ring",
    "pinky",
    "wrist",
    "yaw",
)

MOTOR_SPEED = {
    "thumb": 500,
    "index": 500,
    "middle": 500,
    "ring": 500,
    "pinky": 500,
    "wrist": 240,
    "yaw": 260,
}

motors = {}
for name, port in MOTOR_PORTS.items():
    motor = Motor(port)
    motor.reset_angle(0)
    motors[name] = motor

keyboard = poll()
keyboard.register(stdin)


def read_line():
    data = b""
    while True:
        while not keyboard.poll(0):
            wait(5)
        char = stdin.buffer.read(1)
        if char in (b"\n", b"\r"):
            if data:
                return data
        elif char:
            data += char


def write_status(text):
    stdout.buffer.write(text.encode("utf-8"))


def stop_all():
    for motor in motors.values():
        motor.stop()


def handle_motion(parts):
    if len(parts) < 2 + len(MOTOR_ORDER):
        write_status("ERR short\n")
        return

    # parts[0] is "M"; parts[1] is the laptop wait duration in ms.
    targets = {}
    for name, value in zip(MOTOR_ORDER, parts[2:]):
        targets[name] = float(value)

    for name, motor in motors.items():
        motor.run_target(
            MOTOR_SPEED.get(name, 300),
            targets.get(name, 0.0),
            then=Stop.HOLD,
            wait=False,
        )
    write_status("OK\n")


write_status("receiver ready\n")
while True:
    stdout.buffer.write(b"rdy")
    line = read_line()
    try:
        parts = line.decode("ascii").strip().split(",")
        command = parts[0]
        if command == "M":
            handle_motion(parts)
        elif command == "STOP":
            stop_all()
            write_status("STOPPED\n")
        elif command == "BYE":
            stop_all()
            write_status("BYE\n")
            break
        else:
            stop_all()
            write_status("ERR unknown\n")
    except Exception as exc:
        stop_all()
        write_status("ERR {}\n".format(exc))
