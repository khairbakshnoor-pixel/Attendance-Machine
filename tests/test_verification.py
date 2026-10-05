from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
from config.settings import Settings
from database.database import Database
from face.embeddings import normalize
from services.verification import VerificationService


class Backend:
    model_version = "test"
    offset = 0
    unknown = False
    bad_frame = False

    def extract(self, frame):
        if self.bad_frame:
            raise ValueError("Multiple faces detected.")
        face = np.array([0, 0, 100, 100, 20, 20, 80, 20, 50 + self.offset * 60, 50, 20, 80, 80, 80, .99])
        return face, normalize(np.ones(128) * (-1 if self.unknown else 1))


def test_end_to_end_gate_and_cooldown(tmp_path, monkeypatch):
    database = Database(tmp_path / "test.db")
    database.register("EMP-1", "Test", normalize(np.ones(128)), "test", datetime.now(ZoneInfo("Asia/Karachi")))
    backend = Backend()
    service = VerificationService(database, backend, Settings())
    clock = [100.0]
    monkeypatch.setattr("services.verification.time.monotonic", lambda: clock[0])
    def frame(offset=0):
        backend.offset = offset
        clock[0] += .15
        return service.process(np.zeros((10, 10, 3)), "Sign In")
    for _ in range(5):
        frame()
    assert database.metrics(datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat())["Total sign-ins"] == 0
    direction = service.challenge.direction
    for _ in range(3):
        frame(.2 * direction)
    for _ in range(2):
        frame()
    assert frame()[0] == "success"
    assert "Please wait" in frame()[1]
    backend.unknown = True
    assert "Unknown Face" in frame()[1]
    frame()
    assert database.metrics("2026-10-05")["Unknown attempts"] == 1
    backend.bad_frame = True
    assert "Multiple faces" in frame()[1]
    assert service.challenge.stage == "center"


def test_action_change_cannot_reuse_liveness(tmp_path, monkeypatch):
    database = Database(tmp_path / "test.db")
    database.register("EMP-1", "Test", normalize(np.ones(128)), "test", datetime.now(ZoneInfo("Asia/Karachi")))
    backend = Backend()
    service = VerificationService(database, backend, Settings())
    clock = [10.0]
    monkeypatch.setattr("services.verification.time.monotonic", lambda: clock[0])
    for _ in range(5):
        clock[0] += .1
        service.process(np.zeros((10, 10, 3)), "Sign In")
    assert service.challenge.stage == "turn"
    clock[0] += .1
    service.process(np.zeros((10, 10, 3)), "Sign Out")
    assert service.challenge.stage == "center"
    assert database.metrics("2026-10-05")["Total sign-ins"] == 0
