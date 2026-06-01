from spike import PrimeHub, Motor
from spike.control import wait_for_seconds


hub = PrimeHub()

# Motors
# Rotation / wrist = D
# Yaw = F
wrist = Motor("D")
yaw = Motor("F")

# Calibration
DEFAULT_WRIST = 0
PALM_DOWN_WRIST = -165

# DJ yaw motion
YAW_DEGREE = 28
DJ_REPEAT = 15

# Speeds
WRIST_SPEED = 20
YAW_SPEED = 100


def setup_motors():
    # Start robot physically in default position before running.
    wrist.set_stop_action("hold")
    yaw.set_stop_action("hold")

    wrist.set_degrees_counted(0)
    yaw.set_degrees_counted(0)


def face_downward():
    wrist.run_for_degrees(
        abs(PALM_DOWN_WRIST),
        speed=-WRIST_SPEED
    )


def dj_yaw_back_and_forth():
    # Start by moving to one side
    yaw.run_for_degrees(
        YAW_DEGREE,
        speed=YAW_SPEED
    )

    # Then swing between +YAW_DEGREE and -YAW_DEGREE
    for _ in range(DJ_REPEAT):
        yaw.run_for_degrees(
            YAW_DEGREE * 2,
            speed=-YAW_SPEED
        )

        yaw.run_for_degrees(
            YAW_DEGREE * 2,
            speed=YAW_SPEED
        )

    # Return to center
    yaw.run_for_degrees(
        YAW_DEGREE,
        speed=-YAW_SPEED
    )


def return_default():
    # Return wrist back up/default
    wrist.run_for_degrees(
        abs(PALM_DOWN_WRIST),
        speed=WRIST_SPEED
    )


def stop_all():
    wrist.stop()
    yaw.stop()


def main():
    hub.light_matrix.write("DJ")

    setup_motors()

    face_downward()
    dj_yaw_back_and_forth()

    wait_for_seconds(0.1)

    return_default()
    stop_all()

    hub.light_matrix.write("OK")


main()