"""Camera → quality → embedding → matching → liveness → attendance."""
from datetime import datetime
import time
from zoneinfo import ZoneInfo
import numpy as np

from config.settings import Settings
from database.database import Database
from face.liveness import LivenessChallenge
from face.preprocessing import head_offset
from face.recognizer import FaceBackend, match_embedding


class VerificationService:
    def __init__(self, database: Database, backend: FaceBackend, settings: Settings):
        self.database, self.backend, self.settings = database, backend, settings
        self.challenge = LivenessChallenge(settings)
        self.cooldowns: dict[int, float] = {}
        self.last_unknown = float("-inf")
        self.action = None

    def reset(self):
        self.challenge.reset()

    def process(self, frame: np.ndarray, action: str) -> tuple[str, str, np.ndarray | None]:
        if action not in {"Sign In", "Sign Out"}:
            raise ValueError("Invalid attendance action.")
        if self.action != action:
            self.reset()
            self.action = action
        monotonic = time.monotonic()
        now = datetime.now(ZoneInfo(self.settings.timezone))
        try:
            face, embedding = self.backend.extract(frame)
        except ValueError as exc:
            self.reset()
            return "info", str(exc), None
        gallery = self.database.gallery(self.backend.model_version)
        if not gallery:
            self.reset()
            return "info", "No compatible registrations. Ask an administrator to register people.", face
        match = match_embedding(embedding, gallery, self.settings.recognition_threshold, self.settings.recognition_margin)
        if match is None:
            self.reset()
            if monotonic - self.last_unknown >= self.settings.attendance_cooldown:
                self.database.unknown(now)
                self.last_unknown = monotonic
            return "warning", "Unknown Face — attendance was not marked.", face
        label = f"{match.name} · {match.employee_id} · similarity {match.score:.2f}"
        remaining = self.settings.attendance_cooldown - (monotonic - self.cooldowns.get(match.user_id, float("-inf")))
        if remaining > 0:
            self.reset()
            return "info", f"{label} · Please wait {remaining:.0f}s before another attempt.", face
        if not self.challenge.update(match.user_id, head_offset(face), monotonic):
            return "info", f"{label} · {self.challenge.instruction}", face
        message = self.database.mark(match.user_id, action, now)
        self.cooldowns[match.user_id] = monotonic
        return ("success" if message.startswith("Attendance marked") else "warning"), message, face
