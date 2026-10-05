import time
import streamlit as st
from config.settings import Settings
from utils.security import LoginLimiter


@st.cache_resource
def limiter():
    return LoginLimiter()


def is_admin(settings: Settings) -> bool:
    started = st.session_state.get("admin_since", 0)
    return started > 0 and time.monotonic() - started < settings.admin_session_minutes * 60


def require_admin(settings: Settings) -> bool:
    if is_admin(settings):
        return True
    st.session_state.pop("enrollment", None)
    st.info("Administrator sign-in is required to view records or manage people.")
    if not settings.admin_password_hash:
        st.warning("Admin setup is incomplete. Run `python scripts/setup_admin.py` in the terminal, then restart the app.")
        return False
    with st.form("admin_login", clear_on_submit=True):
        password = st.text_input("Administrator password", type="password", max_chars=1024)
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        ok, message = limiter().attempt(password, settings.admin_password_hash)
        if ok:
            st.session_state.admin_since = time.monotonic()
            st.rerun()
        st.error(message)
    return False
