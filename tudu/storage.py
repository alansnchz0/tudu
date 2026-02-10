"""Secure local storage for Tudu using SQLite with encryption."""

from __future__ import annotations

import base64
import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from platformdirs import user_data_dir

from tudu.models import Project, Task


def _get_data_dir() -> Path:
    """Get the OS-appropriate data directory for Tudu."""
    data_dir = Path(user_data_dir("tudu", "tudu"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _get_or_create_key(data_dir: Path) -> bytes:
    """Get or create an encryption key stored securely in the data directory.

    The key is derived from a machine-specific salt and a random master key.
    The master key file has restricted permissions (owner-only read/write).
    """
    key_file = data_dir / ".tudu_key"

    if key_file.exists():
        master_key = key_file.read_bytes()
    else:
        master_key = Fernet.generate_key()
        key_file.write_bytes(master_key)
        # Restrict permissions: owner read/write only
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            pass  # Windows may not support this

    # Derive a key using PBKDF2 for extra security
    salt_file = data_dir / ".tudu_salt"
    if salt_file.exists():
        salt = salt_file.read_bytes()
    else:
        salt = os.urandom(16)
        salt_file.write_bytes(salt)
        try:
            os.chmod(salt_file, 0o600)
        except OSError:
            pass

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(master_key))
    return derived_key


class Storage:
    """Encrypted local storage using SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize storage.

        Args:
            db_path: Optional path to the SQLite database.
                     If None, uses the OS-appropriate data directory.
        """
        if db_path:
            self._db_path = Path(db_path)
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            data_dir = self._db_path.parent
        else:
            data_dir = _get_data_dir()
            self._db_path = data_dir / "tudu.db"

        self._key = _get_or_create_key(data_dir)
        self._fernet = Fernet(self._key)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    data BLOB NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    data BLOB NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_project
                ON tasks(project_id)
            """)

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        return sqlite3.connect(str(self._db_path))

    def _encrypt(self, data: dict) -> bytes:
        """Encrypt a dictionary to bytes."""
        json_bytes = json.dumps(data).encode("utf-8")
        return self._fernet.encrypt(json_bytes)

    def _decrypt(self, data: bytes) -> dict:
        """Decrypt bytes to a dictionary."""
        json_bytes = self._fernet.decrypt(data)
        return json.loads(json_bytes.decode("utf-8"))

    # ── Project Operations ──────────────────────────────────────────

    def save_project(self, project: Project) -> Project:
        """Save or update a project."""
        encrypted = self._encrypt(project.to_dict())
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO projects (id, data) VALUES (?, ?)",
                (project.id, encrypted),
            )
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row is None:
            return None
        return Project.from_dict(self._decrypt(row[0]))

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get a project by name (case-insensitive)."""
        projects = self.list_projects()
        for project in projects:
            if project.name.lower() == name.lower():
                return project
        return None

    def list_projects(self) -> list[Project]:
        """List all projects."""
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM projects").fetchall()
        return [Project.from_dict(self._decrypt(row[0])) for row in rows]

    def delete_project(self, project_id: str) -> None:
        """Delete a project and all its tasks."""
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    def get_or_create_project(self, name: str) -> Project:
        """Get a project by name or create it if it doesn't exist."""
        project = self.get_project_by_name(name)
        if project is None:
            project = Project(name=name)
            self.save_project(project)
        return project

    # ── Task Operations ─────────────────────────────────────────────

    def save_task(self, task: Task) -> Task:
        """Save or update a task."""
        encrypted = self._encrypt(task.to_dict())
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO tasks (id, project_id, data) VALUES (?, ?, ?)",
                (task.id, task.project_id, encrypted),
            )
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        if row is None:
            return None
        return Task.from_dict(self._decrypt(row[0]))

    def list_tasks(
        self,
        project_id: Optional[str] = None,
        sort_by_points: bool = True,
    ) -> list[Task]:
        """List tasks, optionally filtered by project.

        Args:
            project_id: If set, only return tasks for this project.
            sort_by_points: If True, sort by story points (descending).
        """
        with self._connect() as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT data FROM tasks WHERE project_id = ?", (project_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT data FROM tasks").fetchall()

        tasks = [Task.from_dict(self._decrypt(row[0])) for row in rows]

        if sort_by_points:
            # Sort by: incomplete first, then by story points (high to low), then position
            tasks.sort(
                key=lambda t: (
                    t.is_complete,         # Incomplete tasks first
                    -t.story_points,       # Higher points first
                    t.position,            # Then by manual position
                    t.created_at,          # Then by creation date
                )
            )
        return tasks

    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_next_position(self, project_id: str) -> int:
        """Get the next position number for a task in a project."""
        tasks = self.list_tasks(project_id=project_id, sort_by_points=False)
        if not tasks:
            return 0
        return max(t.position for t in tasks) + 1

    # ── Statistics ──────────────────────────────────────────────────

    def get_project_stats(self, project_id: str) -> dict:
        """Get statistics for a project."""
        tasks = self.list_tasks(project_id=project_id, sort_by_points=False)
        total = len(tasks)
        done = sum(1 for t in tasks if t.status.value == "done")
        in_progress = sum(1 for t in tasks if t.status.value == "in_progress")
        total_points = sum(t.story_points for t in tasks)
        done_points = sum(t.story_points for t in tasks if t.status.value == "done")

        return {
            "total_tasks": total,
            "done_tasks": done,
            "in_progress_tasks": in_progress,
            "todo_tasks": total - done - in_progress,
            "total_points": total_points,
            "done_points": done_points,
            "completion_pct": (done_points / total_points * 100) if total_points else 0,
        }
