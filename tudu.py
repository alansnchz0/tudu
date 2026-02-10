#!/usr/bin/env python3
"""Tudu - A simple TUI todo list with story points.

A simpler Jira in your terminal. Manage tasks with story points,
organize by project, and use vim-like keybindings for fast navigation.

Usage:
    # Launch interactive TUI
    python tudu.py

    # Add a task via CLI
    python tudu.py --project "Tudu" --add-task "Create app" --story-points 4

    # List tasks
    python tudu.py --list
    python tudu.py --list --project "Tudu"

    # List projects
    python tudu.py --projects

    # Complete a task
    python tudu.py --complete "Create app"

    # Delete a task
    python tudu.py --delete-task "Create app"
"""

from tudu.cli import run_cli
from tudu.app import run_tui


def main() -> None:
    """Main entry point: run CLI if arguments given, otherwise launch TUI."""
    if not run_cli():
        run_tui()


if __name__ == "__main__":
    main()
