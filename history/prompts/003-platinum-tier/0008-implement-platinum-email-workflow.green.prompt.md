---
id: "0008"
title: Implement Platinum Email Workflow
stage: green
date: 2026-02-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: 003-platinum-tier
branch: 003-platinum-tier
user: ps_qasim
command: /sp.implement
labels: ["platinum","email","approval-handler","gmail-watcher","mcp","orchestrator"]
links:
  spec: specs/003-platinum-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - local_agent/src/approval_handler.py
  - local_agent/src/executors/email_sender.py
  - cloud_agent/src/watchers/gmail_watcher.py
  - cloud_agent/src/generators/email_draft.py
  - cloud_agent/src/orchestrator.py
  - local_agent/src/orchestrator.py
  - agent_skills/vault_parser.py
  - docs/platinum/phase3-complete-testing.md
tests:
  - docs/platinum/phase3-complete-testing.md (manual smoke test script)
---

## Prompt

Implement missing Platinum tier components based on this analysis:

HIGH PRIORITY - Build these files:

1. local_agent/src/approval_handler.py - Monitors vault/Approved/ folder every 30 seconds, detects new .md files, parses frontmatter (type, to, subject, content), routes to correct executor based on type (email/linkedin/whatsapp), moves file to vault/Done/ on success, vault/Failed/ on error, logs all actions to vault/Logs/Local/

2. local_agent/src/executors/email_sender.py - Reads approved email .md file, extracts to/subject/content from frontmatter, calls existing mcp_servers/email_mcp/ to send, returns success/failure status, logs to vault/Logs/MCP_Actions/

3. cloud_agent/src/watchers/gmail_watcher.py - Monitors Gmail inbox every 60 seconds, detects new emails, creates draft files in vault/Pending_Approval/Email/, uses existing Gold tier gmail watcher pattern, runs 24/7 on Oracle VM

4. cloud_agent/src/generators/email_draft.py - Takes raw email data, uses Claude API to generate smart reply draft, saves to vault/Pending_Approval/Email/, follows existing Gold tier pattern

5. Update cloud_agent/src/orchestrator.py - Add main scanning loop (every 30s), integrate gmail_watcher, integrate email_draft generator, add proper logging

6. Update local_agent/src/orchestrator.py - Add approval_handler integration, add main loop, add proper logging

IMPORTANT: Reuse ALL existing Gold tier code from agent_skills/, reuse mcp_servers/email_mcp/ for sending, follow patterns in watchers/gmail_watcher.py (Gold tier)

After implementation: Test locally first, then deploy to Oracle VM with git pull + pm2 restart all. Create docs/platinum/phase3-complete-testing.md with test steps

## Response snapshot

Implemented 8 files covering the full Platinum email automation workflow:

1. **local_agent/src/approval_handler.py** - ApprovalHandler class scans vault/Approved/{Email,WhatsApp,LinkedIn,Odoo}/ every cycle, delegates to agent_skills/approval_watcher.process_approval(), moves failures to vault/Failed/, logs to vault/Logs/Local/approval_actions.md

2. **local_agent/src/executors/email_sender.py** - EmailSender class reads .md frontmatter (to, subject, draft_body), calls email-mcp send_email via MCPClient, logs to vault/Logs/MCP_Actions/email_sender.md

3. **cloud_agent/src/watchers/gmail_watcher.py** - CloudGmailWatcher polls Gmail every 60s, writes EMAIL_{id}.md to vault/Inbox/, persists processed IDs to prevent duplicates, reuses Silver tier auth/token logic

4. **cloud_agent/src/generators/email_draft.py** - EmailDraftGenerator wraps agent_skills/draft_generator.generate_email_draft(), saves to vault/Pending_Approval/Email/ with full YAML frontmatter, idempotent (skips if draft exists)

5. **cloud_agent/src/orchestrator.py** (updated) - Added poll_gmail() method + CloudGmailWatcher init, orchestration_cycle now calls poll_gmail → process_inbox → generate_social_drafts → send_notifications

6. **local_agent/src/orchestrator.py** (updated) - process_approvals() now instantiates ApprovalHandler and calls run_once()

7. **agent_skills/vault_parser.py** (updated) - Added parse_email_from_vault() function that parses EMAIL_*.md frontmatter into flat email dict (was imported by orchestrator but missing)

8. **docs/platinum/phase3-complete-testing.md** - 7-test guide covering Gmail detection → draft generation → dashboard approval → email send → git sync; includes smoke test bash script and deployment steps for Oracle VM

All 7 Python files pass compile/syntax check.
---
