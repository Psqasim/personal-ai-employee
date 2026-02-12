#!/usr/bin/env python3
"""Gmail Watcher for Silver Tier Personal AI Employee.

Polls Gmail API every 2 minutes for important unread emails and creates
task files in vault/Inbox/EMAIL_{id}.md.

Features:
- OAuth2 authentication with token refresh
- Polls "is:unread is:important" emails (maxResults=10)
- Creates EMAIL_{message_id}.md with YAML frontmatter
- Tracks processed IDs to prevent duplicates
- Error handling: 403 (auth expired), 429 (rate limit backoff), 500 (retry)
- Graceful shutdown via SIGINT/SIGTERM

Usage:
    python watchers/gmail_watcher.py
    python watchers/gmail_watcher.py --vault-path /path/to/vault

Environment:
    VAULT_PATH: Path to vault directory (required)
    GMAIL_CREDENTIALS_PATH: Path to OAuth2 credentials JSON
    GMAIL_POLL_INTERVAL: Polling interval in seconds (default: 120)
"""

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [gmail]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "personal-ai-employee"
TOKEN_PATH = CONFIG_DIR / "gmail_token.json"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
]

# Global flag for graceful shutdown
_watcher_running = True


def _signal_handler(signum, frame) -> None:
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global _watcher_running
    logger.info("Shutdown signal received, stopping Gmail watcher...")
    _watcher_running = False


def _get_vault_path() -> Path:
    """Get vault path from environment."""
    vault_path = os.getenv("VAULT_PATH", "vault")
    return Path(vault_path).expanduser().resolve()


def _load_env() -> None:
    """Load .env file from project root if present."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def _build_gmail_service():
    """Build authenticated Gmail API service.

    Returns:
        Google API service object or None if auth fails
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        logger.error(
            "Missing Google packages. Install: pip install google-api-python-client "
            "google-auth-httplib2 google-auth-oauthlib"
        )
        return None

    if not TOKEN_PATH.exists():
        logger.error(
            f"Gmail token not found at {TOKEN_PATH}. "
            "Run: python scripts/setup_gmail_auth.py"
        )
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GMAIL_SCOPES)

        if creds.expired and creds.refresh_token:
            logger.info("Refreshing Gmail OAuth2 token...")
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            logger.info("Token refreshed successfully")

        if not creds.valid:
            logger.error(
                "Gmail credentials invalid. Re-run: python scripts/setup_gmail_auth.py"
            )
            return None

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        return service

    except Exception as e:
        logger.error(f"Failed to build Gmail service: {e}")
        return None


def track_processed_ids(vault_path: Path, message_id: Optional[str] = None) -> bool:
    """Check or record a processed Gmail message ID.

    Prevents duplicate task creation for already-processed emails.

    Args:
        vault_path: Path to vault root
        message_id: If provided, check if already processed and record it.
                    If None, just initializes the tracking file.

    Returns:
        True if message_id was already processed (duplicate), False if new
    """
    processed_file = vault_path / "Logs" / "gmail_processed_ids.txt"
    processed_file.parent.mkdir(parents=True, exist_ok=True)

    if message_id is None:
        return False

    # Read existing IDs
    processed_ids: set = set()
    if processed_file.exists():
        try:
            processed_ids = set(processed_file.read_text(encoding="utf-8").splitlines())
        except Exception:
            pass

    if message_id in processed_ids:
        return True  # Already processed

    # Record new ID
    try:
        with processed_file.open("a", encoding="utf-8") as f:
            f.write(f"{message_id}\n")
    except Exception as e:
        logger.warning(f"Failed to record processed ID: {e}")

    return False


def create_email_task(vault_path: Path, message: Dict) -> Optional[Path]:
    """Create an EMAIL_{id}.md task file in vault/Inbox/.

    Args:
        vault_path: Path to vault root
        message: Gmail message dict with id, from, subject, snippet, internalDate

    Returns:
        Path to created file, or None if creation failed
    """
    message_id = message.get("id", "unknown")
    inbox_path = vault_path / "Inbox"
    inbox_path.mkdir(parents=True, exist_ok=True)

    task_file = inbox_path / f"EMAIL_{message_id}.md"

    if task_file.exists():
        return task_file  # Already exists

    sender = message.get("from", "Unknown Sender")
    subject = message.get("subject", "(No Subject)")
    snippet = message.get("snippet", "")[:200]
    received = message.get("received", datetime.now().isoformat())

    # Escape YAML special characters
    safe_subject = subject.replace('"', '\\"')
    safe_sender = sender.replace('"', '\\"')

    content = f"""---
type: email
from: "{safe_sender}"
subject: "{safe_subject}"
received: "{received}"
priority: high
status: pending
source: gmail
---

# {subject}

**From**: {sender}
**Received**: {received}

## Email Summary

{snippet}

## Suggested Actions

- [ ] Read full email
- [ ] Reply if needed
- [ ] File or archive when complete
"""

    try:
        task_file.write_text(content, encoding="utf-8")
        logger.info(f"Created email task: EMAIL_{message_id}.md")
        return task_file
    except Exception as e:
        logger.error(f"Failed to create email task for {message_id}: {e}")
        return None


