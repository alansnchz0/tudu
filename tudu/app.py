"""Tudu TUI Application built with Textual."""

from __future__ import annotations

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Rule,
    Select,
    Static,
)

from tudu.models import Priority, Project, Task, TaskStatus
from tudu.storage import Storage


# ── Styles ──────────────────────────────────────────────────────────────

APP_CSS = """
Screen {
    background: $surface;
}

#main-container {
    layout: horizontal;
    height: 1fr;
}

#sidebar {
    width: 30;
    min-width: 25;
    background: $panel;
    border-right: tall $primary-background;
    padding: 1;
}

#sidebar-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    padding-bottom: 1;
}

#project-list {
    height: 1fr;
}

#project-list > ListItem {
    padding: 0 1;
}

#project-list > ListItem.--highlight {
    background: $accent 30%;
}

.project-item {
    height: 3;
    padding: 0 1;
    content-align-vertical: middle;
}

.project-item-selected {
    background: $accent 20%;
    text-style: bold;
}

.project-stats {
    color: $text-muted;
    text-style: italic;
}

#task-panel {
    width: 1fr;
    padding: 1 2;
}

#task-header {
    height: auto;
    padding-bottom: 1;
}

#task-title {
    text-style: bold;
    color: $accent;
}

#task-stats {
    color: $text-muted;
    dock: right;
}

#task-list-scroll {
    height: 1fr;
}

#task-list {
    height: auto;
}

.task-row {
    height: 3;
    padding: 0 1;
    margin-bottom: 0;
    layout: horizontal;
}

.task-row:hover {
    background: $accent 10%;
}

.task-row-selected {
    background: $accent 20%;
    border-left: thick $accent;
}

.task-status-icon {
    width: 5;
    content-align-vertical: middle;
}

.task-sp-badge {
    width: 6;
    content-align-vertical: middle;
    content-align: center middle;
    text-style: bold;
}

.sp-critical { color: #e06c75; }
.sp-high { color: #e5c07b; }
.sp-medium { color: #61afef; }
.sp-low { color: #98c379; }
.sp-trivial { color: $text-muted; }

.task-title-text {
    width: 1fr;
    content-align-vertical: middle;
    padding-left: 1;
}

.task-title-done {
    text-style: strike italic;
    color: $text-muted;
}

.task-priority-label {
    width: 10;
    content-align-vertical: middle;
    content-align: right middle;
}

.priority-critical { color: #e06c75; text-style: bold; }
.priority-high { color: #e5c07b; }
.priority-medium { color: #61afef; }
.priority-low { color: #98c379; }
.priority-trivial { color: $text-muted; }

#empty-state {
    width: 1fr;
    height: 1fr;
    content-align: center middle;
    color: $text-muted;
    text-style: italic;
}

/* ── Modal Screens ─────────────────────────────────────── */

.modal-dialog {
    width: 60;
    max-width: 80%;
    height: auto;
    max-height: 80%;
    background: $panel;
    border: tall $accent;
    padding: 1 2;
    margin: 4 8;
    align: center middle;
}

.modal-title {
    text-style: bold;
    color: $accent;
    padding-bottom: 1;
    text-align: center;
}

.modal-field {
    margin-bottom: 1;
}

.modal-field-label {
    color: $text;
    padding-bottom: 0;
    text-style: bold;
}

.modal-buttons {
    layout: horizontal;
    height: auto;
    align: center middle;
    padding-top: 1;
}

.modal-buttons Button {
    margin: 0 1;
}

/* Help Screen */

#help-container {
    width: 70;
    height: auto;
    max-height: 90%;
    background: $panel;
    border: tall $accent;
    padding: 2 3;
    align: center middle;
    margin: 2;
}

#help-title {
    text-style: bold;
    color: $accent;
    text-align: center;
    padding-bottom: 1;
}

.help-section {
    padding-bottom: 1;
}

.help-section-title {
    text-style: bold underline;
    color: $accent;
    padding-bottom: 0;
}

.help-key {
    color: #e5c07b;
    text-style: bold;
}

.help-desc {
    color: $text;
}
"""


# ── Modal Screens ───────────────────────────────────────────────────────

