#!/usr/bin/env python3
"""
Plan Watcher - Monitor vault/Approved/Plans/ for Approved Plan Execution

This script monitors the vault/Approved/Plans/ folder for approved plan files.
When a plan is approved (file moved to Approved/Plans/), it:
1. Parses the Plan.md file
2. Initializes ExecutionState in vault/In_Progress/{plan_id}/state.md
3. Invokes plan_executor.execute_plan() (Ralph Wiggum loop)
4. Updates Dashboard.md with plan progress

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Task: T044 [US4] Create scripts/plan_watcher.py
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from filelock import FileLock, Timeout

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.plan_executor import execute_plan_ralph_wiggum_loop
from agent_skills.vault_parser import parse_plan_file
from agent_skills.dashboard_updater import update_dashboard


class PlanApprovalHandler(FileSystemEventHandler):
    """Handle plan approval events (file created/moved to vault/Approved/Plans/)"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.approved_plans_dir = self.vault_path / "Approved" / "Plans"
        self.approved_plans_dir.mkdir(parents=True, exist_ok=True)

        # Track processed plans to avoid duplicates
        self.processed_file = self.vault_path / "Logs" / "processed_plans.txt"
        self.processed_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.processed_file.exists():
            self.processed_file.write_text("", encoding="utf-8")

    def on_created(self, event):
        """Triggered when plan file moved/created in vault/Approved/Plans/"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process .md files in Approved/Plans/
        if file_path.suffix != ".md":
            return

        if "Approved/Plans" not in str(file_path):
            return

        print(f"[plan_watcher] Plan approval detected: {file_path.name}")
        self._process_approved_plan(file_path)

    def _process_approved_plan(self, file_path: Path):
        """
        Process an approved plan file.

        Args:
            file_path: Path to approved plan file
        """
        # Use file lock to prevent duplicate processing
        lock_path = file_path.with_suffix(".lock")

        try:
            with FileLock(lock_path, timeout=5):
                # Check if already processed (idempotency)
                if self._is_processed(file_path):
                    print(f"[plan_watcher] Plan already processed: {file_path.name}")
                    return

                # Parse plan
                try:
                    plan = parse_plan_file(str(file_path))
                    plan_id = plan.plan_id
                except Exception as e:
                    print(f"[plan_watcher] ERROR: Failed to parse plan {file_path.name}: {e}")
                    self._create_error_escalation(file_path, f"Plan parsing failed: {e}")
                    return

                # Log approval
                self._log_plan_approval(plan_id, str(file_path))

                # Move plan to vault/Plans/ for execution
                plans_dir = self.vault_path / "Plans"
                plans_dir.mkdir(parents=True, exist_ok=True)
                plan_execution_file = plans_dir / file_path.name

                if plan_execution_file.exists():
                    print(f"[plan_watcher] WARNING: Plan file already exists in Plans/: {file_path.name}")
                else:
                    # Copy to Plans/ (keep original in Approved/ for audit)
                    import shutil
                    shutil.copy2(file_path, plan_execution_file)

                # Execute plan via Ralph Wiggum loop (async)
                print(f"[plan_watcher] Starting plan execution: {plan_id}")
                asyncio.run(self._execute_plan_async(plan_id, plan_execution_file))

                # Mark as processed
                self._mark_processed(file_path)

                # Update dashboard
                self._update_dashboard_plan_started(plan_id, plan.objective)

        except Timeout:
            # Another watcher is processing this plan
            print(f"[plan_watcher] Another watcher is processing plan: {file_path.name}")
            return
        except Exception as e:
            print(f"[plan_watcher] ERROR: Failed to process plan {file_path.name}: {e}")
            self._create_error_escalation(file_path, str(e))

    async def _execute_plan_async(self, plan_id: str, plan_file: Path):
        """Execute plan using Ralph Wiggum loop"""
        try:
            success = await execute_plan_ralph_wiggum_loop(plan_id, str(self.vault_path))

            if success:
                print(f"[plan_watcher] Plan completed successfully: {plan_id}")
            else:
                print(f"[plan_watcher] Plan escalated or failed: {plan_id}")

        except Exception as e:
            print(f"[plan_watcher] ERROR: Plan execution failed: {e}")
            self._create_error_escalation(plan_file, f"Execution failed: {e}")

    def _is_processed(self, file_path: Path) -> bool:
        """Check if plan has already been processed"""
        processed_plans = self.processed_file.read_text(encoding="utf-8").splitlines()
        return str(file_path) in processed_plans

    def _mark_processed(self, file_path: Path):
        """Mark plan as processed"""
        with open(self.processed_file, "a", encoding="utf-8") as f:
            f.write(f"{file_path}\n")

    def _log_plan_approval(self, plan_id: str, approval_file_path: str):
        """Log plan approval to vault/Logs/Human_Approvals/"""
        log_dir = self.vault_path / "Logs" / "Human_Approvals"
        log_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"{today}.md"

        log_entry = f"""
## Plan Approval at {datetime.now().strftime('%H:%M:%S')}
**Plan ID**: {plan_id}
**Approval File**: {approval_file_path}
**Action**: Plan execution approved
**Timestamp**: {datetime.now().isoformat()}
"""

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def _update_dashboard_plan_started(self, plan_id: str, objective: str):
        """Update dashboard with plan execution status"""
        # This is a simplified update - in production, would use dashboard_updater module
        print(f"[dashboard] Plan started: {objective}")

    def _create_error_escalation(self, plan_file: Path, error: str):
        """Create error escalation file in vault/Needs_Action/"""
        from datetime import datetime

        escalation_file = self.vault_path / "Needs_Action" / f"plan_error_{plan_file.stem}_{int(time.time())}.md"

        with open(escalation_file, "w", encoding="utf-8") as f:
            f.write(f"""---
plan_file: {plan_file.name}
error: {error}
timestamp: {datetime.now().isoformat()}
---

# Plan Watcher Error

**Plan File**: {plan_file.name}
**Error**: {error}
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Recovery Actions
1. Review plan file at {plan_file}
2. Fix any validation errors
3. Re-approve plan or simplify
""")


def start_plan_watcher(vault_path: str = "vault"):
    """
    Start plan watcher to monitor vault/Approved/Plans/.

    Args:
        vault_path: Path to vault root (default: "vault")
    """
    vault = Path(vault_path).resolve()

    if not vault.exists():
        print(f"[plan_watcher] ERROR: Vault not found: {vault}")
        sys.exit(1)

    # Create Approved/Plans/ directory if it doesn't exist
    approved_plans = vault / "Approved" / "Plans"
    approved_plans.mkdir(parents=True, exist_ok=True)

    # Start watchdog observer
    observer = Observer()
    handler = PlanApprovalHandler(str(vault))

    observer.schedule(handler, str(approved_plans), recursive=False)
    observer.start()

    print(f"[plan_watcher] Monitoring: {approved_plans}")
    print("[plan_watcher] Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[plan_watcher] Stopping...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plan Watcher - Monitor approved plans for execution")
    parser.add_argument("--vault", default="vault", help="Path to vault directory (default: vault)")

    args = parser.parse_args()

    start_plan_watcher(vault_path=args.vault)
