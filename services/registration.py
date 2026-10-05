"""Enrollment only persists consistent, independently captured face samples."""
from datetime import datetime
import re
import numpy as np
from config.settings import Settings
from database.database import Database
from face.embeddings import normalize
from face.recognizer import FaceBackend


def validate_identity(employee_id: str, name: str) -> tuple[str, str]:
    employee_id, name = employee_id.strip().upper(), name.strip()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,31}", employee_id):
        raise ValueError("ID must contain 2–32 letters, digits, underscores or hyphens and start with a letter/digit.")
    if not 1 <= len(name) <= 100 or any(ord(char) < 32 for char in name):
        raise ValueError("Enter a name of 1–100 characters without control characters.")
    return employee_id, name


class Registration:
    def __init__(self, backend: FaceBackend, settings: Settings):
        self.backend, self.settings = backend, settings
        self.samples: list[np.ndarray] = []

    def add_sample(self, frame: np.ndarray):
        _, embedding = self.backend.extract(frame)
        if self.samples and min(float(embedding @ sample) for sample in self.samples) < self.settings.recognition_threshold:
            raise ValueError("Sample does not match the previous face. Use the same person or restart enrollment.")
        if len(self.samples) >= self.settings.registration_samples:
            raise ValueError("Enough samples collected. Save or restart enrollment.")
        self.samples.append(embedding)

    def save(self, database: Database, employee_id: str, name: str, now: datetime):
        employee_id, name = validate_identity(employee_id, name)
        if len(self.samples) < self.settings.registration_samples:
            raise ValueError(f"Capture {self.settings.registration_samples} valid samples first.")
        embedding = normalize(np.mean(self.samples, axis=0))
        for person in database.gallery(self.backend.model_version):
            if float(embedding @ normalize(person["embedding"])) >= self.settings.recognition_threshold:
                raise ValueError("This face resembles an existing registration. Review existing users before enrolling.")
        database.register(employee_id, name, embedding, self.backend.model_version, now)
        self.samples.clear()
