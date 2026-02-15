#!/usr/bin/env python3
"""
Approval Watcher Runner - Background Service

Monitors vault/Approved/* folders using watchdog for file-move events.
Invokes approval_watcher.py to process approved drafts and invoke MCP actions.

Handles:
- Email approvals (T015)
- LinkedIn approvals (T023)
- WhatsApp approvals (T034)
- Plan approvals

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Tasks: T015, T023, T034 (approval handlers)
"""

import os
import sys
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[ERROR] watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

# Add agent_skills to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.approval_watcher import process_approval


class ApprovalFileHandler(FileSystemEventHandler):
    """Handle file creation events in vault/Approved/* folders"""

    def __init__(self, approval_type: str):
        """
        Initialize handler.

        Args:
            approval_type: Type of approvals to handle ("email", "whatsapp", "linkedin", "plan")
        """
        self.approval_type = approval_type
        super().__init__()

    def on_created(self, event):
        """Triggered when file created/moved into Approved folder"""
        if event.is_directory:
            return

        file_path = event.src_path

        # Only process markdown files
        if not file_path.endswith('.md'):
            return

        print(f"[approval_watcher] Approval detected: {Path(file_path).name} ({self.approval_type})")

        # Process approval (invokes MCP)
        try:
            success = process_approval(file_path, self.approval_type)
            if success:
                print(f"[approval_watcher] ✓ Approval processed successfully")
            else:
                print(f"[approval_watcher] ✗ Approval processing failed")

        except Exception as e:
            print(f"[approval_watcher] Error processing approval: {e}")


def run_approval_watcher(vault_path: str):
    """
    Start approval watcher for all approval types.

    Args:
        vault_path: Absolute path to vault root
    """
    vault = Path(vault_path)
    approved_dir = vault / "Approved"

    # Ensure Approved directories exist
    approved_email = approved_dir / "Email"
    approved_whatsapp = approved_dir / "WhatsApp"
    approved_linkedin = approved_dir / "LinkedIn"
    approved_plans = approved_dir / "Plans"

    for directory in [approved_email, approved_whatsapp, approved_linkedin, approved_plans]:
        directory.mkdir(parents=True, exist_ok=True)

    print(f"[approval_watcher] Starting approval watcher")
    print(f"[approval_watcher] Monitoring: {approved_dir}")
    print(f"[approval_watcher] Watching:")
    print(f"  - Email: {approved_email}")
    print(f"  - WhatsApp: {approved_whatsapp}")
    print(f"  - LinkedIn: {approved_linkedin}")
    print(f"  - Plans: {approved_plans}")

    # Create observer
    observer = Observer()

    # Schedule handlers for each approval type
    observer.schedule(ApprovalFileHandler("email"), str(approved_email), recursive=False)
    observer.schedule(ApprovalFileHandler("whatsapp"), str(approved_whatsapp), recursive=False)
    observer.schedule(ApprovalFileHandler("linkedin"), str(approved_linkedin), recursive=False)
    observer.schedule(ApprovalFileHandler("plan"), str(approved_plans), recursive=False)

    # Start observer
    observer.start()
    print("[approval_watcher] ✓ Watcher started (press Ctrl+C to stop)\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[approval_watcher] Stopping...")
        observer.stop()

    observer.join()
    print("[approval_watcher] Stopped")


if __name__ == "__main__":
    # Get vault path from environment or command line
    vault_path = os.getenv("VAULT_PATH", "vault")

    if len(sys.argv) > 1:
        vault_path = sys.argv[1]

    run_approval_watcher(vault_path)