class AddTaskScreen(ModalScreen[Task | None]):
    """Modal screen for adding a new task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("Add New Task", classes="modal-title")

            yield Label("Title:", classes="modal-field-label")
            yield Input(
                placeholder="Task title...",
                id="task-title-input",
                classes="modal-field",
            )

            yield Label("Story Points:", classes="modal-field-label")
            yield Input(
                placeholder="1",
                id="task-sp-input",
                classes="modal-field",
                type="integer",
            )

            yield Label("Description:", classes="modal-field-label")
            yield Input(
                placeholder="Optional description...",
                id="task-desc-input",
                classes="modal-field",
            )

            with Horizontal(classes="modal-buttons"):
                yield Button("Add [Enter]", variant="primary", id="btn-add")
                yield Button("Cancel [Esc]", variant="default", id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#task-title-input", Input).focus()

    @on(Button.Pressed, "#btn-add")
    def on_add(self) -> None:
        self._submit_task()

    @on(Button.Pressed, "#btn-cancel")
    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Input.Submitted, "#task-title-input")
    def on_title_submit(self) -> None:
        self.query_one("#task-sp-input", Input).focus()

    @on(Input.Submitted, "#task-sp-input")
    def on_sp_submit(self) -> None:
        self.query_one("#task-desc-input", Input).focus()

    @on(Input.Submitted, "#task-desc-input")
    def on_desc_submit(self) -> None:
        self._submit_task()

    def _submit_task(self) -> None:
        title = self.query_one("#task-title-input", Input).value.strip()
        if not title:
            self.notify("Title is required!", severity="error")
            return

        sp_text = self.query_one("#task-sp-input", Input).value.strip()
        try:
            story_points = int(sp_text) if sp_text else 1
        except ValueError:
            story_points = 1

        description = self.query_one("#task-desc-input", Input).value.strip()

        task = Task(
            title=title,
            project_id=self.project.id,
            story_points=max(1, story_points),
            description=description,
        )
        self.dismiss(task)


class AddProjectScreen(ModalScreen[Project | None]):
    """Modal screen for adding a new project."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("New Project", classes="modal-title")

            yield Label("Name:", classes="modal-field-label")
            yield Input(
                placeholder="Project name...",
                id="project-name-input",
                classes="modal-field",
            )

            yield Label("Description:", classes="modal-field-label")
            yield Input(
                placeholder="Optional description...",
                id="project-desc-input",
                classes="modal-field",
            )

            with Horizontal(classes="modal-buttons"):
                yield Button("Create [Enter]", variant="primary", id="btn-create")
                yield Button("Cancel [Esc]", variant="default", id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#project-name-input", Input).focus()

    @on(Button.Pressed, "#btn-create")
    def on_create(self) -> None:
        self._submit_project()

    @on(Button.Pressed, "#btn-cancel")
    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Input.Submitted, "#project-name-input")
    def on_name_submit(self) -> None:
        self.query_one("#project-desc-input", Input).focus()

    @on(Input.Submitted, "#project-desc-input")
    def on_desc_submit(self) -> None:
        self._submit_project()

    def _submit_project(self) -> None:
        name = self.query_one("#project-name-input", Input).value.strip()
        if not name:
            self.notify("Project name is required!", severity="error")
            return

        description = self.query_one("#project-desc-input", Input).value.strip()
        project = Project(name=name, description=description)
        self.dismiss(project)


