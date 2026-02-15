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


def _get_gold_stats(vault_path: Path) -> Dict[str, any]:
    """
    Calculate Gold tier statistics from vault.

    Args:
        vault_path: Path to vault root directory

    Returns:
        Dict with Gold tier stats:
        - api_cost_today: Float (USD)
        - active_plans: Int
        - mcp_email/whatsapp/linkedin: Status str ("✓ Active" or "✗ Inactive")
        - pending_email/whatsapp/linkedin/plans: Int (count of pending approvals)
    """
    import os
    from datetime import date

    stats = {
        "api_cost_today": 0.0,
        "active_plans": 0,
        "mcp_email": "✗ Inactive",
        "mcp_whatsapp": "✗ Inactive",
        "mcp_linkedin": "✗ Inactive",
        "pending_email": 0,
        "pending_whatsapp": 0,
        "pending_linkedin": 0,
        "pending_plans": 0,
    }

    # Count pending approvals
    pending_approval = vault_path / "Pending_Approval"
    if pending_approval.exists():
        stats["pending_email"] = len(list((pending_approval / "Email").glob("*.md")))
        stats["pending_whatsapp"] = len(list((pending_approval / "WhatsApp").glob("*.md")))
        stats["pending_linkedin"] = len(list((pending_approval / "LinkedIn").glob("*.md")))
        stats["pending_plans"] = len(list((pending_approval / "Plans").glob("*.md")))

    # Count active plans
    in_progress = vault_path / "In_Progress"
    if in_progress.exists():
        stats["active_plans"] = len([d for d in in_progress.iterdir() if d.is_dir()])

    # Calculate today's API cost from vault/Logs/API_Usage/
    today_str = date.today().isoformat()
    api_usage_log = vault_path / "Logs" / "API_Usage" / f"{today_str}.md"
    if api_usage_log.exists():
        # Simple parsing: look for cost entries in YAML frontmatter
        try:
            content = api_usage_log.read_text(encoding="utf-8")
            # Extract cost_usd values from log entries (simplified)
            import re
            costs = re.findall(r"cost_usd:\s*([\d.]+)", content)
            stats["api_cost_today"] = sum(float(c) for c in costs)
        except Exception:
            pass

    # Check MCP server status (simplified: check if env vars are set)
    if os.getenv("SMTP_HOST") and os.getenv("SMTP_USER"):
        stats["mcp_email"] = "✓ Active"
    if os.getenv("WHATSAPP_SESSION_PATH"):
        stats["mcp_whatsapp"] = "✓ Active"
    if os.getenv("LINKEDIN_ACCESS_TOKEN"):
        stats["mcp_linkedin"] = "✓ Active"

    return stats


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


