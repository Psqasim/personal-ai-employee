#!/usr/bin/env python3
"""
Odoo Watcher - Detect Accounting Tasks and Create Odoo Drafts

This script monitors vault/Inbox/ for tasks with type="invoice" or type="expense",
parses task content for odoo_data, and creates OdooDraft files in
vault/Pending_Approval/Odoo/ for human approval.

Features:
- Detect invoice/expense tasks in vault/Inbox/
- Parse task frontmatter for odoo_data (customer/vendor, amount, description)
- Generate OdooDraft markdown files with YAML frontmatter
- Graceful degradation when ENABLE_ODOO=false
- Integration with approval workflow

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Task: T059 [US7] Create Odoo draft detection logic
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def parse_task_for_odoo_data(task_file: Path) -> Optional[Dict[str, Any]]:
    """
    Parse task file and extract Odoo-relevant data from YAML frontmatter.

    Args:
        task_file: Path to task markdown file

    Returns:
        Dict with keys: type, odoo_data, task_id
        None if not an Odoo-related task

    Expected Task Format:
    ---
    task_id: TASK_123
    type: invoice  # or "expense"
    priority: High
    odoo_data:
      customer: "Acme Corp"  # for invoices
      vendor: "Office Supplies Ltd"  # for expenses
      amount: 1500.00
      description: "Website development services"
      date: "2026-02-14"  # optional
    ---
    """
    try:
        content = task_file.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter = yaml.safe_load(parts[1])

        # Check if this is an Odoo task
        task_type = frontmatter.get("type", "").lower()
        if task_type not in ["invoice", "expense"]:
            return None

        # Extract odoo_data
        odoo_data = frontmatter.get("odoo_data", {})
        if not odoo_data:
            print(f"[odoo_watcher] WARNING: Task {task_file.name} has type={task_type} but no odoo_data")
            return None

        # Validate required fields
        if task_type == "invoice":
            required_fields = ["customer", "amount", "description"]
        else:  # expense
            required_fields = ["vendor", "amount", "description"]

        missing_fields = [f for f in required_fields if f not in odoo_data]
        if missing_fields:
            print(f"[odoo_watcher] ERROR: Task {task_file.name} missing fields: {missing_fields}")
            return None

        return {
            "type": task_type,
            "odoo_data": odoo_data,
            "task_id": frontmatter.get("task_id", task_file.stem)
        }

    except Exception as e:
        print(f"[odoo_watcher] ERROR parsing {task_file.name}: {e}")
        return None


def create_odoo_draft(task_data: Dict[str, Any], vault_path: Path) -> bool:
    """
    Create OdooDraft file in vault/Pending_Approval/Odoo/.

    Args:
        task_data: Parsed task data with type, odoo_data, task_id
        vault_path: Path to vault root

    Returns:
        True if draft created successfully, False otherwise
    """
    draft_dir = vault_path / "Pending_Approval" / "Odoo"
    draft_dir.mkdir(parents=True, exist_ok=True)

    # Generate draft filename
    task_type = task_data["type"]
    task_id = task_data["task_id"]
    timestamp = int(datetime.now().timestamp())
    draft_filename = f"ODOO_{task_type.upper()}_{task_id}_{timestamp}.md"
    draft_path = draft_dir / draft_filename

    # Determine action type
    if task_type == "invoice":
        action = "create_draft_invoice"
        entity = task_data["odoo_data"].get("customer", "Unknown Customer")
    else:  # expense
        action = "create_draft_expense"
        entity = task_data["odoo_data"].get("vendor", "Unknown Vendor")

    # Create draft file with YAML frontmatter
    draft_content = f"""---
draft_id: ODOO_{task_type.upper()}_{task_id}_{timestamp}
original_task_id: {task_id}
entry_type: {task_type}
odoo_data:
  {yaml.dump(task_data["odoo_data"], default_flow_style=False).strip()}
action: {action}
status: pending_approval
generated_at: {datetime.now().isoformat()}
mcp_server: odoo-mcp
---

