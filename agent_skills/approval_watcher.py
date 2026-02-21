"""
Approval Watcher - Monitor vault/Approved/* and invoke MCP actions

This module monitors vault/Approved/* folders for human-approved drafts,
parses draft files, invokes appropriate MCP servers, and logs all actions.

Features:
- File-move detection via watchdog
- Filelock for race condition handling
- MCP invocation via mcp_client
- Comprehensive audit logging
- Graceful error handling with retries

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from filelock import FileLock

# Import local modules
from agent_skills.mcp_client import get_mcp_client
from agent_skills.vault_parser import parse_draft_file, detect_draft_type, parse_plan_file


def process_approval(file_path: str, approval_type: str) -> bool:
    """
    Process a single approved file and invoke MCP action.

    Args:
        file_path: Absolute path to approved file
        approval_type: Type of approval ("email", "whatsapp", "linkedin", "plan")

    Returns:
        True if successful, False if failed

    Raises:
        Exception: On critical errors (logged, not re-raised)
    """
    lock_path = file_path + '.lock'

    try:
        # Acquire lock (5s timeout to prevent race conditions)
        with FileLock(lock_path, timeout=5):
            # Check if already processed (idempotency)
            if _is_processed(file_path):
                print(f"[approval_watcher] Already processed: {file_path}")
                # Move stale file to Done so it stops looping
                if Path(file_path).exists():
                    try:
                        _move_to_done(file_path, status="sent")
                    except Exception as _me:
                        print(f"[approval_watcher] Could not move stale file to Done: {_me}")
                return True

            # Parse draft file
            if approval_type in ["email", "whatsapp", "linkedin", "odoo"]:
                draft = parse_draft_file(file_path, draft_type=approval_type)

                # Invoke MCP server
                result = _invoke_mcp_for_draft(draft, approval_type)

                # Log MCP action
                _log_mcp_action(draft, result, file_path)

                # Move to Done on success, Needs_Action on failure
                if result.get("success"):
                    _move_to_done(file_path, status="sent")
                    # Only mark processed on success (file is gone from Approved)
                    _mark_processed(file_path)
                else:
                    # Move file out of Approved so it doesn't loop as "already processed"
                    _move_to_needs_action(file_path, result.get("error", "Unknown error"))
                    # Do NOT mark processed — keeps it retriable after fix

            elif approval_type == "plan":
                # Plan execution handled by plan_executor.py
                print(f"[approval_watcher] Plan approval detected: {file_path}")
                # This would trigger Ralph Wiggum loop via plan_watcher.py
                return True

            return True

    except Exception as e:
        print(f"[approval_watcher] Error processing {file_path}: {e}")
        _log_error(file_path, str(e))
        return False


def _invoke_mcp_for_draft(draft: Any, draft_type: str) -> Dict[str, Any]:
    """
    Invoke appropriate MCP server for draft.

    Args:
        draft: Parsed draft object (EmailDraft, WhatsAppDraft, or LinkedInDraft)
        draft_type: Type of draft

    Returns:
        Dict with keys: success (bool), result (dict), error (str)
    """
    # Use default 90s timeout (changed from 30s to support browser automation)
    mcp_client = get_mcp_client()

    try:
        if draft_type == "email":
            # Invoke email-mcp send_email tool
            result = mcp_client.call_tool(
                mcp_server="email-mcp",
                tool_name="send_email",
                arguments={
                    "to": draft.to,
                    "subject": draft.subject,
                    "body": draft.draft_body
                },
                retry_count=3,
                retry_delay=5
            )
            return {"success": True, "result": result, "error": None}

        elif draft_type == "whatsapp":
            # Invoke whatsapp-mcp with extended timeout — browser automation needs 120-180s
            # (browser launch ~10s + WhatsApp Web load ~30s + login check ~60s + send ~10s)
            import threading
            whatsapp_client = get_mcp_client(timeout=180)  # 3min for full browser flow
            result_holder = {}

            def _send():
                try:
                    r = whatsapp_client.call_tool(
                        mcp_server="whatsapp-mcp",
                        tool_name="send_message",
                        arguments={
                            "chat_id": draft.chat_id,
                            "message": draft.draft_body
                        },
                        retry_count=1,
                        retry_delay=2
                    )
                    result_holder["result"] = r
                except Exception as e:
                    result_holder["error"] = str(e)

            t = threading.Thread(target=_send, daemon=True)
            t.start()
            t.join(timeout=185)  # 185s hard wall-clock limit (5s slack over MCP timeout)

            if t.is_alive():
                return {"success": False, "result": None, "error": "WhatsApp MCP timeout (185s) — session may be expired or browser stuck"}
            if "error" in result_holder:
                return {"success": False, "result": None, "error": result_holder["error"]}
            return {"success": True, "result": result_holder.get("result", {}), "error": None}

        elif draft_type == "linkedin":
            # Invoke linkedin-mcp create_post tool
            result = mcp_client.call_tool(
                mcp_server="linkedin-mcp",
                tool_name="create_post",
                arguments={
                    "text": draft.post_content,
                    "author_urn": os.getenv("LINKEDIN_AUTHOR_URN", "")
                },
                retry_count=3,
                retry_delay=5
            )
            return {"success": True, "result": result, "error": None}

        elif draft_type == "odoo":
            # T060: Invoke odoo-mcp for invoice or expense creation
            # Check if Odoo is enabled (T061: graceful degradation)
            if os.getenv("ENABLE_ODOO", "false").lower() != "true":
                print("[approval_watcher] Odoo MCP disabled (ENABLE_ODOO=false)")
                return {
                    "success": False,
                    "result": None,
                    "error": "Odoo MCP disabled. Set ENABLE_ODOO=true in .env to enable."
                }

            # Determine action type (invoice or expense)
            action_type = draft.action  # "create_draft_invoice" or "create_draft_expense"

            if action_type == "create_draft_invoice":
                result = mcp_client.call_tool(
                    mcp_server="odoo-mcp",
                    tool_name="create_draft_invoice",
                    arguments={
                        "customer": draft.odoo_data.get("customer"),
                        "amount": draft.odoo_data.get("amount"),
                        "description": draft.odoo_data.get("description"),
                        "invoice_date": draft.odoo_data.get("invoice_date")
                    },
                    retry_count=3,
                    retry_delay=5
                )
            elif action_type == "create_draft_expense":
                result = mcp_client.call_tool(
                    mcp_server="odoo-mcp",
                    tool_name="create_draft_expense",
                    arguments={
                        "vendor": draft.odoo_data.get("vendor"),
                        "amount": draft.odoo_data.get("amount"),
                        "description": draft.odoo_data.get("description"),
                        "expense_date": draft.odoo_data.get("expense_date")
                    },
                    retry_count=3,
                    retry_delay=5
                )
            else:
                return {"success": False, "result": None, "error": f"Unknown Odoo action: {action_type}"}

            return {"success": True, "result": result, "error": None}

        else:
            return {"success": False, "result": None, "error": f"Unknown draft type: {draft_type}"}

    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}


def _log_mcp_action(draft: Any, result: Dict, approval_file_path: str):
    """
    Log MCP action to vault/Logs/MCP_Actions/YYYY-MM-DD.md.

    Args:
        draft: Parsed draft object
        result: MCP invocation result
        approval_file_path: Path to approval file
    """
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))
    log_dir = vault_path / "Logs" / "MCP_Actions"
    log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.md"

    # Create log entry
    log_id = f"LOG_{int(datetime.now().timestamp())}"

    # Sanitize payload summary (no PII, max 50 chars)
    if hasattr(draft, 'to'):
        payload_summary = f"To: {draft.to[:20]}..."
    elif hasattr(draft, 'chat_id'):
        payload_summary = f"Chat: {draft.chat_id[:20]}..."
    else:
        payload_summary = "LinkedIn post"

    log_entry = f"""---
