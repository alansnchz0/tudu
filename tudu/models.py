"""Data models for Tudu - Projects and Tasks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    """Status of a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value

    @property
    def display(self) -> str:
        """Human-readable display name."""
        return {
            TaskStatus.TODO: "To Do",
            TaskStatus.IN_PROGRESS: "In Progress",
            TaskStatus.DONE: "Done",
            TaskStatus.CANCELLED: "Cancelled",
        }[self]

    @property
    def icon(self) -> str:
        """Icon for the status."""
        return {
            TaskStatus.TODO: "[ ]",
            TaskStatus.IN_PROGRESS: "[~]",
            TaskStatus.DONE: "[x]",
            TaskStatus.CANCELLED: "[-]",
        }[self]


class Priority(str, Enum):
    """Priority levels derived from story points."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"

    def __str__(self) -> str:
        return self.value

    @property
    def display(self) -> str:
        return self.value.capitalize()

    @staticmethod
    def from_story_points(points: int) -> Priority:
        """Derive priority from story points."""
        if points >= 13:
            return Priority.CRITICAL
        elif points >= 8:
            return Priority.HIGH
        elif points >= 5:
            return Priority.MEDIUM
        elif points >= 3:
            return Priority.LOW
        else:
            return Priority.TRIVIAL


@dataclass
class Task:
    """A single task/todo item."""

    title: str
    project_id: str
    story_points: int = 1
    status: TaskStatus = TaskStatus.TODO
    description: str = ""
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    position: int = 0  # For manual ordering within a project

    @property
    def priority(self) -> Priority:
        """Get priority based on story points."""
        return Priority.from_story_points(self.story_points)

    @property
    def is_complete(self) -> bool:
        return self.status in (TaskStatus.DONE, TaskStatus.CANCELLED)

    def toggle_status(self) -> None:
        """Toggle between TODO and DONE."""
        if self.status == TaskStatus.DONE:
            self.status = TaskStatus.TODO
            self.completed_at = None
        else:
            self.status = TaskStatus.DONE
            self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def cycle_status(self) -> None:
        """Cycle through statuses: TODO -> IN_PROGRESS -> DONE -> TODO."""
        cycle = {
            TaskStatus.TODO: TaskStatus.IN_PROGRESS,
            TaskStatus.IN_PROGRESS: TaskStatus.DONE,
            TaskStatus.DONE: TaskStatus.TODO,
            TaskStatus.CANCELLED: TaskStatus.TODO,
        }
        self.status = cycle[self.status]
        if self.status == TaskStatus.DONE:
            self.completed_at = datetime.now().isoformat()
        else:
            self.completed_at = None
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "project_id": self.project_id,
            "story_points": self.story_points,
            "status": self.status.value,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            project_id=data["project_id"],
            story_points=data.get("story_points", 1),
            status=TaskStatus(data.get("status", "todo")),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            position=data.get("position", 0),
        )


@dataclass
class Project:
    """A project that contains tasks."""

    name: str
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    color: str = "#61afef"  # Default blue color for TUI display

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            color=data.get("color", "#61afef"),
        )
