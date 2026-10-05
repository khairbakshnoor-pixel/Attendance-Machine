"""AI Face Recognition Attendance System — local Streamlit kiosk."""
import logging
import sqlite3
import threading
import time
import uuid
import cv2
import streamlit as st

from config.settings import load_settings
from database.database import Database
from face.recognizer import SFaceBackend
from services.verification import VerificationService
from ui import admin, dashboard, live
from ui.auth import is_admin
from utils.camera import Camera

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
st.set_page_config(page_title="FaceTrack • AI Attendance", page_icon="◉", layout="wide")


@st.cache_resource
def get_database(path):
    return Database(path)


@st.cache_resource
def get_camera(index):
    camera = Camera(index)
    def reap():
        while True:
            time.sleep(2)
            camera.reap()
    threading.Thread(target=reap, daemon=True, name="camera-lease-reaper").start()
    return camera


def main():
    settings = load_settings()
    database = get_database(settings.database_path)
    camera = get_camera(settings.camera_index)
    token = st.session_state.setdefault("camera_token", uuid.uuid4().hex)
    st.markdown("""<style>
        .stApp { background: #f5f7fb; }
        [data-testid="stSidebar"] { background: #e8eef5; }
        h1, h2, h3 { color: #152d46; }
        [data-testid="stMetric"] { background: white; border-radius: 12px; }
        .block-container { padding-top: 2.2rem; max-width: 1250px; }
    </style>""", unsafe_allow_html=True)
    with st.sidebar:
        st.title("◉ FaceTrack")
        st.caption("AI FACE RECOGNITION\n\nAttendance System")
        page = st.radio("Workspace", ["Attendance kiosk", "Dashboard", "Registration", "Administration"])
        st.divider()
        st.caption("YuNet detection · SFace embeddings\n\nLocal SQLite storage · " + settings.timezone)
        if is_admin(settings):
            st.success("Administrator signed in")
            if st.button("Log out"):
                st.session_state.pop("admin_since", None)
                st.session_state.pop("enrollment", None)
                live.stop_camera(camera, token)
                st.rerun()
    if st.session_state.get("previous_page") != page:
        live.stop_camera(camera, token)
        st.session_state.pop("enrollment", None)
        if "verifier" in st.session_state:
            st.session_state.verifier.reset()
        st.session_state.previous_page = page
    if page == "Dashboard":
        dashboard.render(database, settings)
    elif page == "Administration":
        admin.render(database, settings)
    else:
        # Per-session models prevent concurrent setInputSize()/feature() calls on one DNN.
        if page == "Registration":
            from ui.auth import require_admin
            if not require_admin(settings):
                return
        if "backend" not in st.session_state:
            with st.spinner("Loading face detection and recognition models…"):
                st.session_state.backend = SFaceBackend(settings)
        backend = st.session_state.backend
        if "verifier" not in st.session_state:
            st.session_state.verifier = VerificationService(database, backend, settings)
        if page == "Attendance kiosk":
            live.render_attendance(database, settings, camera, backend, st.session_state.verifier, token)
        else:
            live.render_registration(database, settings, camera, backend, token)


try:
    main()
except ValueError as exc:
    st.error(str(exc))
except (sqlite3.Error, cv2.error, OSError):
    logging.getLogger(__name__).exception("Application setup or storage error")
    st.error("Unable to access storage, camera or models. Check file permissions and model setup, then retry.")