def render_dashboard(tasks: List[Dict[str, str]], vault_path: Optional[Path] = None) -> str:
    """Generate Dashboard.md markdown from task list.

    Args:
        tasks: List of task dictionaries
        vault_path: Optional path to vault root (for Gold tier stats)

    Returns:
        Complete Dashboard.md content as string
    """
    import os

    ai_enabled = os.getenv("ENABLE_AI_ANALYSIS", "false").lower() == "true"
    tier = os.getenv("TIER", "bronze").lower()
    plan_execution_enabled = os.getenv("ENABLE_PLAN_EXECUTION", "false").lower() == "true"

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

    # Render markdown with enhanced UI
    lines = [
        "# 🤖 Personal AI Employee Dashboard",
        "",
        f"**Tier:** {tier.upper()} {'🥉' if tier == 'bronze' else '🥈' if tier == 'silver' else '🥇'}",
        f"**Status:** {'🟢 Active' if plan_execution_enabled else '🟡 Monitoring'}",
        "",
        "---",
        "",
        "## 📋 Task Overview",
        "",
    ]

    # Silver tier: include Category column when AI is enabled
    if ai_enabled:
        lines.extend([
            "| Filename | Date | Status | Priority | Category |",
            "|----------|------|--------|----------|----------|",
        ])
        for task in sorted_tasks:
            filename_link = f"[[{task['filename']}]]"
            category = task.get("category", "Uncategorized")

            # Add emoji indicators
            priority = task.get('priority', 'Medium')
            priority_icon = {'Urgent': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(priority, '⚪')
            status = task.get('status', 'Inbox')
            status_icon = {'Inbox': '📥', 'Needs Action': '⚠️', 'Done': '✅', 'In_Progress': '⏳'}.get(status.replace(' ', '_'), '📌')

            lines.append(
                f"| {filename_link} | {task['date_added']} | {status_icon} {task['status']} "
                f"| {priority_icon} {priority} | {category} |"
            )
    else:
        # Bronze format (backward compatible)
        lines.extend([
            "| Filename | Date Added | Status | Priority |",
            "|----------|-----------|--------|----------|",
        ])
        for task in sorted_tasks:
            filename_link = f"[[{task['filename']}]]"
            priority_icon = {'Urgent': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(task.get('priority', 'Medium'), '⚪')
            status_icon = {'Inbox': '📥', 'Needs Action': '⚠️', 'Done': '✅'}.get(task.get('status', 'Inbox'), '📌')
            lines.append(
                f"| {filename_link} | {task['date_added']} | {status_icon} {task['status']} | {priority_icon} {task['priority']} |"
            )

    # Add statistics section with visual progress
    total = stats['total'] if stats['total'] > 0 else 1  # Avoid division by zero
    inbox_pct = int((stats['inbox'] / total) * 100)
    needs_action_pct = int((stats['needs_action'] / total) * 100)
    done_pct = int((stats['done'] / total) * 100)

    lines.extend([
        "",
        "---",
        "",
        "## 📊 Statistics",
        "",
        f"### Task Status",
        f"- 📥 **Inbox**: {stats['inbox']} ({inbox_pct}%)",
        f"- ⚠️  **Needs Action**: {stats['needs_action']} ({needs_action_pct}%)",
        f"- ✅ **Done**: {stats['done']} ({done_pct}%)",
        f"- 📌 **Total Tasks**: {stats['total']}",
    ])

    # Silver tier category statistics
    if ai_enabled:
        lines.extend([
            "",
            "### 🏷️ Category Breakdown",
            f"- 💼 **Work**: {stats['work']} tasks",
            f"- 🏠 **Personal**: {stats['personal']} tasks",
            f"- 🚨 **Urgent**: {stats['urgent']} tasks",
        ])

    # Gold tier status section
    if tier == "gold" and vault_path:
        gold_stats = _get_gold_stats(vault_path)

        # Calculate cost alert level
        cost_today = gold_stats['api_cost_today']
        cost_icon = '🟢' if cost_today < 0.10 else '🟡' if cost_today < 0.25 else '🔴'

        lines.extend([
            "",
            "---",
            "",
            "## 🥇 Gold Tier Status",
            "",
            "### 🔧 System Status",
            f"- 🤖 **Autonomous Mode**: {'✅ Enabled' if plan_execution_enabled else '⏸️ Monitoring Only'}",
            f"- {cost_icon} **API Cost Today**: ${cost_today:.4f} / $0.10",
            f"- 📋 **Active Plans**: {gold_stats['active_plans']}",
            "",
            "### 🔌 MCP Servers",
            f"- 📧 **email-mcp**: {gold_stats['mcp_email']}",
            f"- 💬 **whatsapp-mcp**: {gold_stats['mcp_whatsapp']}",
            f"- 🔗 **linkedin-mcp**: {gold_stats['mcp_linkedin']}",
            "",
            "### ⏳ Pending Approvals",
            f"- 📧 **Email Drafts**: {gold_stats['pending_email']}",
            f"- 💬 **WhatsApp Drafts**: {gold_stats['pending_whatsapp']}",
            f"- 🔗 **LinkedIn Posts**: {gold_stats['pending_linkedin']}",
            f"- 📋 **Execution Plans**: {gold_stats['pending_plans']}",
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
        markdown_content = render_dashboard(existing_tasks, vault_path=vault)

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
