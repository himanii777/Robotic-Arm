# Roboarm Task Scripts

These scripts can run in two motor modes:

- `--driver console` prints the motor timeline for rehearsal and calibration. This is the default.
- `--driver ble` sends the same timeline to a SPIKE Prime hub running Pybricks.

## What Codex Can Set Up In The Repo

The repo includes:

- `task_runtime.py`: shared task runner, poses, camera helpers, speech/audio helpers.
- `spike_ble_bridge.py`: laptop-side BLE sender using `bleak`.
- `hub_pybricks_receiver.py`: hub-side Pybricks program that receives motor targets.
- `songs/`: place `.mp3` or `.wav` files here for emotional support and DJ modes.

The Python dependency is listed in `requirements.txt` and `pyproject.toml`:

```powershell
python -m pip install -r requirements.txt
```

## What Must Be Done Manually

Pybricks firmware must be installed on the physical hub through Pybricks Code:

1. Open `https://code.pybricks.com`.
2. Connect the SPIKE Prime hub.
3. Install Pybricks firmware.
4. Open `Roboarm_tasks/hub_pybricks_receiver.py` in Pybricks Code.
5. Adjust `MOTOR_PORTS` to match your real wiring.
6. Run/download the program, then disconnect Pybricks Code.
7. Start the hub program with the hub button.

Then run a laptop task with BLE:

```powershell
python Roboarm_tasks\Handshake.py --mode fist-bump --driver ble
```

If the hub name is different:

```powershell
python Roboarm_tasks\Handshake.py --mode fist-bump --driver ble --hub-name "Your Hub Name"
```

## Port Limit Warning

One SPIKE Prime hub has six motor ports. The default receiver maps:

- Port A: thumb
- Port B: index
- Port C: middle
- Port D: ring
- Port E: pinky
- Port F: yaw

Your full design mentions five finger motors plus yaw plus wrist pitch/roll, which is eight motors if all are independent. For all eight, use two hubs or mechanically link some axes.
