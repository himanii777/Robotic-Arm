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

## Troubleshooting

If MediaPipe fails with `Output tensor range is required`, make sure the
environment is using `mediapipe==0.10.9`:

```bash
uv sync
uv run --no-sync python -c "import mediapipe as mp; print(mp.__version__)"
```
