from __future__ import annotations

import ctypes
import os
import threading
import time
from dataclasses import replace
from ctypes import wintypes

import mss
import numpy as np
from PySide6.QtCore import QThread, Signal
from targeting import select_target, input_status, can_move


from config import Settings, BUILTIN_POSE_MODELS
from vision import resolve_classes, infer_frame, attach_poses
from motion import Motion, target_is_fresh


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KeyboardInput(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class InputUnion(ctypes.Union):
    _fields_ = [("mi", MouseInput), ("ki", KeyboardInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _anonymous_ = ("payload",)
    _fields_ = [("type", wintypes.DWORD), ("payload", InputUnion)]


USER32 = ctypes.WinDLL("user32", use_last_error=True)
USER32.GetForegroundWindow.restype = wintypes.HWND
USER32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
USER32.GetWindowThreadProcessId.restype = wintypes.DWORD
USER32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
USER32.GetAsyncKeyState.argtypes = [ctypes.c_int]
USER32.GetAsyncKeyState.restype = ctypes.c_short
USER32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(Input), ctypes.c_int]
USER32.SendInput.restype = wintypes.UINT
USER32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
USER32.GetCursorPos.restype = wintypes.BOOL
USER32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
USER32.SetCursorPos.restype = wintypes.BOOL
USER32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
USER32.SetWindowDisplayAffinity.restype = wintypes.BOOL
USER32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
USER32.SetWindowPos.restype = wintypes.BOOL


def position_overlay(window_id: int, monitor: dict) -> None:
    USER32.SetWindowPos(wintypes.HWND(window_id), None, monitor["left"], monitor["top"],
                        monitor["width"], monitor["height"], 0x0004 | 0x0010)


def held(key: int) -> bool:
    return bool(USER32.GetAsyncKeyState(key) & 0x8000)


def foreground_matches(title: str) -> bool:
    buffer = ctypes.create_unicode_buffer(512)
    window = USER32.GetForegroundWindow()
    process_id = wintypes.DWORD()
    USER32.GetWindowThreadProcessId(window, ctypes.byref(process_id))
    if process_id.value == os.getpid():
        return False
    USER32.GetWindowTextW(window, buffer, len(buffer))
    return bool(title.strip()) and title.casefold() in buffer.value.casefold()


def move_mouse(dx: int, dy: int) -> None:
    event = Input(type=0, payload=InputUnion(mi=MouseInput(dx, dy, 0, 0x0001, 0, 0)))
    if USER32.SendInput(1, ctypes.byref(event), ctypes.sizeof(Input)) != 1:
        raise RuntimeError("Windows blocked mouse input. Input injection may be restricted by the game; no bypass is attempted.")


def cursor_position():
    point = wintypes.POINT()
    if not USER32.GetCursorPos(ctypes.byref(point)):
        raise RuntimeError("Cursorposition konnte nicht gelesen werden.")
    return point.x, point.y


def move_cursor(x: int, y: int):
    if not USER32.SetCursorPos(x, y):
        raise RuntimeError("Windows hat die Cursorbewegung blockiert. Keine Umgehung wird versucht.")


def exclude_from_capture(window_id: int) -> bool:
    return bool(USER32.SetWindowDisplayAffinity(wintypes.HWND(window_id), 0x11))


class Detector(QThread):
    frame = Signal(object)
    status = Signal(str)
    failed = Signal(str)
    _model_cache = None
    _pose_cache = None

    def __init__(self, settings: Settings):
        super().__init__()
        self._settings = settings
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._active = True
        self._epoch = 0
        self._sequence = 0
        self._latest = None
        self._fps = 0.0
        self._names = {}
        self._device = ""
        self._phase = "Lade Modell · erster Start benötigt gegebenenfalls einen Download…"
        self._control_error = None

    def configure(self, settings: Settings):
        with self._lock:
            self._settings = replace(settings)
            self._epoch += 1
            self._latest = None

    def stop(self):
        self._stop_event.set()

    def _cancelled(self, epoch):
        with self._lock:
            return self._stop_event.is_set() or not self._active or epoch != self._epoch

    def _set_phase(self, text):
        with self._lock:
            self._phase = text
        self.status.emit(text)

    @classmethod
    def _load_model(cls, factory, path, device, pose=False):
        stamp = os.stat(path).st_mtime_ns if os.path.isfile(path) else None
        key = (os.path.abspath(path), stamp, device)
        slot = "_pose_cache" if pose else "_model_cache"
        cached = getattr(cls, slot)
        if cached is not None and cached[0] == key:
            return cached[1]
        setattr(cls, slot, None)
        model = factory(path)
        stamp = os.stat(path).st_mtime_ns if os.path.isfile(path) else None
        setattr(cls, slot, ((os.path.abspath(path), stamp, device), model))
        return model

    def _control_loop(self, monitor):
        motion = Motion()
        previous_toggle = False
        previous_time = time.perf_counter()
        next_display = 0.0
        try:
            while not self._stop_event.is_set():
                started = time.perf_counter()
                delta = started - previous_time
                previous_time = started
                if held(0x77):
                    self.stop()
                    break
                with self._lock:
                    config = self._settings
                    toggle = held(config.toggle_key)
                    if toggle and not previous_toggle:
                        self._active = not self._active
                        self._epoch += 1
                        self._latest = None
                    previous_toggle = toggle
                    active, latest, epoch = self._active, self._latest, self._epoch
                    phase, fps, names, device = self._phase, self._fps, self._names, self._device
                foreground = foreground_matches(config.window_title)
                aim_held = held(config.aim_key)
                boxes, target, detections = [], None, []
                fresh = latest is not None and target_is_fresh(latest[1], started, config.target_max_age)
                if active and fresh:
                    detections = latest[0]
                    boxes, target = select_target([item["box"] for item in detections], config,
                                                   monitor["width"], monitor["height"])
                if active and can_move(config, target, foreground, aim_held):
                    if config.input_mode == "cursor":
                        origin = cursor_position()
                        point = (monitor["left"] + target[1], monitor["top"] + target[2])
                    else:
                        origin = (monitor["width"] / 2, monitor["height"] / 2)
                        point = target[1:]
                    step_x, step_y = motion.step((latest[2], point, config.input_mode), point,
                                                 origin, config, delta)
                    # Check gates again immediately before input, independently of model latency.
                    with self._lock:
                        valid_epoch = epoch == self._epoch
                    if (valid_epoch and not self._stop_event.is_set() and not held(0x77)
                            and foreground_matches(config.window_title)
                            and (config.automatic or held(config.aim_key))
                            and target_is_fresh(latest[1], time.perf_counter(), config.target_max_age)):
                        if step_x or step_y:
                            if config.input_mode == "cursor":
                                move_cursor(origin[0] + step_x, origin[1] + step_y)
                            else:
                                move_mouse(step_x, step_y)
                    else:
                        motion.reset()
                else:
                    motion.reset()
                if started >= next_display:
                    if not active:
                        state = "Paused · F6 / gewählter Pause-Hotkey zum Fortsetzen"
                    elif phase:
                        state = phase
                    elif not foreground and not config.desktop_detection:
                        state = "Warte auf Spielfenster im Vordergrund"
                    elif latest is not None and not fresh:
                        state = "Bild zu alt für Eingabe (>250 ms) · Auflösung reduzieren / Schnellprofil wählen"
                    else:
                        state = f"Running · {device} · " + input_status(config, target, foreground, aim_held)
                    accepted = {tuple(box) for box in boxes}
                    self.frame.emit({"boxes": boxes, "target": target, "monitor": monitor,
                                     "poses": [item["keypoints"] for item in detections
                                               if tuple(item["box"]) in accepted],
                                     "names": names, "fps": fps, "state": state,
                                     "latency_ms": (started - latest[1]) * 1000 if latest else None})
                    next_display = started + 1 / 30
                self._stop_event.wait(max(0, 1 / 240 - (time.perf_counter() - started)))
        except Exception as exc:
            self._control_error = str(exc)
            self.stop()

    def run(self):
        controller = None
        error = None
        try:
            with self._lock:
                initial = self._settings
            with mss.mss() as capture:
                if not 1 <= initial.monitor < len(capture.monitors):
                    raise ValueError("Selected monitor is no longer available.")
                monitor = capture.monitors[initial.monitor]
                controller = threading.Thread(target=self._control_loop, args=(monitor,), daemon=True)
                controller.start()
                from ultralytics import YOLO
                import torch

                if self._stop_event.is_set():
                    return
                device = "0" if torch.cuda.is_available() else "cpu"
                if device == "cpu":
                    torch.set_num_threads(max(1, min(4, (os.cpu_count() or 2) // 2)))
                model = self._load_model(YOLO, initial.model, device)
                if model.task not in {"detect", "pose"}:
                    raise ValueError("Bitte ein Detect- oder Pose-Modell auswählen.")
                classes = resolve_classes(model.names, initial.class_id)
                native_pose = initial.model in BUILTIN_POSE_MODELS and model.task == "pose"
                pose_model = None
                with self._lock:
                    self._names, self._device = model.names, "CUDA GPU" if device != "cpu" else "CPU"
                self._set_phase(f"{self._device} · erste Inferenz wird vorbereitet…")
                with torch.inference_mode():
                    while not self._stop_event.is_set():
                        with self._lock:
                            config, active, epoch = self._settings, self._active, self._epoch
                        if not active or (not config.desktop_detection and not foreground_matches(config.window_title)):
                            with self._lock:
                                self._latest = None
                            self._stop_event.wait(0.02)
                            continue
                        started = time.perf_counter()
                        image = np.ascontiguousarray(np.asarray(capture.grab(monitor))[:, :, :3])
                        should_stop = lambda: self._cancelled(epoch)
                        detections = infer_frame(model, image, config, classes, device, should_stop,
                                                 allow_pose=native_pose and config.skeleton)
                        if config.skeleton and not native_pose and detections and not should_stop():
                            if pose_model is None:
                                self._set_phase("Lade optionales Nano-Pose-Modell · für maximale Geschwindigkeit Skeleton deaktivieren")
                                pose_model = self._load_model(YOLO, "yolo11n-pose.pt", device, pose=True)
                            poses = infer_frame(pose_model, image, replace(config, tiled=False, image_size=640),
                                                [0], device, should_stop)
                            attach_poses(detections, poses)
                        if should_stop():
                            continue
                        elapsed = time.perf_counter() - started
                        with self._lock:
                            if epoch == self._epoch and self._active and not self._stop_event.is_set():
                                self._sequence += 1
                                # Only the newest frame is retained; no inference or input backlog.
                                self._latest = (detections, started, self._sequence)
                                self._fps = 1 / max(elapsed, .001)
                                self._phase = ""
        except Exception as exc:
            error = str(exc)
        finally:
            self.stop()
            if controller is not None:
                controller.join()
            if error or self._control_error:
                self.failed.emit(error or self._control_error)