class EditTaskScreen(ModalScreen[Task | None]):
    """Modal screen for editing an existing task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.task = task

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("Edit Task", classes="modal-title")

            yield Label("Title:", classes="modal-field-label")
            yield Input(
                value=self.task.title,
                id="task-title-input",
                classes="modal-field",
            )

            yield Label("Story Points:", classes="modal-field-label")
            yield Input(
                value=str(self.task.story_points),
                id="task-sp-input",
                classes="modal-field",
                type="integer",
            )

            yield Label("Description:", classes="modal-field-label")
            yield Input(
                value=self.task.description,
                id="task-desc-input",
                classes="modal-field",
            )

            yield Label("Status:", classes="modal-field-label")
            yield Select(
                [(s.display, s.value) for s in TaskStatus],
                value=self.task.status.value,
                id="task-status-select",
                classes="modal-field",
            )

            with Horizontal(classes="modal-buttons"):
                yield Button("Save [Enter]", variant="primary", id="btn-save")
                yield Button("Cancel [Esc]", variant="default", id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#task-title-input", Input).focus()

    @on(Button.Pressed, "#btn-save")
    def on_save(self) -> None:
        self._submit_task()

    @on(Button.Pressed, "#btn-cancel")
    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Input.Submitted)
    def on_submit(self) -> None:
        self._submit_task()

    def _submit_task(self) -> None:
        title = self.query_one("#task-title-input", Input).value.strip()
        if not title:
            self.notify("Title is required!", severity="error")
            return

        sp_text = self.query_one("#task-sp-input", Input).value.strip()
        try:
            story_points = int(sp_text) if sp_text else self.task.story_points
        except ValueError:
            story_points = self.task.story_points

        description = self.query_one("#task-desc-input", Input).value.strip()
        status_val = self.query_one("#task-status-select", Select).value

        self.task.title = title
        self.task.story_points = max(1, story_points)
        self.task.description = description
        if status_val and status_val != Select.BLANK:
            self.task.status = TaskStatus(status_val)

        self.dismiss(self.task)


class HelpScreen(ModalScreen):
    """Modal screen showing keyboard shortcuts help."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("question_mark", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-container"):
            yield Label("Tudu - Keyboard Shortcuts", id="help-title")
            yield Rule()

            with Vertical(classes="help-section"):
                yield Label("Navigation", classes="help-section-title")
                yield Label("  j / Down      Move cursor down")
                yield Label("  k / Up        Move cursor up")
                yield Label("  h / Left      Focus sidebar (projects)")
                yield Label("  l / Right     Focus task list")
                yield Label("  Tab           Switch focus between panels")

            with Vertical(classes="help-section"):
                yield Label("Task Management", classes="help-section-title")
                yield Label("  a             Add new task")
                yield Label("  e             Edit selected task")
                yield Label("  Enter/Space   Toggle task status (cycle)")
                yield Label("  x             Mark task done / toggle")
                yield Label("  d             Delete selected task")

            with Vertical(classes="help-section"):
                yield Label("Project Management", classes="help-section-title")
                yield Label("  P             Add new project")
                yield Label("  D             Delete selected project")

            with Vertical(classes="help-section"):
                yield Label("General", classes="help-section-title")
                yield Label("  ?             Show this help")
                yield Label("  q             Quit")
                yield Label("  Esc           Close dialog / Cancel")

            yield Rule()
            yield Label("  Press Esc or ? to close", classes="help-desc")


