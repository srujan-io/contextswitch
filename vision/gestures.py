
import time
from collections import deque
from statistics import median


class GestureRecognizer:
    def __init__(self):
        self.neutral = None

        self.calibration_samples = deque(maxlen=20)
        self.samples = deque(maxlen=5)

        self.thresholds = {
            "pitch": 7.0,
            "yaw": 8.0,
            "roll": 12.0,
        }

        self.release_ratio = 0.5
        self.hold_seconds = 0.12
        self.cooldown_seconds = 0.5

        self.candidate = None
        self.candidate_since = 0.0
        self.last_emit = 0.0
        self.armed = True

    def _angles(self, pose):
        if not isinstance(pose, dict):
            return None

        if not pose.get("valid_for_actions", False):
            return None

        try:
            return {
                axis: float(pose[axis])
                for axis in ("pitch", "yaw", "roll")
            }
        except (KeyError, ValueError, TypeError):
            return None

    def calibrate(self, pose):
        angles = self._angles(pose)

        if angles is None:
            return False

        self.neutral = angles.copy()
        self.calibration_samples.clear()
        self.samples.clear()
        self.candidate = None
        self.armed = True

        print(
            "[HEAD] Manual calibration:",
            self.neutral,
            flush=True,
        )

        return True

    def reset(self):
        self.neutral = None
        self.calibration_samples.clear()
        self.samples.clear()
        self.candidate = None
        self.armed = True

    def auto_calibrate(self, pose):
        angles = self._angles(pose)

        if angles is None:
            self.calibration_samples.clear()
            return False

        self.calibration_samples.append(angles)

        if len(self.calibration_samples) < 20:
            return False

        neutral = {}

        for axis in ("pitch", "yaw", "roll"):
            values = [
                sample[axis]
                for sample in self.calibration_samples
            ]

            if max(values) - min(values) > 6.0:
                self.calibration_samples.clear()
                return False

            neutral[axis] = median(values)

        self.neutral = neutral
        self.samples.clear()
        self.calibration_samples.clear()
        self.candidate = None
        self.armed = True

        print(
            "[HEAD] Auto calibration successful:",
            self.neutral,
            flush=True,
        )

        return True

    def process(self, pose):
        now = time.monotonic()

        angles = self._angles(pose)

        if angles is None:
            self.candidate = None
            self.samples.clear()
            return None

        if self.neutral is None:
            self.auto_calibrate(pose)
            return None

        self.samples.append(angles)

        delta = {}

        for axis in ("pitch", "yaw", "roll"):
            values = [
                sample[axis]
                for sample in self.samples
            ]

            delta[axis] = (
                median(values) - self.neutral[axis]
            )

        # Choose the strongest threshold-normalized axis.
        axis = max(
            delta,
            key=lambda a: (
                abs(delta[a]) / self.thresholds[a]
            ),
        )

        magnitude = abs(delta[axis])
        threshold = self.thresholds[axis]

        if all(
            abs(delta[a])
            < self.thresholds[a] * self.release_ratio
            for a in delta
        ):
            self.armed = True
            self.candidate = None
            return None

        if not self.armed or magnitude < threshold:
            self.candidate = None
            return None

        mapping = {
            ("pitch", 1): "SCROLL_DOWN",
            ("pitch", -1): "SCROLL_UP",
            ("yaw", 1): "NEXT_PAGE",
            ("yaw", -1): "PREVIOUS_PAGE",
            ("roll", 1): "ZOOM_IN",
            ("roll", -1): "ZOOM_OUT",
        }

        sign = 1 if delta[axis] > 0 else -1
        action = mapping[(axis, sign)]

        if action != self.candidate:
            self.candidate = action
            self.candidate_since = now
            return None

        if now - self.candidate_since < self.hold_seconds:
            return None

        if now - self.last_emit < self.cooldown_seconds:
            return None

        self.last_emit = now
        self.armed = False
        self.candidate = None

        print(
            f"[HEAD GESTURE] {action} "
            f"delta={delta[axis]:.2f}",
            flush=True,
        )

        return {
            "action": action,
            "parameters": {
                "axis": axis,
                "magnitude": round(delta[axis], 2),
            },
        }