def _log_error(vault_path: Path, error_msg: str) -> None:
    """Log error to vault/Logs/gmail_watcher_errors.md."""
    error_file = vault_path / "Logs" / "gmail_watcher_errors.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with error_file.open("a", encoding="utf-8") as f:
            f.write(f"## {timestamp}\n{error_msg}\n\n")
    except Exception:
        pass


def poll_gmail(service, vault_path: Path) -> List[Dict]:
    """Query Gmail API for unread important messages.

    Args:
        service: Authenticated Gmail API service
        vault_path: Vault root for logging

    Returns:
        List of message dicts with from, subject, snippet, received, id
    """
    try:
        result = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread is:important", maxResults=10)
            .execute()
        )
    except Exception as e:
        raise

    messages = result.get("messages", [])
    if not messages:
        return []

    email_data = []
    for msg_ref in messages:
        message_id = msg_ref["id"]

        # Skip already-processed messages
        if track_processed_ids(vault_path, None) and message_id in _load_processed_ids(vault_path):
            continue
        if _is_already_processed(vault_path, message_id):
            continue

        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="metadata",
                     metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )

            headers = {
                h["name"]: h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            # Convert internalDate (milliseconds) to ISO format
            internal_date_ms = int(msg.get("internalDate", "0"))
            received_dt = datetime.fromtimestamp(internal_date_ms / 1000)

            email_data.append({
                "id": message_id,
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "(No Subject)"),
                "snippet": msg.get("snippet", ""),
                "received": received_dt.isoformat(),
            })

        except Exception as e:
            logger.warning(f"Failed to fetch message {message_id}: {e}")

    return email_data


def _is_already_processed(vault_path: Path, message_id: str) -> bool:
    """Check if a message ID has been processed without recording it."""
    processed_file = vault_path / "Logs" / "gmail_processed_ids.txt"
    if not processed_file.exists():
        return False
    try:
        ids = set(processed_file.read_text(encoding="utf-8").splitlines())
        return message_id in ids
    except Exception:
        return False


def _load_processed_ids(vault_path: Path) -> set:
    """Load set of all processed message IDs."""
    processed_file = vault_path / "Logs" / "gmail_processed_ids.txt"
    if not processed_file.exists():
        return set()
    try:
        return set(processed_file.read_text(encoding="utf-8").splitlines())
    except Exception:
        return set()


async def main(vault_path_override: Optional[str] = None) -> None:
    """Main Gmail watcher entry point.

    Args:
        vault_path_override: Optional vault path (uses VAULT_PATH env if not set)
    """
    global _watcher_running

    _load_env()

    vault_path = Path(vault_path_override).resolve() if vault_path_override else _get_vault_path()
    poll_interval = int(os.getenv("GMAIL_POLL_INTERVAL", "120"))

    # Register signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logger.info(f"Starting Gmail watcher (poll interval: {poll_interval}s)")
    logger.info(f"Vault: {vault_path}")

    # Ensure Logs directory exists
    (vault_path / "Logs").mkdir(parents=True, exist_ok=True)

    backoff_seconds = 60

    while _watcher_running:
        service = _build_gmail_service()

        if service is None:
            logger.error("Cannot connect to Gmail API. Will retry in 60 seconds.")
            _log_error(vault_path, "Gmail service unavailable - credentials issue")
            await asyncio.sleep(60)
            continue

        try:
            emails = poll_gmail(service, vault_path)
            logger.info(f"Polled Gmail: {len(emails)} new important email(s)")

            for email in emails:
                # Skip already processed
                if track_processed_ids(vault_path, email["id"]):
                    continue

                # Create task file
                task_file = create_email_task(vault_path, email)
                if task_file:
                    track_processed_ids(vault_path, email["id"])

            backoff_seconds = 60  # Reset backoff on success

        except Exception as e:
            error_str = str(e)

            if "403" in error_str or "insufficient authentication" in error_str.lower():
                logger.error(
                    f"Gmail API 403 Forbidden: {e}\n"
                    "OAuth2 token expired. Run: python scripts/setup_gmail_auth.py"
                )
                _log_error(vault_path, f"403 Forbidden: {e}\nRun setup_gmail_auth.py to re-authorize.")
                # Pause watcher - requires manual re-authorization
                logger.info("Pausing Gmail watcher due to auth error. Manual re-auth required.")
                await asyncio.sleep(300)  # 5 minutes before retry
                continue

            elif "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                logger.warning(f"Gmail API rate limit (429): {e}. Backing off {backoff_seconds}s")
                _log_error(vault_path, f"Rate limit (429): {e}. Backoff: {backoff_seconds}s")
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 240)  # Max 4 min backoff
                continue

            elif "500" in error_str or "503" in error_str:
                logger.warning(f"Gmail API server error (5xx): {e}. Retrying next poll.")
                _log_error(vault_path, f"Server error (5xx): {e}")

            else:
                logger.error(f"Unexpected Gmail error: {e}")
                _log_error(vault_path, f"Unexpected error: {e}")

        await asyncio.sleep(poll_interval)

    logger.info("Gmail watcher stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gmail Watcher for Silver Tier AI Employee")
    parser.add_argument("--vault-path", help="Path to vault directory (overrides VAULT_PATH env)")
    args = parser.parse_args()

    asyncio.run(main(vault_path_override=args.vault_path))
