"""
Gmail Watcher (Cloud Agent)

Monitors Gmail inbox every 60 seconds for new unread/important emails.
Creates EMAIL_*.md task files in vault/Inbox/ for the Cloud Orchestrator
to pick up and generate draft replies for.

Reuses: watchers/gmail_watcher.py (Silver/Gold tier Gmail auth + polling logic)
"""
import os
import sys
import time
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Graceful shutdown flag
_running = True


def _signal_handler(signum, frame) -> None:
    global _running
    logger.info("Shutdown signal received, stopping Cloud Gmail watcher...")
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


class CloudGmailWatcher:
    """
    Cloud-side Gmail watcher.

    Polls Gmail every GMAIL_POLL_INTERVAL seconds (default: 60).
    Writes EMAIL_{id}.md files to vault/Inbox/ for orchestrator processing.

    Delegates auth, token refresh, and API calls to the shared
    watchers/gmail_watcher.py (Silver tier) functions.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / "Inbox"
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        self.poll_interval = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))

        # Processed IDs file to prevent duplicates across restarts
        self.processed_ids_file = self.vault_path / "Logs" / "Cloud" / "gmail_processed_ids.txt"
        self.processed_ids_file.parent.mkdir(parents=True, exist_ok=True)
        self._processed_ids: set = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        """Load previously processed Gmail message IDs from disk."""
        if self.processed_ids_file.exists():
            ids = set(self.processed_ids_file.read_text().splitlines())
            logger.debug(f"Loaded {len(ids)} processed Gmail IDs")
            return ids
        return set()

    def _save_processed_id(self, message_id: str) -> None:
        """Append a processed message ID to disk."""
        self._processed_ids.add(message_id)
        with open(self.processed_ids_file, "a", encoding="utf-8") as f:
            f.write(message_id + "\n")

    def _build_gmail_service(self):
        """Build Gmail API service using shared Silver tier auth logic."""
        try:
            # Re-use path constants from the shared watcher
            sys.path.insert(0, str(project_root / "watchers"))
            from gmail_watcher import _build_gmail_service as _shared_build
            return _shared_build()
        except ImportError:
            logger.warning("Shared gmail_watcher not available, building directly")
            return self._build_gmail_service_direct()

    def _build_gmail_service_direct(self):
        """Fallback: build Gmail service directly."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            logger.error("Google packages not installed. Run: pip install google-api-python-client google-auth-oauthlib")
            return None

        token_path = Path.home() / ".config" / "personal-ai-employee" / "gmail_token.json"
        if not token_path.exists():
            logger.error(f"Gmail token not found: {token_path}. Run: python scripts/setup_gmail_auth.py")
            return None

        try:
            scopes = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.labels",
            ]
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
            if not creds.valid:
                logger.error("Gmail credentials invalid. Re-authenticate.")
                return None
            return build("gmail", "v1", credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return None

    def fetch_unread_emails(self, service) -> list:
        """
        Fetch unread important emails from Gmail.

        Returns:
            List of email dicts with keys: email_id, from, subject, body, priority, received_at
        """
        emails = []
        try:
            results = service.users().messages().list(
                userId="me",
                q="is:unread is:important",
                maxResults=10,
            ).execute()

            messages = results.get("messages", [])
            for msg_ref in messages:
                msg_id = msg_ref["id"]
                if msg_id in self._processed_ids:
                    continue

                try:
                    msg = service.users().messages().get(
                        userId="me", id=msg_id, format="full"
                    ).execute()

                    email_data = self._parse_gmail_message(msg)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg_id}: {e}")

        except Exception as e:
            logger.error(f"Gmail API error: {e}")

        return emails

    def _parse_gmail_message(self, msg: dict) -> Optional[dict]:
        """Parse a Gmail API message into a flat email dict."""
        try:
            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            msg_id = msg["id"]
            sender = headers.get("from", "unknown@unknown.com")
            subject = headers.get("subject", "(no subject)")
            received_at = headers.get("date", datetime.now().isoformat())

            # Extract body text
            body = self._extract_body(msg.get("payload", {}))

            # Determine priority
            label_ids = msg.get("labelIds", [])
            priority = "High" if "IMPORTANT" in label_ids else "Normal"

            return {
                "email_id": msg_id,
                "from": sender,
                "subject": subject,
                "body": body[:2000],  # Cap body at 2000 chars
                "priority": priority,
                "received_at": received_at,
                "label_ids": label_ids,
            }
        except Exception as e:
            logger.warning(f"Failed to parse Gmail message: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from Gmail payload."""
        import base64

        mime_type = payload.get("mimeType", "")

        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

        # Multipart: recurse through parts
        for part in payload.get("parts", []):
            text = self._extract_body(part)
            if text:
                return text

        return ""

    def write_to_inbox(self, email_data: dict) -> Path:
        """
        Write email data to vault/Inbox/EMAIL_{id}.md.

        Args:
            email_data: Parsed email dict

        Returns:
            Path to created file
        """
        msg_id = email_data["email_id"]
        file_path = self.inbox_path / f"EMAIL_{msg_id}.md"

        if file_path.exists():
            return file_path

        content = (
            f"---\n"
            f"email_id: {msg_id}\n"
            f"from: {email_data['from']}\n"
            f"subject: {email_data['subject']}\n"
            f"priority: {email_data.get('priority', 'Normal')}\n"
            f"received_at: {email_data.get('received_at', datetime.now().isoformat())}\n"
            f"status: new\n"
            f"---\n\n"
            f"{email_data.get('body', '')}\n"
        )

        file_path.write_text(content, encoding="utf-8")
        self._save_processed_id(msg_id)
        logger.info(f"📧 New email saved: {file_path.name} | From: {email_data['from']}")
        return file_path

    def poll_once(self) -> int:
        """
        Run a single Gmail poll cycle.

        Returns:
            Number of new emails written to vault/Inbox/
        """
        service = self._build_gmail_service()
        if service is None:
            logger.warning("Gmail service unavailable, skipping poll")
            return 0

        emails = self.fetch_unread_emails(service)
        count = 0
        for email_data in emails:
            self.write_to_inbox(email_data)
            count += 1

        if count:
            logger.info(f"📬 {count} new email(s) added to inbox")
        else:
            logger.debug("No new emails")

        return count

    def run(self) -> None:
        """
        Main loop: poll Gmail every GMAIL_POLL_INTERVAL seconds (default: 60s).
        Runs until SIGINT/SIGTERM.
        """
        global _running
        logger.info(f"🔍 Cloud Gmail Watcher started (poll interval: {self.poll_interval}s)")

        while _running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Gmail watcher error: {e}")

            # Sleep in small increments so shutdown is fast
            for _ in range(self.poll_interval):
                if not _running:
                    break
                time.sleep(1)

        logger.info("Cloud Gmail Watcher stopped")


if __name__ == "__main__":
    import os
    vault = os.getenv("VAULT_PATH", "vault")
    watcher = CloudGmailWatcher(vault)
    watcher.run()
