# Rich Console UI

## Table of Contents
- [Installation & Setup](#installation--setup)
- [Console Basics](#console-basics)
- [Tables](#tables)
- [Panels & Boxes](#panels--boxes)
- [Progress Indicators](#progress-indicators)
- [User Input](#user-input)
- [Layouts](#layouts)
- [Live Display](#live-display)
- [Todo App Patterns](#todo-app-patterns)

## Installation & Setup

```bash
pip install rich
```

```python
from rich.console import Console
from rich.theme import Theme

# Custom theme
custom_theme = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold blue",
    "muted": "dim",
})

console = Console(theme=custom_theme)
```

## Console Basics

### Styled Output

```python
from rich.console import Console

console = Console()

# Basic styles
console.print("Hello", style="bold")
console.print("Warning!", style="bold yellow")
console.print("Error!", style="bold red on white")

# Markup syntax
console.print("[bold]Bold[/bold] and [italic]italic[/italic]")
console.print("[red]Red[/red], [green]Green[/green], [blue]Blue[/blue]")
console.print("[link=https://example.com]Click here[/link]")

# Emoji support
console.print(":white_check_mark: Task completed")
console.print(":x: Task failed")
console.print(":warning: Warning message")
```

### Status Messages

```python
# Success
console.print("[green]✓[/green] Task added successfully")

# Error
console.print("[red]✗[/red] Failed to save task")

# Warning
console.print("[yellow]![/yellow] Task deadline approaching")

# Info
console.print("[blue]ℹ[/blue] 5 tasks remaining")
```

## Tables

### Basic Table

```python
from rich.table import Table

table = Table(title="My Tasks")

table.add_column("ID", style="dim", width=6)
table.add_column("Title", style="bold")
table.add_column("Status", justify="center")
table.add_column("Due", justify="right")

table.add_row("1", "Buy groceries", "[green]Done[/green]", "Today")
table.add_row("2", "Call mom", "[yellow]Pending[/yellow]", "Tomorrow")
table.add_row("3", "Finish report", "[red]Overdue[/red]", "Yesterday")

console.print(table)
```

### Table Styles

```python
# Box styles
from rich.box import ROUNDED, SIMPLE, MINIMAL, HEAVY

table = Table(box=ROUNDED)      # Rounded corners
table = Table(box=SIMPLE)       # Simple lines
table = Table(box=MINIMAL)      # Minimal borders
table = Table(box=None)         # No borders

# Row styles
table = Table(
    show_header=True,
    header_style="bold magenta",
    row_styles=["", "dim"],     # Alternating rows
)

# Column alignment
table.add_column("Name", justify="left")
table.add_column("Count", justify="right")
table.add_column("Status", justify="center")
```

### Dynamic Tables

```python
def create_task_table(tasks: list[dict]) -> Table:
    table = Table(title="Tasks", box=ROUNDED)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title")
    table.add_column("Status", justify="center")

    for task in tasks:
        status = format_status(task["status"])
        table.add_row(str(task["id"]), task["title"], status)

    return table

def format_status(status: str) -> str:
    styles = {
        "pending": "[yellow]●[/yellow] Pending",
        "done": "[green]✓[/green] Done",
        "overdue": "[red]![/red] Overdue",
    }
    return styles.get(status, status)
```

## Panels & Boxes

### Basic Panel

```python
from rich.panel import Panel

# Simple panel
console.print(Panel("Hello, World!"))

# Titled panel
console.print(Panel("Content here", title="My Panel"))

# Styled panel
console.print(Panel(
    "Important message",
    title="[bold red]Alert[/bold red]",
    border_style="red",
    padding=(1, 2),
))
```

### Panel Layouts

```python
from rich.panel import Panel
from rich.columns import Columns

# Side by side panels
panels = [
    Panel("Active: 5", title="Tasks"),
    Panel("2 hours", title="Time Today"),
    Panel("80%", title="Completion"),
]
console.print(Columns(panels))
```

## Progress Indicators

### Progress Bar

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

# Simple progress
with Progress() as progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
        time.sleep(0.05)

# Custom progress
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    task = progress.add_task("Loading tasks...", total=None)
    # Indeterminate spinner
```

### Status Spinner

```python
from rich.console import Console

console = Console()

with console.status("[bold green]Loading...") as status:
    # Do work
    time.sleep(2)
    status.update("[bold blue]Processing...")
    time.sleep(2)
```

## User Input

### Prompts

```python
from rich.prompt import Prompt, Confirm, IntPrompt

# Text input
name = Prompt.ask("Enter task name")

# With default
name = Prompt.ask("Enter task name", default="Untitled")

# Password (hidden)
password = Prompt.ask("Password", password=True)

# Integer input
count = IntPrompt.ask("How many tasks?")

# Choices
priority = Prompt.ask(
    "Priority",
    choices=["low", "medium", "high"],
    default="medium",
)

# Confirmation
if Confirm.ask("Delete this task?"):
    print("Deleted!")
```

### Menu Pattern

```python
from rich.prompt import Prompt
from rich.panel import Panel

def show_menu():
    menu = """
[bold]Todo App[/bold]

[1] Add task
[2] List tasks
[3] Complete task
[4] Delete task
[0] Exit
"""
    console.print(Panel(menu, title="Menu"))

    choice = Prompt.ask(
        "Select option",
        choices=["0", "1", "2", "3", "4"],
    )
    return choice
```

## Layouts

### Columns

```python
from rich.columns import Columns
from rich.panel import Panel

# Equal columns
panels = [Panel(f"Panel {i}") for i in range(3)]
console.print(Columns(panels))

# With explicit widths
from rich.table import Table

layout_table = Table.grid(expand=True)
layout_table.add_column(ratio=1)
layout_table.add_column(ratio=2)
layout_table.add_row(
    Panel("Sidebar"),
    Panel("Main Content"),
)
console.print(layout_table)
```

### Layout System

```python
from rich.layout import Layout
from rich.panel import Panel

layout = Layout()

layout.split_column(
    Layout(name="header", size=3),
    Layout(name="body"),
    Layout(name="footer", size=3),
)

layout["body"].split_row(
    Layout(name="sidebar", ratio=1),
    Layout(name="main", ratio=3),
)

layout["header"].update(Panel("Todo App"))
layout["sidebar"].update(Panel("Menu"))
layout["main"].update(Panel("Tasks"))
layout["footer"].update(Panel("Status"))

console.print(layout)
```

## Live Display

### Live Updates

```python
from rich.live import Live
from rich.table import Table

def generate_table() -> Table:
    table = Table()
    table.add_column("Task")
    table.add_column("Status")
    # ... populate dynamically
    return table

with Live(generate_table(), refresh_per_second=4) as live:
    for _ in range(10):
        time.sleep(0.5)
        live.update(generate_table())
```

## Todo App Patterns

### Task Display

```python
def display_task(task: dict) -> Panel:
    """Display a single task as a panel."""
    status_icon = "✓" if task["done"] else "○"
    status_color = "green" if task["done"] else "yellow"

    content = f"""
[{status_color}]{status_icon}[/{status_color}] [bold]{task['title']}[/bold]

{task.get('description', 'No description')}

[dim]Created: {task['created_at']}[/dim]
"""
    return Panel(content, title=f"Task #{task['id']}")

# Usage
console.print(display_task({
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk, bread, eggs",
    "done": False,
    "created_at": "2025-01-15",
}))
```

### Main Application Loop

```python
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

console = Console()

def main():
    console.clear()
    console.print(Panel("[bold]Todo App[/bold]", style="blue"))

    while True:
        choice = show_menu()

        if choice == "0":
            if Confirm.ask("Exit?"):
                console.print("[green]Goodbye![/green]")
                break
        elif choice == "1":
            add_task()
        elif choice == "2":
            list_tasks()
        # ... etc

def add_task():
    console.print("\n[bold]Add New Task[/bold]\n")
    title = Prompt.ask("Title")
    description = Prompt.ask("Description", default="")

    # Save task...
    console.print(f"[green]✓[/green] Added: {title}")
    Prompt.ask("\nPress Enter to continue")
```

### Error Handling Display

```python
from rich.panel import Panel

def show_error(message: str, details: str = None):
    content = f"[bold red]{message}[/bold red]"
    if details:
        content += f"\n\n[dim]{details}[/dim]"

    console.print(Panel(
        content,
        title="[red]Error[/red]",
        border_style="red",
    ))

def show_success(message: str):
    console.print(Panel(
        f"[green]{message}[/green]",
        title="[green]Success[/green]",
        border_style="green",
    ))
```
