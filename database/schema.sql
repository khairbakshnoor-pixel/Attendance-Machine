PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    employee_id TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 100),
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1))
);
-- Biometric templates are sensitive; never return this table in normal UI/export queries.
CREATE TABLE IF NOT EXISTS biometrics (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL,
    embedding BLOB NOT NULL,
    dimensions INTEGER NOT NULL CHECK(dimensions > 0)
);
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    employee_id TEXT NOT NULL,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    sign_in_time TEXT NOT NULL,
    sign_out_time TEXT,
    verification_status TEXT NOT NULL DEFAULT 'verified' CHECK(verification_status = 'verified'),
    UNIQUE(user_id, date),
    CHECK(sign_out_time IS NULL OR sign_out_time >= sign_in_time)
);
CREATE INDEX IF NOT EXISTS attendance_date ON attendance(date);
CREATE TABLE IF NOT EXISTS unknown_attempts (
    id INTEGER PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    date TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS unknown_date ON unknown_attempts(date);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    action TEXT NOT NULL,
    employee_id TEXT NOT NULL
);
