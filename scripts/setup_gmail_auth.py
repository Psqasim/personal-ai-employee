#!/usr/bin/env python3
"""Gmail OAuth2 Authorization Setup for Silver Tier Personal AI Employee.

Runs a local OAuth2 authorization flow to obtain Gmail API credentials.
Saves the refresh token to ~/.config/personal-ai-employee/gmail_token.json.

Usage:
    python scripts/setup_gmail_auth.py

Prerequisites:
    1. Create a Google Cloud project at https://console.cloud.google.com/
    2. Enable Gmail API
    3. Create OAuth2 credentials (Desktop application type)
    4. Download credentials JSON and set GMAIL_CREDENTIALS_PATH in .env
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
]

CONFIG_DIR = Path.home() / ".config" / "personal-ai-employee"
TOKEN_PATH = CONFIG_DIR / "gmail_token.json"


def setup_gmail_auth() -> bool:
    """Run Gmail OAuth2 authorization flow.

    Returns:
        True if authorization succeeded, False otherwise
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        logger.error(
            "Missing Google auth packages. Install with:\n"
            "  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
        )
        return False

    # Load .env if available
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "")
    if not credentials_path:
        logger.error(
            "GMAIL_CREDENTIALS_PATH not set in .env\n"
            "Download OAuth2 credentials from Google Cloud Console and set the path."
        )
        return False

    credentials_file = Path(credentials_path).expanduser().resolve()
    if not credentials_file.exists():
        logger.error(f"Credentials file not found: {credentials_file}")
        logger.error(
            "Download OAuth2 credentials (Desktop app type) from:\n"
            "  https://console.cloud.google.com/apis/credentials"
        )
        return False

    # Create config directory
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Check for existing valid token
    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            logger.info(f"Found existing token at {TOKEN_PATH}")
        except Exception:
            creds = None

    if creds and creds.valid:
        logger.info("Existing token is valid. No re-authorization needed.")
        return True

    if creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired token...")
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            logger.info(f"Token refreshed and saved to {TOKEN_PATH}")
            return True
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}. Re-authorizing...")

    # Run authorization flow
    logger.info("Starting OAuth2 authorization flow...")
    logger.info("A browser window will open. Please authorize access to your Gmail.")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
        creds = flow.run_local_server(port=0)
    except Exception as e:
        logger.error(f"Authorization failed: {e}")
        return False

    # Save token
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    logger.info(f"Authorization successful! Token saved to {TOKEN_PATH}")
    logger.info("You can now start the Gmail watcher with: pm2 start ecosystem.config.js")

    return True


if __name__ == "__main__":
    success = setup_gmail_auth()
    sys.exit(0 if success else 1)
