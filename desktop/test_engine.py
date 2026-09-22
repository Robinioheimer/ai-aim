import ctypes
import importlib.util
import unittest
import sys
import threading
from contextlib import nullcontext
from types import SimpleNamespace
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from config import Settings


spec = importlib.util.spec_from_file_location("engine_under_test", Path(__file__).with_name("engine.py"))
engine = importlib.util.module_from_spec(spec)
with patch.object(ctypes, "WinDLL", create=True, return_value=Mock()):
    spec.loader.exec_module(engine)


class ClockStop:
    def __init__(self, clock, callback, ticks):
        self.clock, self.callback, self.ticks = clock, callback, ticks
        self.stopped, self.count = False, 0

    def is_set(self):
        return self.stopped

    def set(self):
        self.stopped = True

    def wait(self, seconds):
        self.clock[0] += max(seconds, .001)
        self.count += 1
        if self.callback:
            self.callback(self.count)
        if self.count >= self.ticks:
            self.set()
        return self.stopped


class EngineTests(unittest.TestCase):
    def run_control(self, config=None, keys=None, callback=None, captured_at=1000, ticks=15,
                    foreground=True, left=0):
        config = config or replace(Settings(), exclude_self=False)
        self.worker = engine.Detector(config)
        self.worker._phase = ""
        self.clock = [1000.0]
        self.keys = set(keys or [])
        self.cursor = [left + 100, 100]
        self.moves, self.frames = [], []
        self.worker._latest = ([{"box": [700, 300, 800, 600, .9, 0], "keypoints": []}], captured_at, 1)
        self.worker.frame.connect(self.frames.append)
        stop = ClockStop(self.clock, callback, ticks)
        self.worker._stop_event = stop

        def cursor_move(x, y):
            self.moves.append((x, y))
            self.cursor[:] = [x, y]

        with patch.object(engine.time, "perf_counter", side_effect=lambda: self.clock[0]), \
                patch.object(engine, "held", side_effect=lambda key: key in self.keys), \
                patch.object(engine, "foreground_matches", side_effect=lambda _: foreground), \
                patch.object(engine, "cursor_position", side_effect=lambda: tuple(self.cursor)), \
                patch.object(engine, "move_cursor", side_effect=cursor_move), \
                patch.object(engine, "move_mouse", side_effect=lambda x, y: self.moves.append((x, y))):
            self.worker._control_loop({"left": left, "top": 0, "width": 1000, "height": 1000})
        self.assertIsNone(self.worker._control_error)

    def test_held_hotkey_snaps_cursor_to_target(self):
        self.run_control(keys=[0x02])
        self.assertEqual(self.moves, [(750, 405)])

    def test_hotkey_can_activate_between_detections(self):
        self.run_control(callback=lambda tick: self.keys.add(0x02) if tick == 2 else None)
        self.assertEqual(self.moves, [(750, 405)])

    def test_multi_monitor_coordinates(self):
        self.run_control(keys=[0x02], left=-1920)
        self.assertEqual(self.moves, [(-1170, 405)])

    def test_smoothing_runs_between_inference_frames_and_stops_on_release(self):
        def release(tick):
            if tick == 5:
                self.keys.clear()
                self.moves_at_release = len(self.moves)
        self.run_control(replace(Settings(), smoothing=12, exclude_self=False), [0x02], release)
        self.assertGreater(len(self.moves), 1)
        self.assertEqual(len(self.moves), self.moves_at_release)
        self.assertLess(self.cursor[0], 750)

    def test_no_hotkey_or_wrong_focus_means_no_input(self):
        self.run_control()
        self.assertEqual(self.moves, [])
        self.run_control(keys=[0x02], foreground=False)
        self.assertEqual(self.moves, [])

    def test_disabled_input_means_no_input(self):
        self.run_control(replace(Settings(), aim_enabled=False), [0x02])
        self.assertEqual(self.moves, [])

    def test_stale_result_cannot_move_cursor(self):
        self.run_control(keys=[0x02], captured_at=999)
        self.assertEqual(self.moves, [])
        self.assertIn("Bild zu alt", self.frames[0]["state"])

    def test_relative_mode_does_not_repeat_same_frame_offset(self):
        self.run_control(replace(Settings(), input_mode="relative", exclude_self=False), [0x02])
        self.assertEqual(self.moves, [(250, -95)])

    def test_pause_invalidates_result(self):
        self.run_control(keys=[0x02, 0x75])
        self.assertEqual(self.moves, [])
        self.assertFalse(self.worker._active)
        self.assertIsNone(self.worker._latest)

    def test_f8_blocks_input_without_waiting_for_inference(self):
        self.run_control(keys=[0x02, 0x77])
        self.assertEqual(self.moves, [])
        self.assertTrue(self.worker._stop_event.is_set())

    def test_inference_settings_change_discards_old_result(self):
        # confidence is an inference input — changing it must drop stale detections
        self.run_control(callback=lambda tick: self.worker.configure(replace(Settings(), confidence=.5)) if tick == 1 else self.keys.add(0x02))
        self.assertEqual(self.moves, [])
        self.assertIsNone(self.worker._latest)

    def test_aim_tuning_does_not_discard_detections(self):
        # vertical/ESP cosmetics must keep the latest frame (no overlay flicker on tab switches)
        self.run_control(callback=lambda tick: self.worker.configure(replace(Settings(), vertical=.12, line_width=4)) if tick == 1 else self.keys.add(0x02))
        self.assertIsNotNone(self.worker._latest)
        self.assertEqual(self.moves, [(750, 336)])

    def test_stale_frame_still_emits_esp(self):
        self.run_control(keys=[0x02], captured_at=999)
        self.assertTrue(self.frames[0]["show_esp"])
        self.assertTrue(self.frames[0]["boxes"])
        self.assertEqual(self.moves, [])

    def test_sendinput_failure_is_not_silenced(self):
        with patch.object(engine.USER32, "SendInput", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "blocked mouse input"):
                engine.move_mouse(1, 2)

    def test_cursor_failure_is_not_silenced(self):
        with patch.object(engine.USER32, "SetCursorPos", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "blockiert"):
                engine.move_cursor(1, 2)

    def test_hotkey_and_emergency_stop_work_during_blocked_inference(self):
        worker = engine.Detector(replace(Settings(), exclude_self=False, target_max_age=1.5))
        inference_blocked, release_inference = threading.Event(), threading.Event()
        aim, emergency, moved = threading.Event(), threading.Event(), threading.Event()
        cursor = [100, 100]
        image = engine.np.zeros((1000, 1000, 4), dtype=engine.np.uint8)
        capture = Mock()
        capture.__enter__ = Mock(return_value=capture)
        capture.__exit__ = Mock(return_value=False)
        capture.monitors = [{}, {"left": 0, "top": 0, "width": 1000, "height": 1000}]
        capture.grab.return_value = image
        calls = []
        tensor = SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: [[700, 300, 800, 600, .9, 0]]))

        def predict(*args, **kwargs):
            calls.append(1)
            if len(calls) > 1:
                inference_blocked.set()
                release_inference.wait(3)
            return [SimpleNamespace(boxes=SimpleNamespace(data=tensor), keypoints=None)]

        model = SimpleNamespace(task="detect", names={0: "person"}, predict=predict)
        torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False),
                                set_num_threads=Mock(), inference_mode=nullcontext)

        def move(x, y):
            cursor[:] = [x, y]
            moved.set()

        with patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=Mock(return_value=model)), "torch": torch}), \
                patch.object(engine.Detector, "_model_cache", None), \
                patch.object(engine.mss, "mss", return_value=capture), \
                patch.object(engine, "held", side_effect=lambda key: emergency.is_set() if key == 0x77 else aim.is_set() if key == 0x02 else False), \
                patch.object(engine, "foreground_matches", return_value=True), \
                patch.object(engine, "cursor_position", side_effect=lambda: tuple(cursor)), \
                patch.object(engine, "move_cursor", side_effect=move):
            thread = threading.Thread(target=worker.run)
            thread.start()
            try:
                self.assertTrue(inference_blocked.wait(1), "Second inference never started")
                self.assertFalse(moved.is_set())
                aim.set()
                self.assertTrue(moved.wait(.5), "Input waited for blocked inference")
                self.assertEqual(cursor, [750, 405])
                emergency.set()
                self.assertTrue(worker._stop_event.wait(.5), "F8 waited for blocked inference")
                self.assertFalse(release_inference.is_set())
            finally:
                worker.stop()
                release_inference.set()
                thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertIsNone(worker._control_error)

    def test_model_is_reused_between_sessions(self):
        factory = Mock(return_value=object())
        with patch.object(engine.Detector, "_model_cache", None):
            first = engine.Detector._load_model(factory, "test-model-not-downloaded.pt", "cpu")
            second = engine.Detector._load_model(factory, "test-model-not-downloaded.pt", "cpu")
            self.assertIs(first, second)
            factory.assert_called_once()
            engine.Detector._load_model(factory, "different-model.pt", "cpu")
            self.assertEqual(factory.call_count, 2)


if __name__ == "__main__":
    unittest.main()
