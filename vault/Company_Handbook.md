---
version: 1.0.0
tier: bronze
last_updated: 2026-02-10
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
