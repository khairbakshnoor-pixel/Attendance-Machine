"""Rerunnable Streamlit fragments keep the camera responsive without blocking loops."""
from datetime import datetime
import logging
import sqlite3
from zoneinfo import ZoneInfo
import cv2
import streamlit as st
from services.registration import Registration, validate_identity
from ui.auth import is_admin, require_admin
from utils.camera import draw_face

logger = logging.getLogger(__name__)


def stop_camera(camera, token):
    camera.release(token)
    st.session_state.camera_running = False


def render_attendance(database, settings, camera, backend, verifier, token):
    st.title("Face attendance kiosk")
    st.caption("Choose an action, look at the camera, and follow the movement challenge.")
    st.info("Use only with informed consent. This local demonstration uses basic head-turn liveness; it is not certified anti-spoofing.")
    action = st.radio("Attendance action", ["Sign In", "Sign Out"], horizontal=True)
    left, right = st.columns(2)
    if left.button("Start camera", type="primary", use_container_width=True):
        verifier.reset()
        st.session_state.camera_running = True
    if right.button("Stop camera", use_container_width=True):
        stop_camera(camera, token)
        verifier.reset()
    st.caption("Camera is attached to the computer running Streamlit. Preview is not mirrored: follow the named edge of the preview.")

    @st.fragment(run_every=0.15 if st.session_state.get("camera_running") else None)
    def preview():
        if not st.session_state.get("camera_running"):
            st.info("Camera is stopped.")
            return
        try:
            frame = camera.read(token)
            severity, message, face = verifier.process(frame, action)
            st.image(draw_face(frame, face), channels="BGR", use_container_width=True)
            getattr(st, severity)(message)
            if severity in {"success", "warning"} and "Unknown Face" not in message:
                st.session_state.last_attendance_result = message
            if st.session_state.get("last_attendance_result"):
                st.caption("Last result: " + st.session_state.last_attendance_result)
        except (ValueError, cv2.error, sqlite3.Error, OSError) as exc:
            verifier.reset()
            stop_camera(camera, token)
            logger.warning("Camera verification stopped: %s", type(exc).__name__)
            st.error(str(exc) if isinstance(exc, ValueError) else "Camera, model or database failure. Stop and restart after checking your setup.")
    preview()


def render_registration(database, settings, camera, backend, token):
    st.title("Register a person")
    if not require_admin(settings):
        stop_camera(camera, token)
        return
    st.caption("Capture several clear samples with small pose variations. Raw images remain in memory only.")
    employee_id = st.text_input("Employee / student ID", max_chars=32)
    name = st.text_input("Full name", max_chars=100)
    consent = st.checkbox("The person has been informed about biometric storage and has agreed to enrollment.")
    identity_key = (employee_id.strip().upper(), name.strip())
    if st.session_state.get("enrollment_identity") != identity_key:
        st.session_state.enrollment = Registration(backend, settings)
        st.session_state.enrollment_identity = identity_key
    if "enrollment" not in st.session_state:
        st.session_state.enrollment = Registration(backend, settings)
    enrollment = st.session_state.enrollment
    a, b = st.columns(2)
    if a.button("Start enrollment camera", type="primary"):
        validate_identity(employee_id, name)
        if not consent:
            st.warning("Confirm consent before capturing samples.")
        else:
            st.session_state.camera_running = True
    if b.button("Stop & clear samples"):
        stop_camera(camera, token)
        enrollment.samples.clear()

    @st.fragment(run_every=0.2 if st.session_state.get("camera_running") else None)
    def preview():
        if not is_admin(settings):
            enrollment.samples.clear()
            stop_camera(camera, token)
            st.warning("Admin session expired. Sign in again.")
            return
        st.progress(len(enrollment.samples) / settings.registration_samples,
                    text=f"{len(enrollment.samples)} / {settings.registration_samples} samples captured")
        if not st.session_state.get("camera_running"):
            return
        try:
            frame = camera.read(token)
            st.image(frame, channels="BGR", use_container_width=True)
            if st.button("Capture sample", disabled=not consent or len(enrollment.samples) >= settings.registration_samples):
                enrollment.add_sample(frame)
                st.success(f"Sample {len(enrollment.samples)} accepted. Change your pose slightly for the next sample.")
        except ValueError as exc:
            st.warning(str(exc))
        except (cv2.error, OSError):
            stop_camera(camera, token)
            st.error("Camera/model error. Check the camera connection and downloaded models.")
    preview()
    if st.button("Save registration", type="primary", disabled=not consent):
        if not is_admin(settings):
            st.error("Admin session expired.")
            return
        enrollment.save(database, employee_id, name, datetime.now(ZoneInfo(settings.timezone)))
        stop_camera(camera, token)
        st.success(f"{name.strip()} registered successfully.")