# Odoo {task_type.capitalize()} Draft

**Original Task**: {task_id}
**Type**: {task_type.capitalize()}
**Entity**: {entity}
**Amount**: ${task_data["odoo_data"].get("amount", 0):.2f}

## Draft Details

**Description**: {task_data["odoo_data"].get("description", "N/A")}
**Date**: {task_data["odoo_data"].get("date") or task_data["odoo_data"].get("invoice_date") or task_data["odoo_data"].get("expense_date") or datetime.now().strftime("%Y-%m-%d")}

## Approval

**IMPORTANT**: This will create a **DRAFT** entry in Odoo (status=draft).
The entry will NOT be automatically confirmed or posted.
You must manually review and confirm in Odoo after approval.

- Move to `vault/Approved/Odoo/` to create draft in Odoo
- Move to `vault/Rejected/` to discard
"""

    try:
        draft_path.write_text(draft_content, encoding="utf-8")
        print(f"[odoo_watcher] Created Odoo draft: {draft_filename}")
        return True

    except Exception as e:
        print(f"[odoo_watcher] ERROR creating draft: {e}")
        return False


def watch_for_odoo_tasks(vault_path: str = "vault", poll_interval: int = 30):
    """
    Watch vault/Inbox/ for Odoo-related tasks (type=invoice or type=expense).

    Args:
        vault_path: Path to vault root (default: "vault")
        poll_interval: Seconds between polls (default: 30)
    """
    vault = Path(vault_path).resolve()
    inbox_dir = vault / "Inbox"

    if not inbox_dir.exists():
        print(f"[odoo_watcher] ERROR: Inbox not found: {inbox_dir}")
        sys.exit(1)

    # Check if Odoo is enabled (T061: graceful degradation)
    odoo_enabled = os.getenv("ENABLE_ODOO", "false").lower() == "true"

    if not odoo_enabled:
        print("[odoo_watcher] Odoo integration disabled (ENABLE_ODOO=false)")
        print("[odoo_watcher] Set ENABLE_ODOO=true in .env to enable Odoo watcher")
        sys.exit(0)

    print(f"[odoo_watcher] Monitoring: {inbox_dir}")
    print(f"[odoo_watcher] Poll interval: {poll_interval}s")
    print("[odoo_watcher] Looking for tasks with type='invoice' or type='expense'")
    print("[odoo_watcher] Press Ctrl+C to stop")

    # Track processed tasks to avoid duplicates
    processed_tasks_file = vault / "Logs" / "processed_odoo_tasks.txt"
    processed_tasks_file.parent.mkdir(parents=True, exist_ok=True)

    if not processed_tasks_file.exists():
        processed_tasks_file.write_text("", encoding="utf-8")

    processed_tasks = set(processed_tasks_file.read_text(encoding="utf-8").splitlines())

    try:
        while True:
            # Scan inbox for .md files
            for task_file in inbox_dir.glob("*.md"):
                # Skip if already processed
                if str(task_file) in processed_tasks:
                    continue

                # Parse task for Odoo data
                task_data = parse_task_for_odoo_data(task_file)

                if task_data:
                    print(f"[odoo_watcher] Found Odoo task: {task_file.name} (type={task_data['type']})")

                    # Create Odoo draft
                    if create_odoo_draft(task_data, vault):
                        # Mark as processed
                        processed_tasks.add(str(task_file))
                        with open(processed_tasks_file, "a", encoding="utf-8") as f:
                            f.write(f"{task_file}\n")

                        # Move task to Done (draft created)
                        done_dir = vault / "Done"
                        done_dir.mkdir(parents=True, exist_ok=True)
                        task_file.rename(done_dir / task_file.name)

            # Wait before next poll
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n[odoo_watcher] Stopping...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Odoo Watcher - Monitor inbox for accounting tasks")
    parser.add_argument("--vault", default="vault", help="Path to vault directory (default: vault)")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds (default: 30)")

    args = parser.parse_args()

    watch_for_odoo_tasks(vault_path=args.vault, poll_interval=args.interval)
