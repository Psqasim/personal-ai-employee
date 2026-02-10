#!/usr/bin/env python3
"""File Watcher Script for Bronze Tier Personal AI Employee.

Monitors vault/Inbox/ for new .md files and updates Dashboard.md automatically.
Polling-based approach with 30-second intervals (configurable via Company_Handbook.md).
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.dashboard_updater import update_dashboard
from agent_skills.vault_watcher import validate_handbook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Global state for graceful shutdown
watcher_running = True


def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global watcher_running
    logger.info("Shutdown signal received, stopping watcher...")
    watcher_running = False


def detect_new_files(vault_path: Path, processed_files: Set[str]) -> List[Tuple[str, str]]:
    """Detect new .md files in Inbox/ folder.

    Args:
        vault_path: Path to vault root directory
        processed_files: Set of already-processed filenames

    Returns:
        List of (filename, status) tuples for new files
    """
    inbox_path = vault_path / "Inbox"

    if not inbox_path.exists():
        return []

    new_files = []

    try:
        for file_path in inbox_path.glob("*.md"):
            relative_path = f"Inbox/{file_path.name}"

            if relative_path not in processed_files:
                new_files.append((relative_path, "Inbox"))

    except PermissionError:
        logger.warning("Permission denied accessing Inbox folder")

    return new_files


def log_event(vault_path: Path, event_type: str, details: Dict) -> None:
    """Log event to daily watcher log file.

    Args:
        vault_path: Path to vault root directory
        event_type: Event type (file_detected, dashboard_updated, error)
        details: Event details dictionary
    """
    logs_path = vault_path / "Logs"
    logs_path.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    log_file = logs_path / f"watcher-{date_str}.md"

    # Format event
    event_title = event_type.replace("_", " ").title()
    event_lines = [f"## {time_str} - {event_title}\n"]

    for key, value in details.items():
        key_formatted = key.replace("_", " ").title()
        event_lines.append(f"- {key_formatted}: {value}\n")

    event_lines.append("\n")

    # Append to log file
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.writelines(event_lines)
    except Exception as e:
        logger.error(f"Failed to write log: {e}")


def poll_inbox(vault_path: Path, config: Dict) -> None:
    """Main polling loop - monitors Inbox/ and updates Dashboard.

    Args:
        vault_path: Path to vault root directory
        config: Configuration dictionary (polling_interval, etc.)
    """
    global watcher_running

    processed_files: Set[str] = set()
    polling_interval = config.get("polling_interval", 30)

    logger.info(f"Starting file watcher (polling interval: {polling_interval}s)")
    logger.info(f"Monitoring: {vault_path / 'Inbox'}")

    # Log watcher started event
    log_event(vault_path, "watcher_started", {
        "vault_path": str(vault_path),
        "polling_interval": f"{polling_interval} seconds"
    })

    while watcher_running:
        try:
            # Detect new files
            new_files = detect_new_files(vault_path, processed_files)

            if new_files:
                logger.info(f"Detected {len(new_files)} new file(s)")

                # Log detection
                for filename, _ in new_files:
                    log_event(vault_path, "file_detected", {
                        "file": filename
                    })

                # Update dashboard
                success = update_dashboard(str(vault_path), new_files)

                if success:
                    logger.info("Dashboard updated successfully")
                    log_event(vault_path, "dashboard_updated", {
                        "new_tasks": len(new_files),
                        "total_tasks": len(processed_files) + len(new_files)
                    })

                    # Mark files as processed
                    for filename, _ in new_files:
                        processed_files.add(filename)
                else:
                    logger.error("Dashboard update failed")
                    log_event(vault_path, "dashboard_update_failed", {
                        "files": ", ".join([f[0] for f in new_files])
                    })

        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            log_event(vault_path, "error", {
                "message": str(e)
            })

        # Sleep until next cycle
        time.sleep(polling_interval)

    # Log watcher stopped
    log_event(vault_path, "watcher_stopped", {
        "reason": "Graceful shutdown",
        "files_processed": len(processed_files)
    })
    logger.info("Watcher stopped")


def main(vault_path: str, config: Dict = None) -> None:
    """Entry point for inbox file watcher.

    Args:
        vault_path: Absolute path to vault root directory
        config: Optional configuration overrides

    Exit Codes:
        0: Graceful shutdown
        1: Invalid vault path
        2: Handbook validation failed
        3: Permission error
    """
    if config is None:
        config = {}

    vault = Path(vault_path).resolve()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate vault structure
    logger.info("Validating vault structure...")

    required_folders = ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]
    for folder in required_folders:
        folder_path = vault / folder
        if not folder_path.exists():
            logger.error(f"Missing required folder: {folder}/")
            logger.error("Run: python scripts/init_vault.py <vault-path>")
            sys.exit(1)

    if not (vault / "Dashboard.md").exists():
        logger.error("Dashboard.md not found")
        sys.exit(1)

    if not (vault / "Company_Handbook.md").exists():
        logger.error("Company_Handbook.md not found")
        sys.exit(1)

    logger.info("✓ Vault structure valid")

    # Validate handbook
    logger.info("Validating Company_Handbook.md...")
    try:
        is_valid, missing = validate_handbook(str(vault))
        if not is_valid:
            logger.error(f"Handbook validation failed. Missing sections: {', '.join(missing)}")
            sys.exit(2)
        logger.info("✓ Handbook validation passed")
    except Exception as e:
        logger.error(f"Handbook validation error: {e}")
        sys.exit(2)

    # Start polling
    try:
        poll_inbox(vault, config)
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        sys.exit(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor vault/Inbox/ for new markdown files"
    )
    parser.add_argument(
        "vault_path",
        help="Path to vault directory"
    )
    parser.add_argument(
        "--polling-interval",
        type=int,
        default=30,
        help="Polling interval in seconds (default: 30)"
    )

    args = parser.parse_args()

    config = {
        "polling_interval": args.polling_interval
    }

    main(args.vault_path, config)
