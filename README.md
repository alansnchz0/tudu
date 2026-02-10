# Tudu - A Simpler Jira in Your Terminal

A TUI (Terminal User Interface) todo list application with story points for priority ordering, organized by projects. Built with Python and [Textual](https://textual.textualize.io/).

## Features

- **Interactive TUI** with vim-like keybindings for fast navigation
- **Story points** for task prioritization (auto-derived priority levels)
- **Project-based organization** — group tasks by project
- **CLI support** — add/manage tasks directly from the command line
- **Secure local storage** — SQLite database with Fernet encryption
- **Status cycling** — Todo → In Progress → Done
- **Statistics** — track completion percentage and story points per project
- **Future-ready** — designed for AI-powered prioritization integration

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Launch the Interactive TUI

```bash
python tudu.py
```

### CLI Usage

```bash
# Add a task to a project
python tudu.py --project "Tudu" --add-task "Create app" --story-points 4

# Add another task
python tudu.py -p "Tudu" -a "Write tests" -s 3

# List all tasks
python tudu.py --list

# List tasks for a specific project
python tudu.py --list --project "Tudu"

# List all projects
python tudu.py --projects

# Toggle task completion
python tudu.py --complete "Create app"

# Delete a task
python tudu.py --delete-task "Write tests"
```

## TUI Keyboard Shortcuts

### Navigation

| Key         | Action                     |
|-------------|----------------------------|
| `j` / `↓`  | Move cursor down           |
| `k` / `↑`  | Move cursor up             |
| `h` / `←`  | Focus sidebar (projects)   |
| `l` / `→`  | Focus task list            |
| `Tab`       | Switch focus between panels|

### Task Management

| Key           | Action                           |
|---------------|----------------------------------|
| `a`           | Add new task                     |
| `e`           | Edit selected task               |
| `Enter`/`Space` | Cycle task status (Todo → In Progress → Done) |
| `x`           | Toggle task done/todo            |
| `d`           | Delete selected task             |

### Project Management

| Key       | Action                |
|-----------|-----------------------|
| `Shift+P` | Add new project      |
| `Shift+D` | Delete current project|

### General

| Key   | Action          |
|-------|-----------------|
| `?`   | Show help       |
| `q`   | Quit            |
| `Esc` | Close dialog    |

## Story Points & Priority

Tasks are automatically prioritized based on their story points:

| Story Points | Priority  | Color  |
|-------------|-----------|--------|
| 13+         | Critical  | Red    |
| 8-12        | High      | Yellow |
| 5-7         | Medium    | Blue   |
| 3-4         | Low       | Green  |
| 1-2         | Trivial   | Gray   |

Tasks are sorted by priority (story points) within each project, with incomplete tasks appearing first.

## Data Storage

Tudu stores your data securely:

- **Location**: OS-appropriate data directory (`~/.local/share/tudu/` on Linux, `~/Library/Application Support/tudu/` on macOS, `%APPDATA%/tudu/` on Windows)
- **Encryption**: All task and project data is encrypted using Fernet (AES-128-CBC) with a PBKDF2-derived key
- **Key management**: Encryption keys are generated per-machine and stored with restricted file permissions (0600)

## Architecture

```
tudu.py          # Entry point (CLI + TUI dispatcher)
tudu/
├── __init__.py  # Package metadata
├── app.py       # Textual TUI application
├── cli.py       # CLI argument parsing and commands
├── models.py    # Data models (Project, Task)
└── storage.py   # Encrypted SQLite storage layer
```

## Future Roadmap

- **AI Integration**: Connect to an LLM to suggest task ordering, estimate story points, and auto-prioritize backlogs
- **Task dependencies**: Define relationships between tasks
- **Sprint planning**: Time-boxed iterations with velocity tracking
- **Export**: Export tasks to CSV/JSON
- **Team sync**: Shared project boards via encrypted cloud sync

## Dependencies

- [Textual](https://textual.textualize.io/) — Modern TUI framework
- [Rich](https://rich.readthedocs.io/) — Rich text rendering (used by Textual)
- [cryptography](https://cryptography.io/) — Fernet encryption for secure storage
- [platformdirs](https://platformdirs.readthedocs.io/) — OS-appropriate directory paths
