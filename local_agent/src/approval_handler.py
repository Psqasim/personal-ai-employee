"""
Approval Handler - Monitor vault/Approved/ and route to executors

Continuously scans vault/Approved/ subfolders every 30 seconds.
Detects new .md files, parses frontmatter, routes to the correct executor,
moves file to vault/Done/ on success or vault/Failed/ on error.

Reuses: agent_skills/approval_watcher.py for MCP invocation logic
"""
import os
import sys
import time
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.approval_watcher import process_approval
from agent_skills.vault_parser import parse_frontmatter
from cloud_agent.src.notifications.whatsapp_notifier import (
    notify_task_completed,
    notify_critical_error,
)

logger = logging.getLogger(__name__)


class ApprovalHandler:
    """
    Monitors vault/Approved/ subfolders and routes approved drafts to executors.

    Routing:
    - vault/Approved/Email/     → email executor (email-mcp send_email)
    - vault/Approved/WhatsApp/  → whatsapp executor (whatsapp-mcp send_message)
    - vault/Approved/LinkedIn/  → linkedin executor (linkedin-mcp create_post)
    - vault/Approved/Odoo/      → odoo executor (odoo-mcp create_invoice)
    """

    # Map subfolder name → draft_type string used by approval_watcher
    FOLDER_TYPE_MAP = {
        "Email": "email",
        "WhatsApp": "whatsapp",
        "LinkedIn": "linkedin",
        "Odoo": "odoo",
    }

    def __init__(self, vault_path: str, agent_id: str = "local"):
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"
        self.failed_path = self.vault_path / "Failed"
        self.log_path = self.vault_path / "Logs" / "Local"

        # Track processed files to avoid double-processing in same session
        self._processed: set = set()

        # Ensure directories exist
        for d in [self.done_path, self.failed_path, self.log_path]:
            d.mkdir(parents=True, exist_ok=True)

    def scan_approved(self) -> list[Path]:
        """
        Scan vault/Approved/ subfolders for unprocessed .md files.

        Returns:
            List of (file_path, draft_type) tuples ready for processing
        """
        items = []

        if not self.approved_path.exists():
            return items

        for folder_name, draft_type in self.FOLDER_TYPE_MAP.items():
            subfolder = self.approved_path / folder_name
            if not subfolder.exists():
                continue

            for md_file in sorted(subfolder.glob("*.md")):
                # Skip already-processed in this session
                if str(md_file) in self._processed:
                    continue

                # Skip lock files
                if md_file.suffix == ".lock":
                    continue

                items.append((md_file, draft_type))

        return items

    def process_all(self) -> int:
        """
        Process all pending approved files.

        Returns:
            Number of files successfully processed
        """
        pending = self.scan_approved()
        if not pending:
            logger.debug("No pending approvals")
            return 0

        logger.info(f"📋 Found {len(pending)} pending approval(s)")
        success_count = 0

        for file_path, draft_type in pending:
            logger.info(f"Processing {draft_type}: {file_path.name}")
            try:
                # Parse frontmatter BEFORE process_approval() moves the file
                # parse_frontmatter returns (dict, body_string) tuple
                frontmatter, _ = parse_frontmatter(str(file_path))

                ok = process_approval(str(file_path), draft_type)
                if ok:
                    success_count += 1
                    self._processed.add(str(file_path))
                    self._log_action(file_path, draft_type, "success")
                    logger.info(f"✅ {draft_type} processed: {file_path.name}")

                    # WhatsApp confirmation after successful send
                    if draft_type in ("email", "whatsapp"):
                        notify_task_completed(
                            task_type=draft_type.capitalize(),
                            recipient=frontmatter.get("to", frontmatter.get("chat_id", "Unknown")),
                            subject=frontmatter.get("subject")
                        )
                else:
                    self._log_action(file_path, draft_type, "failed")
                    logger.warning(f"⚠️  {draft_type} processing returned False: {file_path.name}")
                    if draft_type in ("email", "whatsapp"):
                        notify_critical_error(f"{draft_type.capitalize()} send failed: {file_path.name}")

            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                self._log_action(file_path, draft_type, "error", str(e))
                self._move_to_failed(file_path, str(e))
                notify_critical_error(f"{draft_type.capitalize()} error after retries: {e}")

        return success_count

    def _move_to_failed(self, file_path: Path, reason: str) -> None:
        """Move a file to vault/Failed/ and annotate with error reason."""
        try:
            dest = self.failed_path / file_path.parent.name / file_path.name
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Append failure reason to file before moving
            content = file_path.read_text(encoding="utf-8")
            content += f"\n\n<!-- Failed: {reason} at {datetime.now().isoformat()} -->\n"
            dest.write_text(content, encoding="utf-8")
            file_path.unlink()

            self._processed.add(str(file_path))
            logger.info(f"Moved to Failed: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to move {file_path.name} to Failed/: {e}")

    def _log_action(self, file_path: Path, draft_type: str, status: str, error: str = "") -> None:
        """Append action log entry to vault/Logs/Local/approval_actions.md."""
        log_file = self.log_path / "approval_actions.md"
        timestamp = datetime.now().isoformat()
        entry = (
            f"| {timestamp} | {draft_type} | {file_path.name} | "
            f"{status} | {error[:100] if error else '-'} |\n"
        )

        try:
            if not log_file.exists():
                log_file.write_text(
                    "# Approval Actions Log\n\n"
                    "| Timestamp | Type | File | Status | Error |\n"
                    "|-----------|------|------|--------|-------|\n"
                )
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            logger.warning(f"Could not write approval log: {e}")

    def run_once(self) -> int:
        """Run a single scan-and-process cycle. Returns count processed."""
        return self.process_all()
