# Phase 3 Complete Testing Guide
## Platinum Tier - Email Workflow End-to-End

**Date**: 2026-02-17
**Branch**: `003-platinum-tier`

---

## Overview

This guide validates the full email automation workflow:

```
Gmail → Cloud Agent → vault/Inbox/ → Draft → vault/Pending_Approval/
  → Dashboard Approve → vault/Approved/ → Local Agent → Email MCP → Sent
```

---

## Prerequisites

### Cloud VM (Oracle Cloud)
```bash
# SSH into VM
ssh ubuntu@<your-vm-ip>

# Verify environment
cd /opt/personal-ai-employee
cat .env.cloud | grep -E "TIER|VAULT_PATH|CLAUDE_API_KEY|GMAIL"

# Check PM2 status
pm2 list
# Expected: cloud_orchestrator (online), git_sync_cloud (online)
```

### Local Machine
```bash
cd /path/to/personal-ai-employee
cat .env | grep -E "VAULT_PATH|SMTP|GMAIL"

# Gmail token exists
ls ~/.config/personal-ai-employee/gmail_token.json
```

---

## Test 1: Gmail Watcher - New Email Detection

### Setup
1. Send a test email to your monitored Gmail account with subject: `[TEST] Platinum Phase 3`

### Execute (Cloud VM)
```bash
cd /opt/personal-ai-employee
source .env.cloud

# Run single poll manually
python -c "
import os
os.environ.setdefault('VAULT_PATH', os.getenv('VAULT_PATH', 'vault'))
from cloud_agent.src.watchers.gmail_watcher import CloudGmailWatcher
w = CloudGmailWatcher(os.getenv('VAULT_PATH'))
count = w.poll_once()
print(f'New emails found: {count}')
"
```

### Verify
```bash
ls vault/Inbox/EMAIL_*.md | tail -5
# Expected: New EMAIL_{id}.md file

cat vault/Inbox/EMAIL_*.md | head -20
# Expected YAML frontmatter:
# ---
# email_id: <gmail_id>
# from: <sender>
# subject: [TEST] Platinum Phase 3
# priority: Normal
# status: new
# ---
```

**Pass Criteria**: EMAIL_*.md created in vault/Inbox/ within 60 seconds

---

## Test 2: Email Draft Generation

### Execute (Cloud VM)
```bash
# Trigger orchestrator cycle manually
python -c "
import os
os.environ.setdefault('VAULT_PATH', os.getenv('VAULT_PATH', 'vault'))
from cloud_agent.src.orchestrator import CloudOrchestrator
orch = CloudOrchestrator()
orch.process_inbox()
"
```

### Verify
```bash
ls vault/Pending_Approval/Email/EMAIL_DRAFT_*.md | tail -5
# Expected: New EMAIL_DRAFT_{id}.md

cat vault/Pending_Approval/Email/EMAIL_DRAFT_*.md | head -30
# Expected:
# ---
# draft_id: EMAIL_DRAFT_...
# to: <sender_email>
# subject: Re: [TEST] Platinum Phase 3
# status: pending_approval
# action: send_email
# mcp_server: email-mcp
# ---
# <AI-generated reply body>
```

**Pass Criteria**: Draft created in vault/Pending_Approval/Email/ with valid YAML frontmatter

---

## Test 3: Dashboard Shows Pending Approval

### Execute (Local Machine)
```bash
# Start Next.js dashboard
cd nextjs_dashboard
npm run dev

# Open browser: http://localhost:3000
```

### Verify
- Dashboard shows approval card for the test email
- Card displays: recipient, subject, preview of AI-generated reply
- Approve/Reject buttons visible and clickable

**Pass Criteria**: Approval card appears within 5 seconds of dashboard load (polling)

---

## Test 4: Approval Handler - File Move and Email Send

### Execute (Local Machine - Dashboard)
1. Click **Approve** on the email draft card in the dashboard

### Verify file movement
```bash
# File should move from Pending to Approved
ls vault/Approved/Email/EMAIL_DRAFT_*.md

# Then move to Done after sending
ls vault/Done/EMAIL_DRAFT_*.md
```

### Verify email sent
```bash
# Check MCP action log
cat vault/Logs/MCP_Actions/email_sender.md | tail -5
# Expected: success entry with timestamp

# Check approval actions log
cat vault/Logs/Local/approval_actions.md | tail -5
# Expected: success entry
```

**Pass Criteria**: Email sent, file in vault/Done/, logs show success

---

## Test 5: Local Orchestrator Approval Loop (Automated)

