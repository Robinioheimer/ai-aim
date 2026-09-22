import importlib.util
import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from config import Settings
from overlay import Overlay


APP = QApplication.instance() or QApplication([])


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.overlay = Overlay(lambda *_: None)
        self.overlay.resize(1000, 1000)
        self.overlay.settings = replace(Settings(), boxes=False, labels=False, tracers=False,
                                        skeleton=False, target_marker=False, circle=False)
        self.overlay.visible_frame = True

    def tearDown(self):
        self.overlay.close()

    def image(self):
        image = QImage(1000, 1000, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        self.overlay.render(image)
        return image

    def test_self_zone_invisible_until_editing(self):
        invisible = self.image()
        self.overlay.settings = replace(self.overlay.settings, exclude_self=False)
        self.assertEqual(invisible, self.image())
        self.overlay.settings = replace(self.overlay.settings, exclude_self=True)
        self.overlay.edit_zone = True
        self.assertNotEqual(invisible, self.image())
        self.overlay.edit_zone = False
        self.assertEqual(invisible, self.image())

    def test_edit_preview_works_without_running_detection(self):
        self.overlay.visible_frame = False
        baseline = self.image()
        self.overlay.edit_zone = True
        self.assertNotEqual(baseline, self.image())

    def test_boxes_tracers_and_skeleton_render_independently(self):
        blank = self.image()
        points = [[100 + i * 5, 200 + i * 10, .95] for i in range(17)]
        self.overlay.data = {"boxes": [[100, 180, 200, 400, .8, 0]], "poses": [points], "target": None}
        for toggle in ("boxes", "tracers", "skeleton"):
            with self.subTest(toggle=toggle):
                self.overlay.settings = replace(self.overlay.settings, **{toggle: True})
                self.assertNotEqual(blank, self.image())
                self.overlay.settings = replace(self.overlay.settings, **{toggle: False})
                self.assertEqual(blank, self.image())

    def test_uncertain_and_full_rectangle_labels_render(self):
        blank = self.image()
        self.overlay.settings = replace(self.overlay.settings, boxes=True, labels=True, box_style="rectangle")
        self.overlay.data = {"boxes": [[100, 180, 200, 400, .2, 0]], "names": {0: "person"}, "target": None}
        self.assertNotEqual(blank, self.image())

    def test_missing_pose_does_not_invent_skeleton(self):
        self.overlay.settings = replace(self.overlay.settings, skeleton=True)
        blank = self.image()
        self.overlay.data = {"boxes": [[100, 180, 200, 400, .8, 0]], "poses": [[]], "target": None}
        self.assertEqual(blank, self.image())


class ConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Windows capture and input are mocked; these tests cover Qt controls, not native OS APIs.
        engine = ModuleType("engine")
        engine.Settings = Settings
        engine.Detector = Mock()
        engine.held = lambda key: False
        engine.position_overlay = Mock()
        engine.exclude_from_capture = Mock(return_value=True)
        capture = Mock()
        capture.__enter__ = Mock(return_value=capture)
        capture.__exit__ = Mock(return_value=False)
        capture.monitors = [{}, {"left": 0, "top": 0, "width": 1920, "height": 1080}]
        mss = ModuleType("mss")
        mss.mss = Mock(return_value=capture)
        spec = importlib.util.spec_from_file_location("console_under_test", Path(__file__).with_name("main.py"))
        cls.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"engine": engine, "mss": mss}):
            spec.loader.exec_module(cls.module)

    def setUp(self):
        self.console = self.module.Console()
        self.console.status_timer.stop()

    def tearDown(self):
        self.console.worker = None
        self.console.close()

    def test_constructor_and_default_controls_match_settings(self):
        config = self.console.settings()
        self.assertEqual(config, Settings())
        self.assertFalse(self.console.edit_zone.isChecked())
        self.assertFalse(self.console.overlay.edit_zone)

    def test_edit_zone_requires_tab_focus_and_explicit_toggle(self):
        with patch.object(self.console, "isActiveWindow", return_value=True):
            self.console.edit_zone.setChecked(True)
            self.assertFalse(self.console.overlay.edit_zone)
            self.console.tabs.setCurrentIndex(3)
            self.assertTrue(self.console.overlay.edit_zone)
            self.console.tabs.setCurrentIndex(2)
            self.assertFalse(self.console.overlay.edit_zone)
            self.console.tabs.setCurrentIndex(3)
            self.assertTrue(self.console.overlay.edit_zone)
        with patch.object(self.console, "isActiveWindow", return_value=False):
            self.console.refresh_overlay()
            self.assertFalse(self.console.overlay.edit_zone)
        self.assertTrue(self.console.settings().exclude_self)

    def test_profiles_and_live_customization(self):
        self.console.apply_profile(1)
        self.assertEqual(self.console.settings().model, "yolo11s-pose.pt")
        self.assertFalse(self.console.settings().tiled)
        self.console.apply_profile(0)
        self.assertEqual(self.console.settings(), Settings())
        self.console.line_width.setValue(4)
        self.console.opacity.setValue(70)
        self.console.tracers.setChecked(False)
        self.console.skeleton.setChecked(False)
        self.assertEqual(self.console.overlay.settings.line_width, 4)
        self.assertEqual(self.console.overlay.settings.opacity, 70)
        self.assertFalse(self.console.overlay.settings.tracers)
        self.assertFalse(self.console.overlay.settings.skeleton)

    def test_input_mode_and_smoothing_are_live(self):
        self.console.worker = Mock()
        self.console.input_mode.setCurrentIndex(1)
        self.console.smoothing.setValue(20)
        settings = self.console.worker.configure.call_args.args[0]
        self.assertEqual(settings.input_mode, "relative")
        self.assertEqual(settings.smoothing, 20)
        self.console.smoothing.setValue(0)
        self.assertEqual(self.console.worker.configure.call_args.args[0].smoothing, 0)

    def test_restart_preserves_hotkey_permission(self):
        self.console.finished()
        self.assertTrue(self.console.arm.isChecked())
        self.assertIsNone(self.console.worker)

    def test_invalid_zone_hides_preview_and_disarms_input(self):
        self.console.worker = Mock()
        self.console.arm.setChecked(True)
        self.console.exclusion_bounds["left"].setValue(90)
        self.assertFalse(self.console.valid_zone())
        self.assertFalse(self.console.arm.isChecked())
        self.assertFalse(self.console.overlay.edit_zone)
        self.assertFalse(self.console.worker.configure.call_args.args[0].aim_enabled)


if __name__ == "__main__":
    unittest.main()