class ConfirmScreen(ModalScreen[bool]):
    """Simple confirmation dialog."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("Confirm", classes="modal-title")
            yield Label(self._message)
            with Horizontal(classes="modal-buttons"):
                yield Button("Yes [y]", variant="error", id="btn-yes")
                yield Button("No [n]", variant="default", id="btn-no")

    @on(Button.Pressed, "#btn-yes")
    def action_confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-no")
    def action_cancel(self) -> None:
        self.dismiss(False)


# ── Task Row Widget ─────────────────────────────────────────────────────

class TaskRow(Widget):
    """A single task row in the task list."""

    DEFAULT_CSS = """
    TaskRow {
        height: 3;
        layout: horizontal;
        padding: 0 1;
    }
    TaskRow:hover {
        background: $accent 10%;
    }
    TaskRow.selected {
        background: $accent 20%;
        border-left: thick $accent;
    }
    """

    selected = reactive(False)

    class Selected(Message):
        def __init__(self, task: Task) -> None:
            super().__init__()
            self.task = task

    def __init__(self, task: Task, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task = task

    def compose(self) -> ComposeResult:
        icon = self.task.status.icon
        sp = self.task.story_points
        priority = self.task.priority

        sp_class = f"sp-{priority.value}"
        priority_class = f"priority-{priority.value}"

        title_class = "task-title-text"
        if self.task.is_complete:
            title_class += " task-title-done"

        yield Static(icon, classes="task-status-icon")
        yield Static(f"[{sp}]", classes=f"task-sp-badge {sp_class}")
        yield Static(self.task.title, classes=title_class)
        yield Static(priority.display, classes=f"task-priority-label {priority_class}")

    def watch_selected(self, value: bool) -> None:
        self.set_class(value, "selected")

    def on_click(self) -> None:
        self.post_message(self.Selected(self.task))


# ── Main Application ───────────────────────────────────────────────────

class TuduApp(App):
    """Tudu - A simpler Jira in your terminal."""

    TITLE = "Tudu"
    SUB_TITLE = "Task Manager"
    CSS = APP_CSS

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("question_mark", "show_help", "Help", show=True, key_display="?"),
        Binding("a", "add_task", "Add Task", show=True),
        Binding("e", "edit_task", "Edit", show=True),
        Binding("x", "toggle_task", "Toggle Done", show=True),
        Binding("d", "delete_task", "Delete", show=True),
        Binding("P", "add_project", "New Project", show=True, key_display="Shift+P"),
        Binding("D", "delete_project", "Del Project", show=True, key_display="Shift+D"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "focus_sidebar", "Sidebar", show=False),
        Binding("l", "focus_tasks", "Tasks", show=False),
        Binding("enter", "cycle_task", "Cycle Status", show=False),
        Binding("space", "cycle_task", "Cycle Status", show=False),
        Binding("tab", "switch_focus", "Switch Panel", show=False),
    ]

    current_project_idx = reactive(0)
    current_task_idx = reactive(0)
    focus_on_tasks = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.storage = Storage()
        self._projects: list[Project] = []
        self._tasks: list[Task] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield Label("Projects", id="sidebar-title")
                yield ListView(id="project-list")
            with Vertical(id="task-panel"):
                with Horizontal(id="task-header"):
                    yield Label("Tasks", id="task-title")
                    yield Label("", id="task-stats")
                yield VerticalScroll(id="task-list-scroll")
        yield Footer()

    def on_mount(self) -> None:
        self._load_data()

    def _load_data(self) -> None:
        """Load projects and tasks from storage."""
        self._projects = self.storage.list_projects()
        self._refresh_project_list()
        self._load_tasks()

    def _refresh_project_list(self) -> None:
        """Refresh the project sidebar."""
        project_list = self.query_one("#project-list", ListView)
        project_list.clear()

        if not self._projects:
            project_list.append(ListItem(Label("  No projects yet"), id="no-projects"))
            return

        for i, project in enumerate(self._projects):
            stats = self.storage.get_project_stats(project.id)
            pct = stats["completion_pct"]
            label_text = f"{project.name}\n  {stats['done_tasks']}/{stats['total_tasks']} tasks  {pct:.0f}%"
            item = ListItem(Label(label_text), id=f"project-{i}")
            project_list.append(item)

        # Ensure valid index
        if self.current_project_idx >= len(self._projects):
            self.current_project_idx = max(0, len(self._projects) - 1)

        if self._projects:
            project_list.index = self.current_project_idx

    def _load_tasks(self) -> None:
        """Load tasks for the currently selected project."""
        scroll = self.query_one("#task-list-scroll", VerticalScroll)
        # Remove old task rows
        for child in list(scroll.children):
            child.remove()

        if not self._projects:
            self._tasks = []
            self._update_task_header()
            scroll.mount(
                Static("No projects yet. Press Shift+P to create one.", id="empty-state")
            )
            return

        project = self._projects[self.current_project_idx]
        self._tasks = self.storage.list_tasks(project_id=project.id)

        self._update_task_header()

        if not self._tasks:
            scroll.mount(
                Static("No tasks yet. Press 'a' to add one.", id="empty-state")
            )
            return

        for i, task in enumerate(self._tasks):
            row = TaskRow(task, id=f"task-{i}")
            if i == self.current_task_idx:
                row.selected = True
            scroll.mount(row)

        # Ensure valid index
        if self.current_task_idx >= len(self._tasks):
            self.current_task_idx = max(0, len(self._tasks) - 1)

    def _update_task_header(self) -> None:
        """Update the task panel header with project name and stats."""
        title_label = self.query_one("#task-title", Label)
        stats_label = self.query_one("#task-stats", Label)

        if not self._projects:
            title_label.update("Tasks")
            stats_label.update("")
            return

        project = self._projects[self.current_project_idx]
        stats = self.storage.get_project_stats(project.id)
        title_label.update(f"Tasks - {project.name}")
        stats_label.update(
            f"{stats['done_points']}/{stats['total_points']} SP | "
            f"{stats['completion_pct']:.0f}% done"
        )

    def _update_selection(self) -> None:
        """Update the visual selection of task rows."""
        scroll = self.query_one("#task-list-scroll", VerticalScroll)
        for i, child in enumerate(scroll.children):
            if isinstance(child, TaskRow):
                child.selected = i == self.current_task_idx

    # ── Event Handlers ──────────────────────────────────────────────

    @on(ListView.Selected, "#project-list")
    def on_project_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.id and event.item.id.startswith("project-"):
            idx = int(event.item.id.split("-")[1])
            if idx != self.current_project_idx:
                self.current_project_idx = idx
                self.current_task_idx = 0
                self._load_tasks()

    @on(TaskRow.Selected)
    def on_task_row_selected(self, event: TaskRow.Selected) -> None:
        # Find the index of this task
        for i, task in enumerate(self._tasks):
            if task.id == event.task.id:
                self.current_task_idx = i
                self._update_selection()
                break

    # ── Actions (vim-like keybindings) ──────────────────────────────

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_cursor_down(self) -> None:
        if self.focus_on_tasks and self._tasks:
            self.current_task_idx = min(
                self.current_task_idx + 1, len(self._tasks) - 1
            )
            self._update_selection()
        elif not self.focus_on_tasks and self._projects:
            project_list = self.query_one("#project-list", ListView)
            if project_list.index is not None and project_list.index < len(self._projects) - 1:
                project_list.index += 1

    def action_cursor_up(self) -> None:
        if self.focus_on_tasks and self._tasks:
            self.current_task_idx = max(self.current_task_idx - 1, 0)
            self._update_selection()
        elif not self.focus_on_tasks:
            project_list = self.query_one("#project-list", ListView)
            if project_list.index is not None and project_list.index > 0:
                project_list.index -= 1

    def action_focus_sidebar(self) -> None:
        self.focus_on_tasks = False
        self.query_one("#project-list", ListView).focus()

    def action_focus_tasks(self) -> None:
        self.focus_on_tasks = True
        try:
            scroll = self.query_one("#task-list-scroll", VerticalScroll)
            scroll.focus()
        except NoMatches:
            pass

    def action_switch_focus(self) -> None:
        if self.focus_on_tasks:
            self.action_focus_sidebar()
        else:
            self.action_focus_tasks()

    def action_add_task(self) -> None:
        if not self._projects:
            self.notify("Create a project first (Shift+P)", severity="warning")
            return

        project = self._projects[self.current_project_idx]

        def on_result(task: Task | None) -> None:
            if task is not None:
                task.position = self.storage.get_next_position(project.id)
                self.storage.save_task(task)
                self._load_tasks()
                self._refresh_project_list()
                self.notify(f"Task '{task.title}' added!")

        self.push_screen(AddTaskScreen(project), on_result)

    def action_edit_task(self) -> None:
        if not self._tasks:
            return

        task = self._tasks[self.current_task_idx]

        def on_result(edited_task: Task | None) -> None:
            if edited_task is not None:
                self.storage.save_task(edited_task)
                self._load_tasks()
                self._refresh_project_list()
                self.notify(f"Task '{edited_task.title}' updated!")

        self.push_screen(EditTaskScreen(task), on_result)

    def action_toggle_task(self) -> None:
        if not self._tasks:
            return

        task = self._tasks[self.current_task_idx]
        task.toggle_status()
        self.storage.save_task(task)
        self._load_tasks()
        self._refresh_project_list()

    def action_cycle_task(self) -> None:
        if not self._tasks:
            return

        task = self._tasks[self.current_task_idx]
        task.cycle_status()
        self.storage.save_task(task)
        self._load_tasks()
        self._refresh_project_list()
        self.notify(f"'{task.title}' -> {task.status.display}")

    def action_delete_task(self) -> None:
        if not self._tasks:
            return

        task = self._tasks[self.current_task_idx]

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self.storage.delete_task(task.id)
                self._load_tasks()
                self._refresh_project_list()
                self.notify(f"Task '{task.title}' deleted.")

        self.push_screen(
            ConfirmScreen(f"Delete task '{task.title}'?"), on_confirm
        )

    def action_add_project(self) -> None:
        def on_result(project: Project | None) -> None:
            if project is not None:
                self.storage.save_project(project)
                self._load_data()
                self.current_project_idx = len(self._projects) - 1
                self._load_tasks()
                self.notify(f"Project '{project.name}' created!")

        self.push_screen(AddProjectScreen(), on_result)

    def action_delete_project(self) -> None:
        if not self._projects:
            return

        project = self._projects[self.current_project_idx]

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self.storage.delete_project(project.id)
                self.current_project_idx = 0
                self._load_data()
                self.notify(f"Project '{project.name}' deleted.")

        self.push_screen(
            ConfirmScreen(
                f"Delete project '{project.name}' and all its tasks?"
            ),
            on_confirm,
        )


def run_tui() -> None:
    """Launch the Tudu TUI application."""
    app = TuduApp()
    app.run()
