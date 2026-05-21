# Local Hand Tracking Demo

Small webcam hand-tracking test using MediaPipe and OpenCV.

## Setup

```bash
uv sync
```

## Run

```bash
uv run --no-sync python hand_tracking.py
```

If the camera does not open:

```bash
uv run --no-sync python hand_tracking.py --camera 1
```

For faster testing on weaker machines:

```bash
uv run --no-sync python hand_tracking.py --width 640 --height 360 --max-hands 1
```

Press `q` or `Esc` to quit.

## Robot Roll View

`robot_hand_tracking.py` opens a side-by-side isometric robot view. The original
`hand_tracking.py` remains the plain hand-tracking demo.

The control signal intentionally ignores hand translation. Sideways and up/down
hand motion should not move the robot; only palm roll around the current neutral
pose changes the motor command.

Controls while running:

- `c` calibrates the current hand pose as neutral roll
- `r` resets the neutral pose and roll filter
- `q` or `Esc` quits

Useful options:

```bash
uv run --no-sync python robot_hand_tracking.py --roll-limit 45 --roll-smoothing 0.16
```

## Troubleshooting

If MediaPipe fails with `Output tensor range is required`, make sure the
environment is using `mediapipe==0.10.9`:

```bash
uv sync
uv run --no-sync python -c "import mediapipe as mp; print(mp.__version__)"
```
