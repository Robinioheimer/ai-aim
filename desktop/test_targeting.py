import unittest
from types import SimpleNamespace
from targeting import select_target, can_move, input_status


def settings(**overrides):
    values = dict(exclude_self=True, exclude_left=15, exclude_top=40,
                  exclude_right=50, exclude_bottom=100, vertical=0.35,
                  fov=600, aim_enabled=True, automatic=False)
    values.update(overrides)
    return SimpleNamespace(**values)


class TargetingTests(unittest.TestCase):
    def test_self_zone_removes_box_and_target(self):
        own = [200, 400, 400, 950, .9, 0]
        enemy = [600, 300, 700, 600, .8, 0]
        boxes, target = select_target([own, enemy], settings(), 1000, 1000)
        self.assertEqual(boxes, [enemy])
        self.assertEqual(target[1:], (650, 405))

    def test_zone_can_be_disabled(self):
        boxes, _ = select_target([[200, 400, 400, 950, .9, 0]], settings(exclude_self=False), 1000, 1000)
        self.assertEqual(len(boxes), 1)

    def test_head_point(self):
        _, target = select_target([[600, 300, 700, 600, .8, 0]], settings(vertical=.12), 1000, 1000)
        self.assertEqual(target[2], 336)

    def test_radius_is_not_detection_range(self):
        boxes, target = select_target([[600, 300, 700, 600, .8, 0]], settings(fov=20), 1000, 1000)
        self.assertEqual(len(boxes), 1)
        self.assertIsNone(target)

    def test_hold_mode(self):
        self.assertFalse(can_move(settings(), (0, 500, 500), True, False))
        self.assertTrue(can_move(settings(), (0, 500, 500), True, True))

    def test_automatic_requires_arm_focus_and_target(self):
        target = (0, 500, 500)
        self.assertTrue(can_move(settings(automatic=True), target, True, False))
        self.assertFalse(can_move(settings(automatic=True), target, False, False))
        self.assertFalse(can_move(settings(automatic=True, aim_enabled=False), target, True, False))
        self.assertFalse(can_move(settings(automatic=True), None, True, False))

    def test_status_explains_hotkey_gate(self):
        self.assertEqual(input_status(settings(), (0, 500, 500), True, False), "Warte auf Ziel-Hotkey")


if __name__ == "__main__":
    unittest.main()
