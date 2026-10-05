"""Fail-closed temporal head-turn challenge. This is basic demo liveness only."""
import secrets
import statistics
from config.settings import Settings


class LivenessChallenge:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.reset()

    def reset(self):
        self.identity = None
        self.started = None
        self.last_frame = None
        self.baseline_samples = []
        self.baseline = 0.0
        self.direction = secrets.choice((-1, 1))
        self.stage = "center"
        self.held = 0

    @property
    def instruction(self) -> str:
        if self.stage == "center":
            return "Look straight ahead and hold still."
        if self.stage == "turn":
            return "Slowly turn your nose toward the " + ("RIGHT" if self.direction > 0 else "LEFT") + " edge of the preview."
        return "Return to the center and hold still."

    def update(self, identity: int, offset: float, now: float) -> bool:
        if (identity != self.identity or self.started is None
                or now - self.started > self.settings.liveness_timeout
                or (self.last_frame is not None and (now - self.last_frame > self.settings.max_frame_gap or now <= self.last_frame))):
            self.reset()
            self.identity, self.started = identity, now
        self.last_frame = now
        if self.stage == "center":
            if abs(offset) > 0.16:
                self.baseline_samples.clear()
                return False
            self.baseline_samples.append(offset)
            if len(self.baseline_samples) >= self.settings.verification_frames:
                if max(self.baseline_samples) - min(self.baseline_samples) > 0.10:
                    self.baseline_samples.clear()
                    return False
                self.baseline = statistics.mean(self.baseline_samples)
                self.stage = "turn"
            return False
        delta = offset - self.baseline
        condition = (delta * self.direction >= self.settings.liveness_turn_delta
                     if self.stage == "turn" else abs(delta) <= self.settings.liveness_turn_delta * 0.4)
        self.held = self.held + 1 if condition else 0
        if self.held < self.settings.liveness_hold_frames:
            return False
        if self.stage == "turn":
            self.stage, self.held = "return", 0
            return False
        self.reset()
        return True
