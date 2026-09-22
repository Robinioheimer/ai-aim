import ast
import unittest
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace

from config import Settings
from targeting import select_target
from vision import (resolve_classes, regions, iou, merge_detections, translated_detections,
                    attach_poses, skeleton_segments, infer_frame)


class VisionTests(unittest.TestCase):
    def test_ui_help_keys_exist(self):
        from help_text import HELP
        tree = ast.parse(Path(__file__).with_name("main.py").read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "AccentCheckBox":
                self.assertIn(ast.literal_eval(node.args[0]), HELP)
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"field", "slider"}:
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    self.assertIn(node.args[1].value, HELP)

    def test_fast_defaults(self):
        config = Settings()
        self.assertEqual(config.model, "yolo11n.pt")
        self.assertEqual(config.image_size, 640)
        self.assertEqual(config.confidence, .2)
        self.assertTrue(config.full_screen and config.aim_enabled)
        self.assertFalse(config.tiled or config.skeleton or config.automatic)
        self.assertEqual(config.input_mode, "cursor")
        self.assertEqual(config.smoothing, 0)
        self.assertEqual(config.max_step, 0)

    def test_settings_roundtrip_persists(self):
        import tempfile
        from pathlib import Path
        from config import load_settings, save_settings
        custom = replace(Settings(), window_title="My Game", monitor=2, smoothing=12,
                         box_color="#ff0000", aim_key=0x05, profile=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            save_settings(custom, path)
            self.assertEqual(load_settings(path), custom)
            # Unknown keys from a newer build must not break older loads.
            path.write_text('{"window_title": "Kept", "not_a_field": true}', encoding="utf-8")
            loaded = load_settings(path)
            self.assertEqual(loaded.window_title, "Kept")
            self.assertEqual(loaded.model, Settings().model)
        self.assertEqual(load_settings(Path(tmp) / "missing.json"), Settings())

    def test_player_class_not_head(self):
        self.assertEqual(resolve_classes({0: "head", 1: "player"}, -1), [1])
        self.assertEqual(resolve_classes({0: "person", 1: "car"}, -1), [0])
        with self.assertRaises(ValueError):
            resolve_classes({0: "head"}, -1)
        with self.assertRaises(ValueError):
            resolve_classes({0: "person"}, 1)

    def test_overlapping_tiles_cover_screen(self):
        crops = regions(1920, 1080, True)
        self.assertEqual(len(crops), 5)
        self.assertEqual(crops[0], (0, 0, 1920, 1080))
        self.assertEqual(crops[-1][2:], (1920, 1080))
        self.assertGreater(crops[1][2], crops[2][0])
        self.assertEqual(regions(1920, 1080, False), [crops[0]])

    def test_tile_offsets_apply_to_boxes_and_pose(self):
        poses = [[[10, 20, .9] for _ in range(17)]]
        item = translated_detections([[0, 0, 100, 200, .9, 0]], poses, 800, 400, 1920, 1080)[0]
        self.assertEqual(item["box"][:4], [800, 400, 900, 600])
        self.assertEqual(item["keypoints"][0], [810, 420, .9])

    def test_nms_preserves_pose_association(self):
        high = {"box": [10, 10, 100, 200, .9, 0], "keypoints": [[1, 2, .9]] * 17}
        low = {"box": [12, 12, 102, 202, .6, 0], "keypoints": []}
        separate = {"box": [300, 10, 400, 200, .3, 0], "keypoints": []}
        merged = merge_detections([low, separate, high])
        self.assertEqual(merged, [high, separate])
        self.assertEqual(iou(high["box"], high["box"]), 1)

    def test_invalid_and_degenerate_boxes_rejected(self):
        self.assertEqual(merge_detections([{"box": [10, 10, 0, 0, .8, 0], "keypoints": []}]), [])

    def test_pose_matching_is_one_to_one(self):
        items = [{"box": [0, 0, 100, 200, .8, 1], "keypoints": []},
                 {"box": [5, 5, 105, 205, .7, 1], "keypoints": []}]
        poses = [{"box": [0, 0, 100, 200, .9, 0], "keypoints": [[10, 20, .9]] * 17}]
        attach_poses(items, poses)
        self.assertTrue(items[0]["keypoints"])
        self.assertFalse(items[1]["keypoints"])

    def test_low_confidence_and_invalid_joints_not_drawn(self):
        self.assertEqual(skeleton_segments([[10, 20, .2]] * 17, .45), [])
        self.assertEqual(skeleton_segments([[0, 0, .9]] * 17, .45), [])
        self.assertEqual(skeleton_segments([[float("nan"), 20, .9]] * 17, .45), [])
        self.assertEqual(skeleton_segments([[10, 20, .9]] * 5, .45), [])
        self.assertGreater(len(skeleton_segments([[10, 20, .9]] * 17, .45)), 0)

    def test_fullscreen_keeps_target_outside_radius(self):
        boxes = [[1800, 50, 1850, 150, .8, 0]]
        config = replace(Settings(), fov=10, exclude_self=False)
        self.assertIsNotNone(select_target(boxes, config, 1920, 1080)[1])
        self.assertIsNone(select_target(boxes, replace(config, full_screen=False), 1920, 1080)[1])

    def test_no_skeleton_for_excluded_self(self):
        boxes = [[200, 400, 400, 950, .9, 0], [600, 300, 700, 600, .8, 0]]
        accepted, _ = select_target(boxes, Settings(), 1000, 1000)
        self.assertEqual(accepted, [boxes[1]])

    def test_fast_profile_runs_one_inference_instead_of_five(self):
        calls = []
        tensor = SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: [[600, 200, 700, 500, .9, 0]]))
        class Image:
            shape = (1080, 1920, 3)
            def __getitem__(self, _):
                return self
        class Model:
            def predict(self, image, **kwargs):
                calls.append(kwargs)
                return [SimpleNamespace(boxes=SimpleNamespace(data=tensor), keypoints=None)]
        detections = infer_frame(Model(), Image(), Settings(), [0], "cpu", lambda: False)
        self.assertEqual(len(calls), 1)
        self.assertEqual(detections[0]["box"], [600, 200, 700, 500, .9, 0])
        calls.clear()
        infer_frame(Model(), Image(), replace(Settings(), tiled=True), [0], "cpu", lambda: False)
        self.assertEqual(len(calls), 5)

    def test_inference_stops_between_tiles(self):
        calls = []
        tensor = SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: []))
        class Image:
            shape = (1080, 1920, 3)
            def __getitem__(self, _):
                return self
        class Model:
            def predict(self, image, **kwargs):
                calls.append(kwargs)
                return [SimpleNamespace(boxes=SimpleNamespace(data=tensor), keypoints=None)]
        self.assertEqual(infer_frame(Model(), Image(), replace(Settings(), tiled=True), [0], "cpu", lambda: len(calls) == 1), [])
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0]["half"])
        self.assertEqual(calls[0]["imgsz"], 640)


if __name__ == "__main__":
    unittest.main()
