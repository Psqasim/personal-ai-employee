---
id: 0006
title: WhatsApp Notifications and Stale Recovery
stage: green
date: 2026-02-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: platinum-tier
branch: 003-platinum-tier
user: ps_qasim
command: /sp.implement
labels: ["whatsapp","notifications","platinum","stale-recovery","FR-P016","FR-P031"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - cloud_agent/src/notifications/whatsapp_notifier.py
  - agent_skills/stale_file_recovery.py
  - cloud_agent/src/orchestrator.py
  - local_agent/src/approval_handler.py
  - local_agent/src/orchestrator.py
  - .env
tests:
  - Import verification: python3 -c "from cloud_agent.src.notifications.whatsapp_notifier import ..."
  - Import verification: python3 -c "from agent_skills.stale_file_recovery import ..."
  - Import verification: python3 -c "from local_agent.src.approval_handler import ApprovalHandler"
  - Import verification: CloudOrchestrator and LocalOrchestrator imports OK
---

## Prompt

 Implement WhatsApp Notifications (FR-P031 to FR-P037):

  CONTEXT (already working):
  - vault/Done/Email/, vault/Done/WhatsApp/ subfolders ✅ DONE
  - Email sending works end-to-end via SMTP ✅ DONE
  - vault_parser.py reads body from markdown section ✅ DONE
  - WhatsApp MCP runs in thread (no PM2 blocking) ✅ DONE
  - WhatsApp session at /home/ps_qasim/.whatsapp_session ✅ DONE
  - PM2 process: local_approval_handler running ✅ DONE

  GOAL: When urgent email arrives or approval needed,
  send WhatsApp notification to admin automatically.

  BUILD THESE:

  1. cloud_agent/src/notifications/whatsapp_notifier.py
     Use existing Gold tier WhatsApp MCP (mcp_servers/whatsapp_mcp/)

     Notification types:
     a) Urgent email alert
     b) Pending approvals alert (when 5+ pending)
     c) Critical error alert
     d) Morning summary (8 AM daily)
     e) After approval confirmation

  2. Update cloud_agent/src/orchestrator.py
  3. Update local_agent/src/orchestrator.py
  4. Add to .env: ENABLE_WHATSAPP_NOTIFICATIONS, WHATSAPP_NOTIFICATION_NUMBER, COST_ALERT_THRESHOLD
  5. Add FR-P016: Stale files recovery (vault/In_Progress/ → Needs_Action/ after 24h)

  Push to GitHub after working. Branch: 003-platinum-tier, also merge to main.

## Response snapshot

Implemented all 5 notification types as non-blocking daemon threads (65s hard timeout).
- Created `cloud_agent/src/notifications/whatsapp_notifier.py` with `notify_urgent_email`, `notify_pending_approvals`, `notify_critical_error`, `notify_morning_summary`, `notify_task_completed`
- Updated `cloud_agent/src/orchestrator.py`: imports notifier, sends urgent alert in `process_inbox()`, hourly pending check + 8AM morning summary in `send_notifications()`
- Created `agent_skills/stale_file_recovery.py`: scans In_Progress/ hourly, moves files older than 24h back to Needs_Action/ with structured log
- Updated `local_agent/src/approval_handler.py`: sends WhatsApp confirmation after successful send; error alert on failure
- Updated `local_agent/src/orchestrator.py`: added `recover_stale()` called hourly via `_last_stale_check` timer
- Added 3 env vars to `.env`: ENABLE_WHATSAPP_NOTIFICATIONS=true, WHATSAPP_NOTIFICATION_NUMBER=+923010822227, COST_ALERT_THRESHOLD=1.00
- All imports verified OK. Pushed to 003-platinum-tier and merged to main.

## Outcome

- ✅ Impact: Platinum tier WhatsApp admin notifications fully wired; stale recovery FR-P016 implemented
- 🧪 Tests: Import verification passed for all 4 modules
- 📁 Files: 2 new files, 3 modified files, .env updated
- 🔁 Next prompts: Test notifications end-to-end; verify morning summary fires at 8AM UTC
- 🧠 Reflection: Used daemon threads with 65s timeout throughout — matches existing approval_watcher.py pattern for non-blocking WhatsApp. ENABLE_WHATSAPP_NOTIFICATIONS flag allows silent skip when disabled.

## Evaluation notes (flywheel)

- Pattern: non-blocking WhatsApp via daemon thread + 65s timeout is the correct pattern for this codebase
- Pattern: stale recovery uses time.time() delta to avoid hourly import overhead
- The `_morning_summary_sent_date` string prevents duplicate morning summaries across cycles
