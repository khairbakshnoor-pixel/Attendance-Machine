from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pytest
from database.database import Database

NOW = datetime(2026, 10, 5, 9, tzinfo=ZoneInfo("Asia/Karachi"))


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    database.register("EMP-01", "Ayesha", np.ones(128) / np.sqrt(128), "test-model", NOW)
    return database


def test_attendance_state_machine(db):
    assert "Sign in first" in db.mark(1, "Sign Out", NOW)
    assert db.records("2026-10-05", "2026-10-05") == []
    assert "successfully" in db.mark(1, "Sign In", NOW)
    assert "Already signed in" in db.mark(1, "Sign In", NOW)
    assert "successfully" in db.mark(1, "Sign Out", NOW + timedelta(hours=8))
    assert "Already signed out" in db.mark(1, "Sign Out", NOW + timedelta(hours=9))
    assert len(db.records("2026-10-05", "2026-10-05")) == 1
    assert db.metrics("2026-10-05")["Currently signed in"] == 0


def test_concurrent_sign_in_is_atomic(db):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: db.mark(1, "Sign In", NOW), range(16)))
    assert sum("successfully" in result for result in results) == 1
    assert len(db.records("2026-10-05", "2026-10-05")) == 1


def test_duplicate_id_and_archival(db):
    with pytest.raises(ValueError, match="already registered"):
        db.register("emp-01", "Other", np.ones(128), "test-model", NOW)
    db.mark(1, "Sign In", NOW)
    db.delete_user(1, NOW)
    assert db.users() == []
    assert db.gallery("test-model") == []
    assert len(db.records("2026-10-05", "2026-10-05")) == 1
    with pytest.raises(ValueError, match="no longer active"):
        db.mark(1, "Sign Out", NOW)


def test_model_isolation_export_privacy_and_search(db):
    assert db.gallery("wrong-model") == []
    assert len(db.gallery("test-model")) == 1
    db.mark(1, "Sign In", NOW)
    rows = db.records("2026-10-05", "2026-10-05", "ayesha")
    assert len(rows) == 1
    assert "embedding" not in rows[0]
    assert db.records("2026-10-05", "2026-10-05", "' OR 1=1 --") == []


def test_daily_boundary_and_clock_regression(db):
    db.mark(1, "Sign In", NOW)
    with pytest.raises(ValueError, match="clock"):
        db.mark(1, "Sign Out", NOW - timedelta(seconds=1))
    assert "Sign in first" in db.mark(1, "Sign Out", NOW + timedelta(days=1))
    assert "successfully" in db.mark(1, "Sign In", NOW + timedelta(days=1))


def test_unknown_attempt_metrics(db):
    db.unknown(NOW)
    assert db.metrics("2026-10-05")["Unknown attempts"] == 1