log_id: {log_id}
mcp_server: {draft.mcp_server}
action: {draft.action}
payload_summary: {payload_summary[:50]}
outcome: {'success' if result['success'] else 'failed'}
plan_id: null
step_num: null
timestamp: {datetime.now().isoformat()}
human_approved: true
approval_file_path: {approval_file_path}
error_message: {result.get('error', 'null')}
---

**Action**: {draft.mcp_server}.{draft.action}
**Outcome**: {'Success ✓' if result['success'] else 'Failed ✗'}
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Approval**: {approval_file_path}

"""

    # Append to log file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def _move_to_done(file_path: str, status: str = "sent"):
    """Move approved file to vault/Done/{subfolder}/ on success"""
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))

    file_path_obj = Path(file_path)
    # Preserve subfolder: vault/Approved/Email/ → vault/Done/Email/
    subfolder = file_path_obj.parent.name  # e.g. "Email", "WhatsApp", "LinkedIn"
    done_dir = vault_path / "Done" / subfolder
    done_dir.mkdir(parents=True, exist_ok=True)

    dest_path = done_dir / file_path_obj.name

    # Log file movement (T051)
    _log_approval_file_movement(str(file_path_obj), str(dest_path), "approved_and_executed")

    # Move file
    file_path_obj.rename(dest_path)


def _move_to_needs_action(file_path: str, error_message: str):
    """Move failed approval file to vault/Needs_Action/"""
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))
    needs_action_dir = vault_path / "Needs_Action"
    needs_action_dir.mkdir(parents=True, exist_ok=True)

    file_path_obj = Path(file_path)
    dest_path = needs_action_dir / f"retry_{file_path_obj.name}"

    # Copy original content + error details to retry file
    original_content = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception:
        pass

    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(f"""---
