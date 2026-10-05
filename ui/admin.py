from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from ui.auth import require_admin, is_admin
from ui.dashboard import attendance_table


def render(database, settings):
    st.title("People & administration")
    if not require_admin(settings):
        return
    people = database.users()
    st.subheader("Registered people")
    st.caption("Add a person from the Registration page. Face images are never stored; embeddings are excluded from this view.")
    st.dataframe(people, use_container_width=True, hide_index=True)
    if people:
        with st.expander("Remove a registration"):
            st.warning("This erases the biometric template and archives the person. Historical attendance and the reserved ID are retained.")
            person = st.selectbox("Person to remove", people, format_func=lambda user: f"{user['name']} ({user['employee_id']})")
            confirmation = st.text_input("Type the employee/student ID to confirm")
            if st.button("Erase biometric registration", type="primary"):
                if not is_admin(settings):
                    st.error("Session expired. Sign in again.")
                elif confirmation.strip().upper() != person["employee_id"]:
                    st.error("The confirmation ID does not match.")
                else:
                    database.delete_user(person["id"], datetime.now(ZoneInfo(settings.timezone)))
                    st.session_state["admin_notice"] = "Biometric registration erased; attendance retained."
                    st.rerun()
    if "admin_notice" in st.session_state:
        st.success(st.session_state.pop("admin_notice"))
    st.subheader("Search & export attendance")
    attendance_table(database, settings, "admin_records")
