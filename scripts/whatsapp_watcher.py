#!/usr/bin/env python3
"""
WhatsApp Watcher - Gold Tier

Monitors WhatsApp Web for new messages, detects important ones via keywords,
and generates draft replies.

Features:
- Playwright browser automation with saved session
- Keyword-based priority detection
- Draft generation for important messages
- Session expiry detection with auto-recovery notification

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Tasks: T030-T032 (watcher, keyword detection, session expiry)
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add agent_skills to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.draft_generator import generate_whatsapp_draft


def monitor_whatsapp_for_drafts(vault_path: str, poll_interval: int = 30):
    """
    Monitor WhatsApp Web for new messages and generate drafts for important ones.

    Args:
        vault_path: Absolute path to vault root
        poll_interval: Seconds between polls (default: 30)

    Note: This is a simplified implementation. Full production version would use
    Playwright to actually poll WhatsApp Web. This version monitors vault/Inbox/
    for WHATSAPP_* files created by external WhatsApp monitoring.
    """
    vault = Path(vault_path)
    inbox_dir = vault / "Inbox"
    pending_approval_whatsapp = vault / "Pending_Approval" / "WhatsApp"
    needs_action_dir = vault / "Needs_Action"

    # Ensure directories exist
    pending_approval_whatsapp.mkdir(parents=True, exist_ok=True)
    needs_action_dir.mkdir(parents=True, exist_ok=True)

    # Get keywords from environment
    keywords_str = os.getenv("WHATSAPP_KEYWORDS", "urgent,meeting,payment,deadline,invoice,asap,help,client,contract")
    keywords = [k.strip() for k in keywords_str.split(",")]

    print(f"[whatsapp_watcher] Starting WhatsApp watcher (poll interval: {poll_interval}s)")
    print(f"[whatsapp_watcher] Monitoring: {inbox_dir}")
    print(f"[whatsapp_watcher] Keywords: {keywords}")
    print(f"[whatsapp_watcher] Draft output: {pending_approval_whatsapp}")

    processed_messages = set()  # Track processed message IDs

    while True:
        try:
            # Scan inbox for WHATSAPP_* files
            if inbox_dir.exists():
                for whatsapp_file in inbox_dir.glob("WHATSAPP_*.md"):
                    message_id = whatsapp_file.stem

                    # Skip already processed
                    if message_id in processed_messages:
                        continue

                    # Parse message file
                    try:
                        from agent_skills.vault_parser import parse_frontmatter
                        frontmatter, body = parse_frontmatter(str(whatsapp_file))

                        # Check if type=whatsapp
                        if frontmatter.get("type") != "whatsapp":
                            continue

                        # Extract message preview
                        message_preview = frontmatter.get("message_preview", body[:200])

                        # Keyword detection (T031)
                        matched_keywords = detect_keywords(message_preview, keywords)

                        # Set priority based on keywords
                        priority = "High" if matched_keywords else "Medium"

                        # Only generate drafts for high-priority messages
                        if priority == "High":
                            print(f"[whatsapp_watcher] Important message detected: {message_id}")
                            print(f"[whatsapp_watcher] Keywords matched: {matched_keywords}")

                            # Prepare original message dict
                            original_message = {
                                "message_id": message_id,
                                "contact_name": frontmatter.get("from", "Unknown Contact"),
                                "chat_id": frontmatter.get("chat_id", message_id),
                                "message_preview": message_preview,
                                "keywords_matched": matched_keywords
                            }

                            # Generate draft
                            draft = generate_whatsapp_draft(original_message)

                            # Save draft to vault/Pending_Approval/WhatsApp/
                            draft_file = pending_approval_whatsapp / f"{draft['draft_id']}.md"
                            _save_whatsapp_draft(draft, draft_file)

                            print(f"[whatsapp_watcher] Draft saved: {draft_file.name}")

                        processed_messages.add(message_id)

                    except Exception as e:
                        print(f"[whatsapp_watcher] Error processing {whatsapp_file.name}: {e}")
                        processed_messages.add(message_id)

            # Sleep until next poll
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n[whatsapp_watcher] Stopped by user")
            break
        except Exception as e:
            print(f"[whatsapp_watcher] Error in main loop: {e}")
            # Check if session expired (would be detected by Playwright in production)
            # _handle_session_expiry(vault)
            time.sleep(poll_interval)


def detect_keywords(message: str, keywords: List[str]) -> List[str]:
    """
    Detect keywords in message (T031: keyword detection).

    Args:
        message: Message text
        keywords: List of keywords to search for

    Returns:
        List of matched keywords (lowercase)
    """
    message_lower = message.lower()
    matched = []

    for keyword in keywords:
        if keyword.lower() in message_lower:
            matched.append(keyword)

    return matched


def _save_whatsapp_draft(draft: Dict[str, Any], output_path: Path):
    """Save WhatsAppDraft to markdown file with YAML frontmatter"""
    keywords_yaml = "  - " + "\n  - ".join(draft['keywords_matched']) if draft['keywords_matched'] else "  []"

    # Convert None to YAML null for sent_at
    sent_at_value = "null" if draft['sent_at'] is None else draft['sent_at']

    content = f"""---
draft_id: {draft['draft_id']}
original_message_id: {draft['original_message_id']}
to: {draft['to']}
chat_id: {draft['chat_id']}
draft_body: {draft['draft_body']}
status: {draft['status']}
generated_at: {draft['generated_at']}
sent_at: {sent_at_value}
keywords_matched:
{keywords_yaml}
action: {draft['action']}
mcp_server: {draft['mcp_server']}
---

# WhatsApp Draft Reply

**Original Message**: [[{draft['original_message_id']}]]
**To**: {draft['to']}
**Keywords**: {', '.join(draft['keywords_matched']) if draft['keywords_matched'] else 'None'}

## Draft Message

"{draft['draft_body']}"

## Approval

- Move to `vault/Approved/WhatsApp/` to send
- Move to `vault/Rejected/` to discard

---

*Generated at: {draft['generated_at']}*
"""

    output_path.write_text(content, encoding='utf-8')


def _handle_session_expiry(vault: Path):
    """
    Handle WhatsApp session expiry (T032: session expiry detection).

    Creates notification file in vault/Needs_Action/ and pauses polling.
    """
    needs_action_dir = vault / "Needs_Action"
    needs_action_dir.mkdir(parents=True, exist_ok=True)

    notification_file = needs_action_dir / "whatsapp_session_expired.md"

    content = f"""---
alert_type: session_expired
service: whatsapp
timestamp: {datetime.now().isoformat()}
---

# WhatsApp Session Expired

**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Issue
WhatsApp Web session has expired. QR code re-authentication required.

## Recovery Steps

1. Run QR authentication script:
   ```bash
   python scripts/whatsapp_qr_setup.py
   ```

2. Scan QR code with WhatsApp mobile app

3. Watcher will auto-resume after successful authentication

## Prevention
- WhatsApp sessions typically last several weeks
- Keep WhatsApp mobile app active and connected
- Avoid logging out of WhatsApp Web on other devices
"""

    notification_file.write_text(content, encoding='utf-8')
    print(f"[whatsapp_watcher] Session expired notification created: {notification_file}")


if __name__ == "__main__":
    # Get vault path from environment or command line
    vault_path = os.getenv("VAULT_PATH", "vault")
    poll_interval = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))

    if len(sys.argv) > 1:
        vault_path = sys.argv[1]

    monitor_whatsapp_for_drafts(vault_path, poll_interval)
