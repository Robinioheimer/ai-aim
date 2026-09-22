import math


class Motion:
    def __init__(self):
        self.reset()

    def reset(self):
        self.token = None
        self.sent_x = self.sent_y = 0
        self.fraction_x = self.fraction_y = 0.0

    def step(self, token, target, origin, config, delta):
        if self.token != token:
            self.sent_x = self.sent_y = 0
            self.token = token
        dx, dy = target[0] - origin[0], target[1] - origin[1]
        if config.input_mode == "relative":
            # A screenshot is a finite movement budget, not a fresh offset on every input tick.
            dx -= self.sent_x
            dy -= self.sent_y
        delta = max(0.0, min(delta, 0.05))
        alpha = 1.0 if config.smoothing <= 0 else -math.expm1(-delta * 60 / config.smoothing)
        step_x, step_y = dx * alpha, dy * alpha
        limit = config.max_step * delta * 60
        length = math.hypot(step_x, step_y)
        if config.max_step > 0 and length > limit:
            step_x *= limit / length
            step_y *= limit / length
        step_x += self.fraction_x
        step_y += self.fraction_y
        x, y = round(step_x), round(step_y)
        x = max(min(x, math.ceil(max(dx, 0))), math.floor(min(dx, 0)))
        y = max(min(y, math.ceil(max(dy, 0))), math.floor(min(dy, 0)))
        self.fraction_x = step_x - x if dx else 0.0
        self.fraction_y = step_y - y if dy else 0.0
        self.sent_x += x
        self.sent_y += y
        return x, y


def target_is_fresh(captured_at, now, max_age):
    return captured_at is not None and 0 <= now - captured_at <= max_age