original_file: {file_path}
error: {error_message}
timestamp: {datetime.now().isoformat()}
---

# MCP Action Failed

**Original File**: {file_path}
**Error**: {error_message}
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Original Content
{original_content}

## Recovery Actions
1. Check MCP server logs for details
2. Verify MCP server configuration in .env
3. Retry manually or move back to vault/Approved/
""")

    # Remove original from Approved so it doesn't get reprocessed
    try:
        file_path_obj.unlink()
    except Exception as e:
        print(f"[approval_watcher] Warning: could not remove original {file_path}: {e}")


def _is_processed(file_path: str) -> bool:
    """Check if file has already been processed (idempotency check)"""
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))
    processed_log = vault_path / "Logs" / "processed_approvals.json"

    if not processed_log.exists():
        return False

    with open(processed_log, 'r', encoding='utf-8') as f:
        processed_files = json.load(f)

    return file_path in processed_files


def _mark_processed(file_path: str):
    """Mark file as processed in log"""
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))
    log_dir = vault_path / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    processed_log = log_dir / "processed_approvals.json"

    # Load existing
    if processed_log.exists():
        with open(processed_log, 'r', encoding='utf-8') as f:
            processed_files = json.load(f)
    else:
        processed_files = []

    # Append
    processed_files.append(file_path)

    # Write back
    with open(processed_log, 'w', encoding='utf-8') as f:
        json.dump(processed_files, f, indent=2)


def _log_approval_file_movement(source_path: str, dest_path: str, action: str):
    """
    Log approval file movements to vault/Logs/Human_Approvals/.

    Task: T051 [US5] Add approval file movement logging

    Args:
        source_path: Source file path (e.g., vault/Approved/Email/...)
        dest_path: Destination file path (e.g., vault/Done/...)
        action: Action taken (approved_and_executed, rejected, failed_and_moved)
    """
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))
    approval_log_dir = vault_path / "Logs" / "Human_Approvals"
    approval_log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    approval_log = approval_log_dir / f"{today}.md"

    log_entry = f"""
## File Movement at {datetime.now().strftime('%H:%M:%S')}
**Source**: {source_path}
**Destination**: {dest_path}
**Action**: {action}
**Timestamp**: {datetime.now().isoformat()}
"""

    with open(approval_log, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def _log_error(file_path: str, error_message: str):
    """Log error to vault/Logs/Error_Recovery/"""
    vault_path = Path(os.getenv("VAULT_PATH", "vault"))
    error_log_dir = vault_path / "Logs" / "Error_Recovery"
    error_log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    error_log = error_log_dir / f"{today}.md"

    with open(error_log, 'a', encoding='utf-8') as f:
        f.write(f"""
## Error at {datetime.now().strftime('%H:%M:%S')}
**File**: {file_path}
**Error**: {error_message}
""")


# Example usage
if __name__ == "__main__":
    # Example: Process approved email draft
    test_file = "vault/Approved/Email/EMAIL_DRAFT_test_001.md"
    success = process_approval(test_file, approval_type="email")
    print(f"Approval processed: {success}")
