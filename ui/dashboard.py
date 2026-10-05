from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.express as px
import streamlit as st
from ui.auth import require_admin
from utils.security import csv_safe


def attendance_table(database, settings, key="records"):
    today = datetime.now(ZoneInfo(settings.timezone)).date()
    a, b, c = st.columns([1, 1, 2])
    start = a.date_input("From", today - timedelta(days=30), key=key + "start")
    end = b.date_input("Through", today, key=key + "end")
    search = c.text_input("Search name or employee/student ID", key=key + "search")
    if start > end:
        st.warning("The start date must be on or before the end date.")
        return pd.DataFrame()
    records = pd.DataFrame(database.records(start.isoformat(), end.isoformat(), search))
    if records.empty:
        st.info("No attendance records match these filters.")
        return records
    people = st.multiselect("Person", sorted(records["name"].unique()), key=key + "people")
    if people:
        records = records[records["name"].isin(people)]
    st.dataframe(records, use_container_width=True, hide_index=True)
    safe = records.map(csv_safe)
    st.download_button("Download filtered CSV", safe.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"attendance_{start}_{end}.csv", mime="text/csv")
    return records


def render(database, settings):
    st.title("Attendance overview")
    st.caption("Live operational totals and attendance trends • " + settings.timezone)
    if not require_admin(settings):
        return
    today = datetime.now(ZoneInfo(settings.timezone)).date().isoformat()
    metrics = database.metrics(today)
    for row in (list(metrics.items())[:3], list(metrics.items())[3:]):
        for column, (label, value) in zip(st.columns(3), row):
            column.metric(label, value, border=True)
    st.caption("Currently signed in counts today's open records. Unknown attempts are rate-limited events, not unique people. Totals include archived users.")
    st.subheader("Attendance records")
    records = attendance_table(database, settings)
    if records.empty:
        return
    st.subheader("Attendance analytics")
    chart_data = records.copy()
    chart_data["day"] = pd.to_datetime(chart_data["date"])
    for tab, rule, label in zip(st.tabs(["Daily", "Weekly", "Monthly", "Sign-in times"]),
                                ["D", "W-MON", "MS", None], ["Daily attendance", "Weekly attendance", "Monthly attendance", "Sign-in trends"]):
        with tab:
            if rule:
                values = chart_data.set_index("day").resample(rule).size().reset_index(name="Attendance")
                chart = px.bar(values, x="day", y="Attendance", title=label, color_discrete_sequence=["#16a085"])
            else:
                chart_data["Hour"] = chart_data["sign_in_time"].str[11:13].astype(int)
                values = chart_data.groupby("Hour").size().reindex(range(24), fill_value=0).reset_index(name="Sign-ins")
                chart = px.line(values, x="Hour", y="Sign-ins", markers=True, title=label)
            chart.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(chart, use_container_width=True)
