import asyncio
import queue
import threading
from dataclasses import dataclass


PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"
MOTOR_ORDER = (
    "thumb",
    "index",
    "middle",
    "ring",
    "pinky",
    "wrist",
    "yaw",
)


@dataclass
class _PendingSend:
    payload: bytes
    done: threading.Event
    error: list


class SpikeBleBridge:
    """Synchronous wrapper around the Pybricks BLE stdin/stdout protocol."""

    def __init__(self, hub_name="Pybricks Hub", timeout=15.0):
        self.hub_name = hub_name
        self.timeout = float(timeout)
        self._queue = queue.Queue()
        self._connected = threading.Event()
        self._stopped = threading.Event()
        self._startup_error = []
        self._thread = threading.Thread(target=self._thread_main, daemon=True)

    def start(self):
        self._thread.start()
        if not self._connected.wait(self.timeout):
            if self._startup_error:
                raise RuntimeError(self._startup_error[0])
            raise RuntimeError(
                "Timed out while connecting to hub '{}'. Make sure Pybricks Code is "
                "disconnected and the hub is advertising.".format(self.hub_name)
            )

    def send_motion(self, state, duration):
        values = [state.get(name, 0.0) for name in MOTOR_ORDER]
        payload = "M,{:d},{}\n".format(
            int(max(0.0, duration) * 1000),
            ",".join("{:.1f}".format(value) for value in values),
        ).encode("ascii")
        self._send(payload)

    def stop(self):
        if self._stopped.is_set():
            return
        self._stopped.set()
        self._send(b"STOP\n", timeout=2.0, raise_on_error=False)
        self._queue.put(None)

    def _send(self, payload, timeout=None, raise_on_error=True):
        timeout = self.timeout if timeout is None else timeout
        pending = _PendingSend(payload=payload, done=threading.Event(), error=[])
        self._queue.put(pending)
        if not pending.done.wait(timeout):
            message = "Timed out waiting for hub to accept command."
            if raise_on_error:
                raise RuntimeError(message)
            return False
        if pending.error:
            if raise_on_error:
                raise RuntimeError(pending.error[0])
            return False
        return True

    def _thread_main(self):
        try:
            asyncio.run(self._run())
        except Exception as exc:
            self._startup_error.append(str(exc))
            self._connected.set()

    async def _run(self):
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError as exc:
            raise RuntimeError(
                "The BLE driver needs bleak. Install with: pip install bleak"
            ) from exc

        main_task = asyncio.current_task()
        ready_event = asyncio.Event()

        def handle_disconnect(_):
            if main_task and not main_task.done():
                main_task.cancel()

        def handle_rx(_, data):
            if not data:
                return
            if data[0] != 0x01:
                return
            payload = bytes(data[1:])
            if payload == b"rdy":
                ready_event.set()
            elif payload:
                try:
                    print("[hub] {}".format(payload.decode("utf-8", "replace").strip()))
                except Exception:
                    print("[hub] {!r}".format(payload))

        device = await BleakScanner.find_device_by_name(self.hub_name, timeout=self.timeout)
        if device is None:
            raise RuntimeError(
                "Could not find hub named '{}'. Check the Pybricks hub name and "
                "disconnect Pybricks Code before running this script.".format(self.hub_name)
            )

        async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
            await client.start_notify(PYBRICKS_COMMAND_EVENT_CHAR_UUID, handle_rx)
            print("[ble] connected to '{}'. Start the hub receiver with the hub button.".format(self.hub_name))
            self._connected.set()

            while not self._stopped.is_set():
                pending = await asyncio.to_thread(self._queue.get)
                if pending is None:
                    break

                try:
                    await asyncio.wait_for(ready_event.wait(), timeout=self.timeout)
                    ready_event.clear()
                    await client.write_gatt_char(
                        PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                        b"\x06" + pending.payload,
                        response=True,
                    )
                except Exception as exc:
                    pending.error.append(str(exc))
                finally:
                    pending.done.set()
