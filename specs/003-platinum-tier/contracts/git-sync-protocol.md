# Git Sync Protocol: Cloud ↔ Remote ↔ Local

**Version**: 1.0.0 | **Feature**: 003-platinum-tier | **Date**: 2026-02-15
**Purpose**: Define Git workflow, commit conventions, conflict resolution algorithm for dual-agent vault synchronization

---

## Overview

Platinum tier uses **Git as the communication layer** between Cloud Agent (Oracle VM, 24/7) and Local Agent (user's laptop, on-demand). Both agents push/pull from a shared Git remote repository (GitHub private repo) every 60 seconds.

**Key Principle**: Vault markdown files are the source of truth. Git is the sync mechanism.

---

## Git Workflow

### Cloud Agent Workflow (Push every 60s)

```
┌─────────────────────────────────────────┐
│ Cloud Agent Git Sync Cycle (60s)       │
└─────────────────────────────────────────┘

1. git add .
   ├─ Stage all changes in vault/
   └─ Includes: new drafts, Dashboard updates, logs

2. git diff HEAD --name-status
   └─ Detect changed files for commit message summary

3. if changes detected:
     ├─ git commit -m "Cloud: {summary}"
     │  └─ Summary: "3 email drafts, 1 LinkedIn post, Dashboard update"
     └─ git push origin main
        ├─ Retry on failure: 3x (10s, 30s, 90s backoff)
        └─ On final failure: queue to vault/.git_queue/pending_ops.md

4. Log sync status to vault/Logs/Cloud/git_sync.md
```

**Example Commit Messages**:
- `Cloud: 3 email drafts, Dashboard update`
- `Cloud: LinkedIn post, CEO Briefing generated`
- `Cloud: WhatsApp notification sent`

---

### Local Agent Workflow (Pull every 60s)

```
┌─────────────────────────────────────────┐
│ Local Agent Git Sync Cycle (60s)       │
└─────────────────────────────────────────┘

1. git fetch origin main
   └─ Download latest commits from remote

2. git pull --rebase origin main
   ├─ Rebase local commits onto Cloud's latest
   └─ Avoids merge commits (cleaner history)

3. if merge conflict detected:
     └─ Auto-resolve via conflict resolution algorithm (see below)

4. if auto-resolve succeeds:
     ├─ git add <resolved-files>
     ├─ git rebase --continue
     └─ Log resolution to vault/Logs/Local/git_conflicts.md

5. if auto-resolve fails:
     ├─ git rebase --abort
     ├─ Create vault/Needs_Action/git_conflict_manual_{timestamp}.md
     └─ Alert human via Dashboard notification

6. git push origin main (if local commits exist)

7. Log sync status to vault/Logs/Local/git_sync.md
```

**Example Commit Messages** (Local):
- `Local: Approved 3 emails, sent via Email MCP`
- `Local: Rejected LinkedIn post`
- `Local: WhatsApp draft approved, sent via WhatsApp MCP`

---

## Commit Message Convention

### Format

```
{Agent}: {Summary}

- {Detail 1}
- {Detail 2}
- {Detail 3}

Co-Authored-By: {Agent} <noreply@{agent}.ai>
```

### Examples

**Cloud Agent Commit**:
```
Cloud: 3 email drafts, 1 LinkedIn post, Dashboard update

- EMAIL_DRAFT_12345.md (reply to john@example.com)
- EMAIL_DRAFT_12346.md (reply to jane@example.com)
- EMAIL_DRAFT_12347.md (reply to client@corp.com)
- LINKEDIN_POST_2026-02-15.md (Product launch announcement)
- Dashboard.md (Updated pending approvals count)

Co-Authored-By: Cloud Agent <noreply@cloud.ai>
```

**Local Agent Commit**:
```
Local: Approved 2 emails, sent via Email MCP

- Moved EMAIL_DRAFT_12345.md to vault/Approved/Email/
- Moved EMAIL_DRAFT_12346.md to vault/Approved/Email/
- Email MCP: Sent 2 emails, logged to vault/Logs/MCP_Actions/2026-02-15.md

Co-Authored-By: Local Agent <noreply@local.ai>
```

---

## Conflict Resolution Algorithm

### File: `Dashboard.md` (Most Common Conflict)

**Problem**: Both Cloud and Local update `Dashboard.md` simultaneously.

**Solution**: Structured merge with section ownership.

#### Dashboard.md Structure

```markdown
# Personal AI Employee Dashboard

## Pending Approvals

| File | Added | Status | Priority |
|------|-------|--------|----------|
[... Local writes here ...]

## Updates

### 2026-02-15 14:30 (Cloud)
- Email draft created: EMAIL_DRAFT_12345.md
- LinkedIn post drafted: LINKEDIN_POST_2026-02-15.md

### 2026-02-15 14:25 (Cloud)
- CEO Briefing generation started
[... Cloud writes here ...]

## Statistics

- Tasks completed today: 15
- Pending approvals: 5
[... Local writes here ...]
```

#### Ownership Rules

| Section | Owner | Conflict Resolution |
|---------|-------|---------------------|
| `## Pending Approvals` | Local | Accept Local version (Local tracks approvals) |
| `## Updates` | Cloud | Accept Cloud version (Cloud pushes status updates) |
| `## Statistics` | Local | Accept Local version (Local computes stats) |

#### Auto-Resolve Implementation

**Python pseudocode** (`local_agent/src/git_sync.py`):

```python
import re

def auto_resolve_dashboard_conflict(conflict_file: str) -> bool:
    """Auto-resolve Dashboard.md merge conflicts."""
    with open(conflict_file, 'r') as f:
        content = f.read()

    # Extract conflict markers
    # <<<<<<< HEAD (Local)
    # ... local content ...
    # =======
    # ... cloud content (from remote) ...
    # >>>>>>> origin/main

    # Parse sections from both versions
    local_sections = extract_sections(content, marker='<<<<<<< HEAD', end='=======')
    cloud_sections = extract_sections(content, marker='=======', end='>>>>>>> origin/main')

    # Merge according to ownership rules
    merged = merge_sections({
        'pending_approvals': local_sections.get('pending_approvals'),  # Local owns
        'updates': cloud_sections.get('updates'),  # Cloud owns
        'statistics': local_sections.get('statistics'),  # Local owns
    })

    # Write resolved content
    with open(conflict_file, 'w') as f:
        f.write(merged)

    return True  # Auto-resolve succeeded
```

---

### File: Other Markdown Files

**Problem**: Cloud creates `EMAIL_DRAFT_12345.md`, Local approves and moves to `vault/Approved/Email/EMAIL_DRAFT_12345.md` simultaneously.

**Solution**: Timestamp-based resolution.

#### Rules

1. **File creation conflict** (rare): Accept most recent timestamp (from Git commit metadata)
2. **File modification conflict**: Accept version with latest `updated_at` in YAML frontmatter
3. **File deletion conflict**: If Cloud deleted and Local modified, accept Local version (Local has final authority)

---

### File: `.git_sync_state.md`

**Problem**: Both agents update sync state simultaneously.

**Solution**: Accept Local version (Local is source of truth for sync state).

---

## Conflict Logging

### Log Format (`vault/Logs/Local/git_conflicts.md`)

```markdown
---
date: 2026-02-15
total_conflicts_today: 3
auto_resolved: 3
manual_escalations: 0
---

## 14:30:45 - Dashboard.md (Auto-Resolved)

**Conflict Type**: Simultaneous update
**Resolution**: Cloud owns /Updates/, Local owns /Pending Approvals/, Local owns /Statistics/
**Outcome**: SUCCESS

**Diff Preview**:
```diff
<<<<<<< HEAD (Local)
## Pending Approvals
- 5 items pending
=======
## Pending Approvals
- 3 items pending
>>>>>>> origin/main

Resolved: Accepted Local version (5 items)
```

---

## Retry Policy

### Git Push Failure (Cloud Agent)

**Failure Scenarios**:
- Network timeout (Oracle VM network issue)
- Remote unreachable (GitHub down)
- Authentication failure (SSH key expired)

**Retry Strategy**:
```
Attempt 1: Immediate
Attempt 2: +10 seconds (exponential backoff)
Attempt 3: +30 seconds
Attempt 4: +90 seconds

If all fail:
  ├─ Queue operation to vault/.git_queue/pending_ops.md
  ├─ Send WhatsApp alert: "🚨 Git sync failing for 5+ min"
  └─ Continue processing other tasks (non-blocking)
```

### Git Pull Failure (Local Agent)

**Retry Strategy**: Same as push (3 retries, exponential backoff)

**On Final Failure**:
- Create `vault/Needs_Action/git_pull_failed_{timestamp}.md`
- Display Dashboard notification: "⚠️ Git sync offline - working locally"
- Continue operating with local vault (degrade gracefully)

---

## Security Rules

### .gitignore Enforcement

**MUST exclude** (enforced by pre-commit hook):

```gitignore
# Environment files
.env
.env.*

# Session files
*.session
*.pem
*.key

# Credentials
credentials.json
vault/.secrets/

# Build artifacts
node_modules/
__pycache__/
.next/
.pytest_cache/

# Logs (except vault/Logs/ which ARE synced)
*.log

# Backups
odoo_backups/
*.bak

# Database files
*.sqlite
*.db
```

### Pre-Commit Hook

**File**: `.git/hooks/pre-commit` (installed during setup)

```bash
#!/bin/bash
# Block commits of sensitive files

FORBIDDEN_PATTERNS=(
  ".env"
  "*.session"
  "credentials.json"
  "vault/.secrets/"
  "*.pem"
  "*.key"
)

STAGED_FILES=$(git diff --cached --name-only)

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  if echo "$STAGED_FILES" | grep -q "$pattern"; then
    echo "ERROR: Attempted to commit forbidden file matching: $pattern"
    echo "Blocked files:"
    echo "$STAGED_FILES" | grep "$pattern"
    exit 1  # Block commit
  fi
done

exit 0  # Allow commit
```

---

## Performance Optimization

### Shallow Clone (Optional for Cloud VM)

To reduce .git/ directory size on Cloud VM:

```bash
git clone --depth 1 git@github.com:user/ai-employee-vault.git
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
```

**Trade-off**: Loses full Git history, but reduces disk usage from ~500MB to ~50MB for large vaults.

**Recommendation**: Use full clone for Local (user has Git history), use shallow clone for Cloud (only needs latest state).

---

## Monitoring & Alerts

### Cloud Agent Git Sync Metrics

Logged to `vault/Logs/Cloud/git_sync.md`:

- `last_push_timestamp`: Most recent successful push
- `last_push_duration_seconds`: Time taken for last push
- `push_failures_today`: Count of failed pushes (resets daily)
- `total_commits_today`: Number of commits pushed

### Local Agent Git Sync Metrics

Logged to `vault/Logs/Local/git_sync.md`:

- `last_pull_timestamp`: Most recent successful pull
- `last_pull_duration_seconds`: Time taken for last pull
- `conflicts_auto_resolved_today`: Count of auto-resolved conflicts
- `conflicts_manual_escalations_today`: Count requiring human intervention

### Alert Triggers

| Condition | Alert | Delivery |
|-----------|-------|----------|
| Git remote unreachable >5 min | 🚨 Git sync offline | WhatsApp |
| >5 conflicts in 1 hour | ⚠️ Frequent conflicts, check agents | Dashboard |
| Manual conflict escalation | ⚠️ Git conflict needs human review | Dashboard + WhatsApp |
| .gitignore violation blocked | 🚨 Security: Attempted commit of .env | WhatsApp |

---

## Testing

### Conflict Simulation Test

**Scenario**: Cloud and Local both update Dashboard.md simultaneously.

**Steps**:
1. Cloud: Add entry to `/## Updates/` section
2. Local: Update Pending Approvals count
3. Cloud: `git add . && git commit -m "Cloud: Dashboard update" && git push`
4. Local: `git add . && git commit -m "Local: Approvals updated"`
5. Local: `git pull --rebase origin main` (triggers conflict)
6. Verify: Auto-resolve succeeds, Dashboard.md merged correctly
7. Verify: Conflict logged to `vault/Logs/Local/git_conflicts.md`

**Expected Result**: Dashboard.md contains Cloud's `/## Updates/` + Local's Pending Approvals.

---

**Git sync protocol complete. Ready for implementation in cloud_agent/src/git_sync.py and local_agent/src/git_sync.py.**
