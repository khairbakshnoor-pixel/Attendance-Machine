"""Streamlit UI tests use temporary storage and never open the physical camera."""
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
from streamlit.testing.v1 import AppTest
from database.database import Database
from utils.security import hash_password


def test_app_starts_and_admin_routes_are_guarded(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", hash_password("test-admin-password"))
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio[0].set_value("Dashboard").run()
    assert not app.exception
    assert len(app.metric) == 0
    assert app.text_input[0].label == "Administrator password"
    app.text_input[0].set_value("test-admin-password")
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 6
    app.sidebar.radio[0].set_value("Administration").run()
    assert not app.exception
    assert len(app.dataframe) == 1
    app.sidebar.radio[0].set_value("Registration").run()
    assert not app.exception
    assert any(item.label == "Employee / student ID" for item in app.text_input)


def test_populated_dashboard_charts_filters_and_export(tmp_path, monkeypatch):
    path = tmp_path / "dashboard.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    database = Database(path)
    now = datetime.now(ZoneInfo("Asia/Karachi"))
    database.register("STU-01", "Demo Student", np.ones(128), "test", now)
    database.mark(1, "Sign In", now)
    app = AppTest.from_file("app.py", default_timeout=30)
    app.session_state["admin_since"] = time.monotonic()
    app.run()
    app.sidebar.radio[0].set_value("Dashboard").run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert len(app.get("plotly_chart")) == 4
    assert len(app.get("download_button")) == 1
    app.text_input[0].set_value("no matching person").run()
    assert not app.exception
    assert len(app.dataframe) == 0
