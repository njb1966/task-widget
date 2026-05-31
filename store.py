import sqlite3
import os
from datetime import datetime, timedelta

DB_DIR = os.path.expanduser("~/.local/share/task_sidebar")
DB_PATH = os.path.join(DB_DIR, "tasks.db")

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TASK_TYPES = ("personal", "project")
SORT_PREFERENCES = ("date", "priority", "type")


def _conn():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                due_date     TEXT,
                priority     TEXT DEFAULT 'medium',
                task_type    TEXT DEFAULT 'personal',
                notes        TEXT DEFAULT '',
                done         INTEGER DEFAULT 0,
                completed_at TEXT,
                archived     INTEGER DEFAULT 0,
                created_at   TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        _ensure_column(c, "tasks", "task_type", "TEXT DEFAULT 'personal'")


def _ensure_column(conn, table, column, definition):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {row[1] for row in rows}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def auto_archive():
    cutoff = (datetime.now() - timedelta(days=14)).isoformat()
    with _conn() as c:
        c.execute(
            "UPDATE tasks SET archived=1 WHERE done=1 AND completed_at IS NOT NULL AND completed_at < ?",
            (cutoff,),
        )


def get_tasks():
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM tasks WHERE archived=0 ORDER BY done ASC, due_date ASC, created_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_sort_preference():
    with _conn() as c:
        row = c.execute(
            "SELECT value FROM settings WHERE key='sort_preference'"
        ).fetchone()
    if row and row[0] in SORT_PREFERENCES:
        return row[0]
    return "date"


def set_sort_preference(preference):
    if preference not in SORT_PREFERENCES:
        preference = "date"
    with _conn() as c:
        c.execute(
            "INSERT INTO settings (key, value) VALUES ('sort_preference', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (preference,),
        )


def normalize_task_type(task_type):
    return task_type if task_type in TASK_TYPES else "personal"


def add_task(title, due_date, priority, task_type, notes):
    with _conn() as c:
        c.execute(
            "INSERT INTO tasks (title, due_date, priority, task_type, notes, created_at) VALUES (?,?,?,?,?,?)",
            (
                title,
                due_date or None,
                priority,
                normalize_task_type(task_type),
                notes,
                datetime.now().isoformat(),
            ),
        )


def update_task(task_id, title, due_date, priority, task_type, notes):
    with _conn() as c:
        c.execute(
            "UPDATE tasks SET title=?, due_date=?, priority=?, task_type=?, notes=? WHERE id=?",
            (
                title,
                due_date or None,
                priority,
                normalize_task_type(task_type),
                notes,
                task_id,
            ),
        )


def mark_done(task_id, done):
    with _conn() as c:
        if done:
            c.execute(
                "UPDATE tasks SET done=1, completed_at=? WHERE id=?",
                (datetime.now().isoformat(), task_id),
            )
        else:
            c.execute(
                "UPDATE tasks SET done=0, completed_at=NULL WHERE id=?",
                (task_id,),
            )


def delete_task(task_id):
    with _conn() as c:
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
