"""Dashboard Updater Module for Bronze Tier Personal AI Employee.

This module provides atomic Dashboard.md updates with backup and recovery:
- update_dashboard(): Atomic write with timestamped backup
- create_backup(): Create Dashboard.md.bak.TIMESTAMP
- restore_from_backup(): Restore from most recent backup
- parse_dashboard(): Extract task list from Dashboard.md
- render_dashboard(): Generate markdown table from task list

All operations use atomic file writes to prevent corruption.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_dashboard(dashboard_path: Path) -> List[Dict[str, str]]:
    """Parse Dashboard.md and extract task table rows.

    Args:
        dashboard_path: Path to Dashboard.md file

    Returns:
        List of task dictionaries with keys: filename, date_added, status, priority, category

    Raises:
        ValueError: If Dashboard.md is corrupted (invalid table format)
    """
    if not dashboard_path.exists():
        return []

    content = dashboard_path.read_text(encoding="utf-8")
    tasks: List[Dict[str, str]] = []

    # Find table start
    lines = content.split("\n")
    table_start = None

    for i, line in enumerate(lines):
        if line.strip().startswith("| Filename"):
            table_start = i + 2  # Skip header and separator
            break

    if table_start is None:
        return []

    # Parse task rows - supports both 4-column (Bronze) and 5-column (Silver) format
    for line in lines[table_start:]:
        if not line.strip() or not line.strip().startswith("|"):
            break

        columns = [col.strip() for col in line.split("|")[1:-1]]
        if len(columns) >= 4:
            # Remove wiki link syntax from filename
            filename = columns[0].strip("[]")
            task = {
                "filename": filename,
                "date_added": columns[1],
                "status": columns[2],
                "priority": columns[3],
                "category": columns[4] if len(columns) >= 5 else "Uncategorized",
            }
            tasks.append(task)

    return tasks


def render_dashboard(tasks: List[Dict[str, str]]) -> str:
    """Generate Dashboard.md markdown from task list.

    Args:
        tasks: List of task dictionaries

    Returns:
        Complete Dashboard.md content as string
    """
    import os

    ai_enabled = os.getenv("ENABLE_AI_ANALYSIS", "false").lower() == "true"

    # Sort tasks by priority order (Urgent → High → Medium → Low), then by date_added
    priority_order = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            priority_order.get(t.get("priority", "Medium"), 2),
            t.get("date_added", ""),
        ),
    )

    # Calculate statistics
    stats = {
        "total": len(sorted_tasks),
        "inbox": sum(1 for t in sorted_tasks if t["status"].lower() == "inbox"),
        "needs_action": sum(1 for t in sorted_tasks if t["status"].lower() == "needs action"),
        "done": sum(1 for t in sorted_tasks if t["status"].lower() == "done"),
        "work": sum(1 for t in sorted_tasks if t.get("category", "") == "Work"),
        "personal": sum(1 for t in sorted_tasks if t.get("category", "") == "Personal"),
        "urgent": sum(1 for t in sorted_tasks if t.get("category", "") == "Urgent"),
    }

    # Render markdown
    lines = [
        "# Personal AI Employee Dashboard",
        "",
        "## Task Overview",
    ]

    # Silver tier: include Category column when AI is enabled
    if ai_enabled:
        lines.extend([
            "| Filename | Date Added | Status | Priority | Category |",
            "|----------|-----------|--------|----------|----------|",
        ])
        for task in sorted_tasks:
            filename_link = f"[[{task['filename']}]]"
            category = task.get("category", "Uncategorized")
            lines.append(
                f"| {filename_link} | {task['date_added']} | {task['status']} "
                f"| {task['priority']} | {category} |"
            )
    else:
        # Bronze format (backward compatible)
        lines.extend([
            "| Filename | Date Added | Status | Priority |",
            "|----------|-----------|--------|----------|",
        ])
        for task in sorted_tasks:
            filename_link = f"[[{task['filename']}]]"
            lines.append(
                f"| {filename_link} | {task['date_added']} | {task['status']} | {task['priority']} |"
            )

    # Add statistics section
    lines.extend([
        "",
        "## Statistics",
        f"- **Total Tasks**: {stats['total']}",
        f"- **Inbox**: {stats['inbox']}",
        f"- **Needs Action**: {stats['needs_action']}",
        f"- **Done**: {stats['done']}",
    ])

    # Silver tier category statistics
    if ai_enabled:
        lines.extend([
            "",
            "### Category Breakdown",
            f"- **Work Tasks**: {stats['work']}",
            f"- **Personal Tasks**: {stats['personal']}",
            f"- **Urgent Tasks**: {stats['urgent']}",
        ])

    lines.extend([
        "",
        "---",
        f"*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ])

    return "\n".join(lines)


def create_backup(dashboard_path: Path) -> Path:
    """Create timestamped backup of Dashboard.md.

    Args:
        dashboard_path: Path to Dashboard.md file

    Returns:
        Path to created backup file

    Raises:
        IOError: If backup creation fails
    """
    if not dashboard_path.exists():
        raise FileNotFoundError(f"Dashboard not found: {dashboard_path}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = dashboard_path.with_name(f"Dashboard.md.bak.{timestamp}")

    try:
        shutil.copy2(dashboard_path, backup_path)
        return backup_path
    except IOError as e:
        raise IOError(f"Failed to create backup: {e}") from e


def validate_dashboard(dashboard_path: Path) -> bool:
    """Validate Dashboard.md markdown structure.

    Args:
        dashboard_path: Path to Dashboard.md file

    Returns:
        True if valid, False otherwise
    """
    if not dashboard_path.exists():
        return False

    try:
        content = dashboard_path.read_text(encoding="utf-8")

        # Check for required sections
        if "| Filename" not in content:
            return False
        if "## Statistics" not in content:
            return False
        if "Last Updated" not in content:
            return False

        return True
    except Exception:
        return False


def update_dashboard(
    vault_path: str,
    new_files: List[Tuple[str, str]],
    ai_results: Optional[List[Tuple[str, str]]] = None,
) -> bool:
    """Update Dashboard.md with new tasks (atomic write with backup).

    Args:
        vault_path: Absolute path to vault root directory
        new_files: List of (filename, status) tuples to add to dashboard
        ai_results: Optional list of (priority, category) tuples from Silver AI analysis.
                    Must match length and order of new_files if provided.

    Returns:
        True if update successful, False if failed

    Raises:
        ValueError: If any status is invalid
        PermissionError: If vault_path is not writable
    """
    vault = Path(vault_path).resolve()
    dashboard_path = vault / "Dashboard.md"
    temp_path = vault / "Dashboard.md.tmp"

    try:
        # Step 1: Create backup
        if dashboard_path.exists():
            create_backup(dashboard_path)

        # Step 2: Parse existing dashboard
        existing_tasks = parse_dashboard(dashboard_path)

        # Step 3: Add new tasks
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        for i, (filename, status) in enumerate(new_files):
            priority = "Medium"
            category = "Uncategorized"

            if ai_results and i < len(ai_results):
                priority, category = ai_results[i]

            existing_tasks.append({
                "filename": filename,
                "date_added": current_time,
                "status": status,
                "priority": priority,
                "category": category,
            })

        # Step 4: Render markdown
        markdown_content = render_dashboard(existing_tasks)

        # Step 5: Write to temp file
        temp_path.write_text(markdown_content, encoding="utf-8")

        # Step 6: Validate temp file
        if not validate_dashboard(temp_path):
            temp_path.unlink()
            return False

        # Step 7: Atomic rename
        temp_path.replace(dashboard_path)

        return True

    except Exception as e:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
        return False


def restore_from_backup(vault_path: str, backup_filename: str = None) -> bool:
    """Restore Dashboard.md from most recent backup.

    Args:
        vault_path: Absolute path to vault root directory
        backup_filename: Optional specific backup to restore (default: most recent)

    Returns:
        True if restore successful, False if no backups found or restore failed
    """
    vault = Path(vault_path).resolve()
    dashboard_path = vault / "Dashboard.md"
    temp_path = vault / "Dashboard.md.tmp"

    # List all backup files
    backup_files = sorted(vault.glob("Dashboard.md.bak.*"), reverse=True)

    if not backup_files:
        return False

    # Select backup to restore
    if backup_filename:
        backup_path = vault / backup_filename
        if not backup_path.exists():
            return False
    else:
        backup_path = backup_files[0]  # Most recent

    try:
        # Copy backup to temp
        shutil.copy2(backup_path, temp_path)

        # Validate temp file
        if not validate_dashboard(temp_path):
            temp_path.unlink()
            return False

        # Atomic rename
        temp_path.replace(dashboard_path)

        return True

    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        return False


def prune_old_backups(vault_path: str, keep_days: int = 7) -> int:
    """Delete backup files older than keep_days.

    Args:
        vault_path: Absolute path to vault root directory
        keep_days: Number of days to keep backups (default: 7)

    Returns:
        Number of backups deleted
    """
    vault = Path(vault_path).resolve()
    cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)

    deleted = 0
    for backup_file in vault.glob("Dashboard.md.bak.*"):
        if backup_file.stat().st_mtime < cutoff_time:
            backup_file.unlink()
            deleted += 1

    return deleted
