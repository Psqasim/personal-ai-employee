#!/usr/bin/env python3
"""Vault Initialization Script for Bronze Tier Personal AI Employee.

This script creates the foundational structure for an Obsidian vault:
- 5 folders: Inbox/, Needs_Action/, Done/, Plans/, Logs/
- Dashboard.md with empty task table
- Company_Handbook.md with required configuration sections
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_folder_structure(vault_path: Path) -> None:
    """Create 5 vault folders with proper structure.

    Args:
        vault_path: Path to vault root directory

    Raises:
        PermissionError: If vault_path parent directory is not writable
    """
    folders = ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]

    for folder in folders:
        folder_path = vault_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Created {folder}/ folder")


def create_dashboard(vault_path: Path) -> None:
    """Create Dashboard.md with empty task table.

    Args:
        vault_path: Path to vault root directory

    Template follows spec Appendix A format with:
    - Task Overview table (4 columns)
    - Statistics section
    - Last Updated timestamp
    """
    dashboard_template = """# Personal AI Employee Dashboard

## Task Overview
| Filename | Date Added | Status | Priority |
|----------|-----------|--------|----------|

## Statistics
- **Total Tasks**: 0
- **Inbox**: 0
- **Needs Action**: 0
- **Done**: 0

---
*Last Updated: {timestamp}*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    dashboard_path = vault_path / "Dashboard.md"
    dashboard_path.write_text(dashboard_template, encoding="utf-8")
    logger.info("✓ Created Dashboard.md")


def create_handbook(vault_path: Path) -> None:
    """Create Company_Handbook.md with 5 required sections and YAML frontmatter.

    Args:
        vault_path: Path to vault root directory

    Template follows spec Appendix B format with all required sections:
    1. File Naming Convention
    2. Folder Usage Guidelines
    3. Forbidden Operations (Bronze Tier)
    4. Escalation Rules
    5. Bronze Tier Limitations
    """
    handbook_template = """---
version: 1.0.0
tier: bronze
last_updated: {date}
polling_interval: 30
---

# Company Handbook - Bronze Tier

## 1. File Naming Convention

All task files in Inbox/ should follow this format:
- Format: `YYYY-MM-DD-brief-description.md`
- Example: `2026-02-10-review-client-proposal.md`
- Hyphens for word separation (no spaces)
- Dates in ISO 8601 format (YYYY-MM-DD)

## 2. Folder Usage Guidelines

- **Inbox/**: Drop all new tasks here. Watcher monitors this folder.
- **Needs_Action/**: (Manual move in Bronze) Tasks requiring immediate attention.
- **Done/**: (Manual move in Bronze) Completed tasks for archival.
- **Plans/**: Reserved for future use (Silver tier and above).
- **Logs/**: System-generated logs. Do not manually edit.

## 3. Forbidden Operations (Bronze Tier)

The Bronze tier AI Employee is **monitoring only**. It will:
- ✅ Detect new files in Inbox/
- ✅ Update Dashboard.md automatically
- ✅ Log events to vault/Logs/

It will **NOT**:
- ❌ Delete any files
- ❌ Move files between folders
- ❌ Modify file contents
- ❌ Execute code from vault files
- ❌ Make network requests

## 4. Escalation Rules

The watcher logs warnings for:
- Obsidian file locks (will retry automatically)
- Dashboard.md corruption (will restore from backup)
- Vault exceeding 1000 files (performance warning)
- Invalid file encoding (UTF-8 required)

**Human intervention required for**:
- Watcher process crashes (check vault/Logs/ for errors)
- Persistent file lock conflicts (close Obsidian temporarily)
- Backup restoration failures (manual recovery from .bak files)

## 5. Bronze Tier Limitations

This is a **foundation tier**. The AI Employee:
- Operates 100% offline (no AI analysis, no external APIs)
- Requires manual file movement (no autonomous actions)
- Defaults all tasks to "Medium" priority (no smart prioritization)
- Polls every 30 seconds (not real-time monitoring)
- Supports up to 1000 files (performance limit)

**Upgrade to Silver Tier for**:
- AI-powered priority analysis
- Automatic file movement with approval workflow
- Integration with email/WhatsApp
""".format(date=datetime.now().strftime("%Y-%m-%d"))

    handbook_path = vault_path / "Company_Handbook.md"
    handbook_path.write_text(handbook_template, encoding="utf-8")
    logger.info("✓ Created Company_Handbook.md")


def main(vault_path: str, overwrite: bool = False) -> None:
    """Initialize Bronze tier vault structure.

    Args:
        vault_path: Absolute path for new vault directory
        overwrite: If True, recreate folders/files even if they exist

    Raises:
        FileExistsError: If vault_path already exists and overwrite=False
        PermissionError: If vault_path parent directory is not writable

    Exit Codes:
        0: Success
        1: Invalid vault path or vault already exists
        3: Permission error (not writable)
    """
    vault = Path(vault_path).resolve()

    # Validate vault path
    if vault.exists() and not overwrite:
        if list(vault.iterdir()):  # Non-empty directory
            logger.error(f"Vault path already exists: {vault}")
            logger.error("Use --overwrite flag to recreate vault")
            sys.exit(1)

    try:
        # Create vault root directory
        vault.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing vault at {vault}")

        # Create folder structure
        logger.info("Creating folder structure...")
        create_folder_structure(vault)

        # Create Dashboard.md
        logger.info("Creating Dashboard.md...")
        create_dashboard(vault)

        # Create Company_Handbook.md
        logger.info("Creating Company_Handbook.md...")
        create_handbook(vault)

        # Success message
        logger.info("")
        logger.info(f"Vault initialized at {vault}")
        logger.info("Ready to use with Obsidian")
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  1. Open vault in Obsidian: {vault}")
        logger.info(f"  2. Start watcher: python scripts/watch_inbox.py {vault}")
        logger.info(f"  3. Drop test file in {vault}/Inbox/")

    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        logger.error(f"Cannot write to {vault.parent}")
        sys.exit(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize Bronze tier Personal AI Employee vault"
    )
    parser.add_argument(
        "vault_path",
        help="Path to vault directory (will be created if doesn't exist)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recreate vault even if it already exists"
    )

    args = parser.parse_args()
    main(args.vault_path, args.overwrite)
