import sqlite3
import os
from datetime import datetime, timedelta

DB_DIR = os.path.expanduser("~/.local/share/task_sidebar")
DB_PATH = os.path.join(DB_DIR, "tasks.db")

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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
                notes        TEXT DEFAULT '',
                done         INTEGER DEFAULT 0,
                completed_at TEXT,
                archived     INTEGER DEFAULT 0,
                created_at   TEXT NOT NULL
            )
        """)


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


def add_task(title, due_date, priority, notes):
    with _conn() as c:
        c.execute(
            "INSERT INTO tasks (title, due_date, priority, notes, created_at) VALUES (?,?,?,?,?)",
            (title, due_date or None, priority, notes, datetime.now().isoformat()),
        )


def update_task(task_id, title, due_date, priority, notes):
    with _conn() as c:
        c.execute(
            "UPDATE tasks SET title=?, due_date=?, priority=?, notes=? WHERE id=?",
            (title, due_date or None, priority, notes, task_id),
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
