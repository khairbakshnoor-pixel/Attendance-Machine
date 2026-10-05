"""Short-lived SQLite connections and atomic attendance transactions."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3

import numpy as np


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(Path(__file__).with_name("schema.sql").read_text())
            if connection.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] != 1:
                raise ValueError("Unsupported database schema version.")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def register(self, employee_id: str, name: str, embedding: np.ndarray, model: str, now: datetime):
        # No pickle: bounded little-endian float32 avoids executable deserialization.
        vector = np.asarray(embedding, dtype="<f4").reshape(-1)
        if vector.size != 128 or not np.isfinite(vector).all() or np.linalg.norm(vector) < 1e-8:
            raise ValueError("Invalid face embedding.")
        with self.connect() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO users(employee_id,name,created_at) VALUES(?,?,?)",
                    (employee_id, name, now.isoformat()),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("This employee/student ID is already registered, including archived IDs.") from exc
            connection.execute("INSERT INTO biometrics VALUES(?,?,?,?)",
                               (cursor.lastrowid, model, vector.tobytes(), vector.size))
            connection.execute("INSERT INTO audit_log(occurred_at,action,employee_id) VALUES(?,?,?)",
                               (now.isoformat(), "register", employee_id))

    def users(self) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(
                "SELECT id,employee_id,name,created_at FROM users WHERE active=1 ORDER BY name")]

    def gallery(self, model: str) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT u.id,u.employee_id,u.name,b.embedding,b.dimensions FROM users u "
                "JOIN biometrics b ON u.id=b.user_id WHERE u.active=1 AND b.model_version=?", (model,))
            result = []
            for row in rows:
                item = dict(row)
                vector = np.frombuffer(item.pop("embedding"), dtype="<f4").copy()
                if vector.size != item.pop("dimensions") or vector.size != 128 or not np.isfinite(vector).all():
                    raise ValueError("Corrupt biometric template; re-enroll the affected person.")
                item["embedding"] = vector
                result.append(item)
            return result

    def delete_user(self, user_id: int, now: datetime):
        """Erase biometrics, archive identity, preserve historical attendance and audit."""
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            user = connection.execute("SELECT employee_id FROM users WHERE id=? AND active=1", (user_id,)).fetchone()
            if user is None:
                raise ValueError("Person was already removed.")
            connection.execute("DELETE FROM biometrics WHERE user_id=?", (user_id,))
            connection.execute("UPDATE users SET active=0 WHERE id=?", (user_id,))
            connection.execute("INSERT INTO audit_log(occurred_at,action,employee_id) VALUES(?,?,?)",
                               (now.isoformat(), "delete_biometrics_and_archive", user[0]))

    def mark(self, user_id: int, action: str, now: datetime) -> str:
        if action not in {"Sign In", "Sign Out"}:
            raise ValueError("Invalid attendance action.")
        today, timestamp = now.date().isoformat(), now.isoformat(timespec="seconds")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            user = connection.execute("SELECT * FROM users WHERE id=? AND active=1", (user_id,)).fetchone()
            if user is None:
                raise ValueError("This registration is no longer active.")
            row = connection.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (user_id, today)).fetchone()
            if action == "Sign In":
                if row:
                    return "Already signed in today."
                connection.execute(
                    "INSERT INTO attendance(user_id,employee_id,name,date,sign_in_time) VALUES(?,?,?,?,?)",
                    (user_id, user["employee_id"], user["name"], today, timestamp))
                return "Attendance marked successfully — signed in."
            if row is None:
                return "Sign in first; no sign-in record exists today."
            if row["sign_out_time"]:
                return "Already signed out today."
            if timestamp < row["sign_in_time"]:
                raise ValueError("System clock moved backward. Correct it before signing out.")
            connection.execute("UPDATE attendance SET sign_out_time=? WHERE id=?", (timestamp, row["id"]))
            return "Attendance marked successfully — signed out."

    def unknown(self, now: datetime):
        with self.connect() as connection:
            connection.execute("INSERT INTO unknown_attempts(occurred_at,date) VALUES(?,?)",
                               (now.isoformat(), now.date().isoformat()))

    def records(self, start: str, end: str, search: str = "") -> list[dict]:
        with self.connect() as connection:
            # instr treats search input literally, including SQL wildcard characters.
            rows = connection.execute(
                "SELECT employee_id,name,date,sign_in_time,sign_out_time,verification_status FROM attendance "
                "WHERE date BETWEEN ? AND ? AND (instr(lower(name),lower(?))>0 "
                "OR instr(lower(employee_id),lower(?))>0) ORDER BY date DESC,sign_in_time DESC",
                (start, end, search, search))
            return [dict(row) for row in rows]

    def metrics(self, today: str) -> dict:
        with self.connect() as connection:
            scalar = lambda sql, args=(): connection.execute(sql, args).fetchone()[0]
            return {
                "Registered people": scalar("SELECT COUNT(*) FROM users WHERE active=1"),
                "Today's attendance": scalar("SELECT COUNT(*) FROM attendance WHERE date=?", (today,)),
                "Currently signed in": scalar("SELECT COUNT(*) FROM attendance WHERE date=? AND sign_out_time IS NULL", (today,)),
                "Total sign-ins": scalar("SELECT COUNT(*) FROM attendance"),
                "Total sign-outs": scalar("SELECT COUNT(*) FROM attendance WHERE sign_out_time IS NOT NULL"),
                "Unknown attempts": scalar("SELECT COUNT(*) FROM unknown_attempts"),
            }