### Execute (Local Machine)
```bash
# Run local orchestrator manually for one cycle
python -c "
import os
from local_agent.src.orchestrator import LocalOrchestrator
orch = LocalOrchestrator()
orch.process_approvals()
"
```

### Verify
- Any files in vault/Approved/Email/ are processed
- Logs updated in vault/Logs/Local/approval_actions.md

**Pass Criteria**: Approvals processed without manual dashboard interaction

---

## Test 6: Full End-to-End (Offline Scenario)

### Scenario: Email arrives while Local Agent is offline

**Step 1**: Stop local agent on laptop
```bash
# On local machine
# Do not run local orchestrator
```

**Step 2**: Send test email to Gmail (Cloud processes it)
```bash
# Wait 60-120 seconds for Cloud Agent cycle
pm2 logs cloud_orchestrator --lines 20
# Expected: "New email saved", "Draft created" log lines
```

**Step 3**: Start local agent on laptop
```bash
python local_agent/src/orchestrator.py
# Or: pm2 start ecosystem.config.local.js
```

**Step 4**: Approve via dashboard or vault file move
```bash
# Manual approval (moves file to Approved/)
mv vault/Pending_Approval/Email/EMAIL_DRAFT_*.md vault/Approved/Email/

# Local orchestrator picks it up in next 30s cycle
```

**Step 5**: Verify email sent
```bash
cat vault/Logs/MCP_Actions/email_sender.md | tail -3
```

**Pass Criteria**: Full flow works even when Local was offline during email arrival

---

## Test 7: Git Sync Verification

### Cloud → Local sync
```bash
# Cloud VM: verify git_sync_cloud is running
pm2 logs git_sync_cloud --lines 20
# Expected: periodic "Git sync: pushed X commit(s)" messages

# Local machine: pull and verify files
git pull
ls vault/Inbox/ vault/Pending_Approval/Email/
```

**Pass Criteria**: vault/Inbox/ files appear on Local within 60s of Cloud creating them

---

## Deployment to Oracle VM

After local testing passes, deploy to Cloud VM:

```bash
# 1. Commit and push new files
git add cloud_agent/ local_agent/ agent_skills/vault_parser.py docs/
git commit -m "[Platinum] Add approval_handler, email_sender, gmail_watcher, email_draft_gen"
git push origin 003-platinum-tier

# 2. On Oracle VM: pull and restart
ssh ubuntu@<vm-ip>
cd /opt/personal-ai-employee
git pull origin 003-platinum-tier
pm2 restart all --update-env
pm2 logs cloud_orchestrator --lines 30
```

---

## Quick Smoke Test Script

```bash
#!/bin/bash
# Run from project root on local machine

echo "=== Platinum Phase 3 Smoke Test ==="

echo "1. Checking vault structure..."
for dir in vault/Inbox vault/Pending_Approval/Email vault/Approved/Email vault/Done vault/Failed vault/Logs/Local vault/Logs/MCP_Actions; do
    mkdir -p "$dir"
    echo "   ✓ $dir"
done

echo "2. Checking new files exist..."
for f in \
    "local_agent/src/approval_handler.py" \
    "local_agent/src/executors/email_sender.py" \
    "cloud_agent/src/watchers/gmail_watcher.py" \
    "cloud_agent/src/generators/email_draft.py"; do
    [ -f "$f" ] && echo "   ✓ $f" || echo "   ✗ MISSING: $f"
done

echo "3. Python import check..."
python -c "
from local_agent.src.approval_handler import ApprovalHandler
from local_agent.src.executors.email_sender import EmailSender
from cloud_agent.src.generators.email_draft import EmailDraftGenerator
from cloud_agent.src.watchers.gmail_watcher import CloudGmailWatcher
from agent_skills.vault_parser import parse_email_from_vault
print('   ✓ All imports OK')
" 2>&1

echo "=== Done ==="
```

---

## Known Limitations

| Issue | Workaround |
|-------|-----------|
| Gmail OAuth token not on Cloud VM | Copy `~/.config/personal-ai-employee/gmail_token.json` to VM |
| Email MCP SMTP credentials only on Local | By design - Cloud drafts only, Local sends |
| WhatsApp notifier not yet implemented | Use email fallback (vault/Logs alerts) |
| Odoo integration not yet set up | Phase 9 (lower priority) |

---

## Next Steps After Tests Pass

1. Deploy to Oracle VM
2. Implement WhatsApp notifier (`cloud_agent/src/notifications/whatsapp_notifier.py`)
3. Add PM2 ecosystem configs (`deployment/pm2/`)
4. Run 30-day stability test

**See**: `specs/003-platinum-tier/tasks.md` for full task list
