import math
import unittest
from dataclasses import replace

from config import Settings
from motion import Motion, target_is_fresh


class MotionTests(unittest.TestCase):
    def test_zero_smoothing_moves_full_distance(self):
        self.assertEqual(Motion().step(1, (850, 350), (100, 100), Settings(), 1 / 240), (750, 250))

    def test_cursor_uses_real_position_including_negative_monitors(self):
        self.assertEqual(Motion().step(1, (-900, 350), (-1800, 100), Settings(), 1 / 240), (900, 250))

    def test_positive_smoothing_approaches_without_overshoot(self):
        motion, origin = Motion(), [0, 0]
        config = replace(Settings(), smoothing=12)
        first = motion.step(1, (1000, 500), origin, config, 1 / 240)
        self.assertGreater(first[0], 0)
        self.assertLess(first[0], 1000)
        origin = list(first)
        for _ in range(600):
            delta = motion.step(1, (1000, 500), origin, config, 1 / 240)
            origin = [origin[i] + delta[i] for i in range(2)]
            self.assertLessEqual(origin[0], 1000)
            self.assertLessEqual(origin[1], 500)
        self.assertEqual(origin, [1000, 500])

    def test_smoothing_is_time_based(self):
        config = replace(Settings(), smoothing=12)
        positions = []
        for hz in (60, 120, 240):
            motion, origin = Motion(), [0, 0]
            for _ in range(hz // 5):
                delta = motion.step(1, (1000, 500), origin, config, 1 / hz)
                origin = [origin[i] + delta[i] for i in range(2)]
            positions.append(origin)
        for position in positions:
            self.assertAlmostEqual(position[0], 1000 * (1 - math.exp(-1)), delta=2)

    def test_limit_is_independent_of_detection_rate(self):
        config = replace(Settings(), max_step=60)
        for hz in (60, 240):
            motion, origin = Motion(), [0, 0]
            for _ in range(hz):
                x, y = motion.step(1, (10000, 0), origin, config, 1 / hz)
                origin = [origin[0] + x, origin[1] + y]
            self.assertEqual(origin, [3600, 0])

    def test_relative_frame_cannot_be_applied_repeatedly(self):
        motion = Motion()
        config = replace(Settings(), input_mode="relative")
        self.assertEqual(motion.step(1, (900, 300), (500, 500), config, 1 / 240), (400, -200))
        for _ in range(20):
            self.assertEqual(motion.step(1, (900, 300), (500, 500), config, 1 / 240), (0, 0))
        self.assertEqual(motion.step(2, (550, 500), (500, 500), config, 1 / 240), (50, 0))

    def test_relative_smoothing_does_not_exceed_frame_budget(self):
        motion = Motion()
        config = replace(Settings(), input_mode="relative", smoothing=8)
        moves = [motion.step(1, (100, -200), (0, 0), config, 1 / 240) for _ in range(600)]
        self.assertEqual(tuple(sum(step[i] for step in moves) for i in range(2)), (100, -200))

    def test_fractional_motion_reaches_one_pixel_target(self):
        motion, origin = Motion(), [0, 0]
        for _ in range(240):
            dx, dy = motion.step(1, (1, -1), origin, replace(Settings(), smoothing=40), 1 / 240)
            origin = [origin[0] + dx, origin[1] + dy]
        self.assertEqual(origin, [1, -1])

    def test_new_frames_preserve_subpixel_convergence(self):
        motion, origin = Motion(), [0, 0]
        for frame in range(240):
            dx, dy = motion.step(frame, (1, -1), origin, replace(Settings(), smoothing=40), 1 / 240)
            origin = [origin[0] + dx, origin[1] + dy]
        self.assertEqual(origin, [1, -1])

    def test_target_age_is_based_on_capture_not_completion(self):
        self.assertTrue(target_is_fresh(10, 10.1, .25))
        self.assertFalse(target_is_fresh(10, 10.3, .25))
        self.assertFalse(target_is_fresh(None, 10.1, .25))
        self.assertFalse(target_is_fresh(11, 10.1, .25))


if __name__ == "__main__":
    unittest.main()
