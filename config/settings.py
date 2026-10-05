"""Validated application configuration, resolved relative to the project root."""
from dataclasses import dataclass
from pathlib import Path
import os
import math
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / "data/attendance.db"
    timezone: str = "Asia/Karachi"
    camera_index: int = 0
    recognition_threshold: float = 0.50
    recognition_margin: float = 0.06
    detection_threshold: float = 0.90
    min_face_size: int = 90
    min_blur_score: float = 65
    verification_frames: int = 5
    attendance_cooldown: float = 30
    liveness_turn_delta: float = 0.16
    liveness_hold_frames: int = 3
    liveness_timeout: float = 20
    max_frame_gap: float = 1.5
    registration_samples: int = 5
    admin_session_minutes: int = 30
    admin_password_hash: str = ""

    def __post_init__(self):
        ZoneInfo(self.timezone)
        for key in self.__dataclass_fields__:
            value = getattr(self, key)
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"{key} must be finite.")
        if not 0 < self.recognition_threshold < 1:
            raise ValueError("RECOGNITION_THRESHOLD must be between 0 and 1.")
        if not 0 <= self.recognition_margin < 1 or not 0 < self.detection_threshold <= 1:
            raise ValueError("Invalid detection threshold or recognition margin.")
        for key in ("min_face_size", "min_blur_score", "attendance_cooldown",
                    "liveness_turn_delta", "liveness_timeout", "max_frame_gap", "admin_session_minutes"):
            if getattr(self, key) <= 0:
                raise ValueError(f"{key} must be positive.")
        if self.verification_frames < 3 or self.liveness_hold_frames < 2 or self.registration_samples < 3:
            raise ValueError("Use at least 3 verification/registration frames and 2 liveness hold frames.")
        if self.camera_index < 0:
            raise ValueError("CAMERA_INDEX must be nonnegative.")


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    defaults = Settings()
    values = {}
    for key in defaults.__dataclass_fields__:
        raw = os.getenv(key.upper())
        if raw is None:
            continue
        default = getattr(defaults, key)
        if isinstance(default, Path):
            path = Path(raw)
            values[key] = path if path.is_absolute() else ROOT / path
        else:
            values[key] = type(default)(raw)
    return Settings(**values)
