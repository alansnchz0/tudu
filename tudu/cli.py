"""CLI interface for Tudu - manage tasks from the command line."""

from __future__ import annotations

import argparse
import sys

from tudu.models import Task, TaskStatus
from tudu.storage import Storage


def _get_status_icon(status: TaskStatus) -> str:
    """Get a simple text icon for a status."""
    return status.icon


def cmd_add_task(args: argparse.Namespace) -> None:
    """Add a new task to a project."""
    storage = Storage()
    project = storage.get_or_create_project(args.project)
    position = storage.get_next_position(project.id)
    task = Task(
        title=args.add_task,
        project_id=project.id,
        story_points=args.story_points,
        description=args.description or "",
        position=position,
    )
    storage.save_task(task)
    print(f"Task added to project '{project.name}':")
    print(f"  {task.priority.display} | SP:{task.story_points} | {task.title}")


def cmd_list_tasks(args: argparse.Namespace) -> None:
    """List tasks, optionally filtered by project."""
    storage = Storage()

    if args.project:
        project = storage.get_project_by_name(args.project)
        if not project:
            print(f"Project '{args.project}' not found.")
            sys.exit(1)
        tasks = storage.list_tasks(project_id=project.id)
        print(f"\n  Project: {project.name}")
        print(f"  {'─' * 50}")
    else:
        tasks = storage.list_tasks()
        print(f"\n  All Tasks")
        print(f"  {'─' * 50}")

    if not tasks:
        print("  No tasks found.")
        return

    for task in tasks:
        icon = _get_status_icon(task.status)
        print(f"  {icon} SP:{task.story_points:<3} {task.title}")

    # Show summary
    total_points = sum(t.story_points for t in tasks)
    done_points = sum(t.story_points for t in tasks if t.status == TaskStatus.DONE)
    print(f"  {'─' * 50}")
    print(f"  {len(tasks)} tasks | {done_points}/{total_points} story points done")
    print()


def cmd_list_projects(args: argparse.Namespace) -> None:
    """List all projects."""
    storage = Storage()
    projects = storage.list_projects()

    if not projects:
        print("  No projects found. Add a task to create one.")
        return

    print(f"\n  Projects")
    print(f"  {'─' * 50}")
    for project in projects:
        stats = storage.get_project_stats(project.id)
        pct = stats["completion_pct"]
        print(
            f"  {project.name:<20} "
            f"{stats['done_tasks']}/{stats['total_tasks']} tasks | "
            f"{stats['done_points']}/{stats['total_points']} SP | "
            f"{pct:.0f}%"
        )
    print()


def cmd_complete_task(args: argparse.Namespace) -> None:
    """Mark a task as done by searching its title."""
    storage = Storage()
    tasks = storage.list_tasks(sort_by_points=False)
    query = args.complete.lower()
    matches = [t for t in tasks if query in t.title.lower()]

    if not matches:
        print(f"No tasks matching '{args.complete}' found.")
        sys.exit(1)

    if len(matches) > 1:
        print(f"Multiple tasks match '{args.complete}':")
        for i, t in enumerate(matches, 1):
            print(f"  {i}. {t.title}")
        print("Please be more specific.")
        sys.exit(1)

    task = matches[0]
    task.toggle_status()
    storage.save_task(task)
    icon = _get_status_icon(task.status)
    print(f"  {icon} {task.title} -> {task.status.display}")


def cmd_delete_task(args: argparse.Namespace) -> None:
    """Delete a task by searching its title."""
    storage = Storage()
    tasks = storage.list_tasks(sort_by_points=False)
    query = args.delete_task.lower()
    matches = [t for t in tasks if query in t.title.lower()]

    if not matches:
        print(f"No tasks matching '{args.delete_task}' found.")
        sys.exit(1)

    if len(matches) > 1:
        print(f"Multiple tasks match '{args.delete_task}':")
        for i, t in enumerate(matches, 1):
            print(f"  {i}. {t.title}")
        print("Please be more specific.")
        sys.exit(1)

    task = matches[0]
    storage.delete_task(task.id)
    print(f"  Deleted: {task.title}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="tudu",
        description="Tudu - A simple TUI todo list with story points.",
        epilog="Run without arguments to launch the interactive TUI.",
    )

    # Task management flags
    parser.add_argument(
        "--project", "-p",
        type=str,
        help="Project name (used with --add-task or --list)",
    )
    parser.add_argument(
        "--add-task", "-a",
        type=str,
        help="Add a new task with the given title",
    )
    parser.add_argument(
        "--story-points", "-s",
        type=int,
        default=1,
        help="Story points for the task (default: 1)",
    )
    parser.add_argument(
        "--description", "-d",
        type=str,
        help="Task description",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List tasks (use --project to filter)",
    )
    parser.add_argument(
        "--projects",
        action="store_true",
        help="List all projects",
    )
    parser.add_argument(
        "--complete", "-c",
        type=str,
        help="Toggle completion of a task (search by title)",
    )
    parser.add_argument(
        "--delete-task",
        type=str,
        help="Delete a task (search by title)",
    )

    return parser


def run_cli() -> bool:
    """Run the CLI. Returns True if a CLI command was executed, False otherwise.

    If no CLI arguments are provided, returns False so the TUI can launch.
    """
    parser = build_parser()
    args = parser.parse_args()

    # If no specific CLI action, return False to launch TUI
    has_action = any([
        args.add_task,
        args.list,
        args.projects,
        args.complete,
        args.delete_task,
    ])

    if not has_action:
        return False

    # Dispatch to the right command
    if args.add_task:
        if not args.project:
            print("Error: --project is required when adding a task.")
            sys.exit(1)
        cmd_add_task(args)
    elif args.list:
        cmd_list_tasks(args)
    elif args.projects:
        cmd_list_projects(args)
    elif args.complete:
        cmd_complete_task(args)
    elif args.delete_task:
        cmd_delete_task(args)

    return True
