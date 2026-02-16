# Data Model: Platinum Tier Entities

**Feature**: 003-platinum-tier | **Date**: 2026-02-15
**Purpose**: Define all entities, attributes, relationships, state transitions, and validation rules for Platinum tier

---

## Entity Definitions

### 1. CloudAgent (New in Platinum)

**Description**: Represents the always-on Cloud Agent running on Oracle VM, responsible for 24/7 email triage, social drafts, and Git synchronization.

**Attributes**:
- `agent_id` (string, PK): Identifier "cloud" (hardcoded)
- `vault_path` (string): Absolute path to vault on Cloud VM (e.g., `/opt/personal-ai-employee/vault`)
- `git_remote_url` (string): Git SSH URL (e.g., `git@github.com:user/ai-employee-vault.git`)
- `whatsapp_notification_number` (string): Phone number for WhatsApp alerts (e.g., `+1234567890`)
- `anthropic_api_key` (string): Claude API key (encrypted in .env.cloud)
- `last_sync_timestamp` (datetime): Last successful Git push timestamp
- `uptime_hours` (int): Hours since Cloud Agent started (for health monitoring)

**File Representation**: Not stored in vault (runtime state only), logged to `vault/Logs/Cloud/agent_state.md`

**Validation Rules**:
- `agent_id` MUST be "cloud" (enforced by code)
- `vault_path` MUST exist and be writable
- `git_remote_url` MUST be valid SSH URL with authenticated key
- `whatsapp_notification_number` MUST be E.164 format (`+[country][number]`)
- `anthropic_api_key` MUST start with `sk-ant-`

**State Transitions**: N/A (always active on Cloud VM)

---

### 2. LocalAgent (New in Platinum)

**Description**: Represents the on-demand Local Agent running on user's laptop, responsible for approvals, MCP execution, and final send/post actions.

**Attributes**:
- `agent_id` (string, PK): Identifier "local" (hardcoded)
- `vault_path` (string): Absolute path to vault on Local machine (e.g., `/home/user/personal-ai-employee/vault`)
- `mcp_servers` (array<string>): List of configured MCP servers (e.g., `["email-mcp", "whatsapp-mcp", "linkedin-mcp"]`)
- `session_files_path` (string): Path to sensitive files (e.g., `~/.whatsapp_session.json`)
- `last_online_timestamp` (datetime): Last time Local Agent was active (for "offline" detection by Cloud)

**File Representation**: Not stored in vault, logged to `vault/Logs/Local/agent_state.md`

**Validation Rules**:
- `agent_id` MUST be "local" (enforced by code)
- `vault_path` MUST exist and be writable
- `mcp_servers` MUST be non-empty array (at least email-mcp, whatsapp-mcp, linkedin-mcp)
- `session_files_path` MUST be in .gitignore (security partition)

**State Transitions**: online ↔ offline (detected by Git sync activity)

---

### 3. GitSyncState (New in Platinum)

**Description**: Tracks current synchronization state between Cloud Agent, Local Agent, and Git remote repository.

**Attributes**:
- `sync_id` (string, PK): Unique ID for sync state (e.g., `gitsync_2026-02-15`)
- `last_pull_timestamp` (datetime): Last successful `git pull` by Local Agent
- `last_push_timestamp` (datetime): Last successful `git push` by Cloud Agent
- `commit_hash_cloud` (string): Latest commit hash pushed by Cloud (40-char SHA)
- `commit_hash_local` (string): Latest commit hash pulled by Local (40-char SHA)
- `pending_conflicts` (array<string>): List of files with unresolved merge conflicts (e.g., `["Dashboard.md"]`)
- `sync_status` (enum): Current sync state: `"synced"`, `"diverged"`, `"conflict"`, `"offline"`

**File Representation**: `vault/.git_sync_state.md` (YAML frontmatter)

**Validation Rules**:
- `commit_hash_cloud` and `commit_hash_local` MUST be 40-char hexadecimal SHA-1 hashes
- `sync_status` transitions:
  - `synced`: `commit_hash_cloud == commit_hash_local`
  - `diverged`: `commit_hash_cloud != commit_hash_local`, no conflicts
  - `conflict`: `pending_conflicts` non-empty
  - `offline`: Git remote unreachable for >5 minutes

**State Transitions**:
```
synced → diverged (Cloud pushes new commits)
diverged → synced (Local pulls successfully)
diverged → conflict (Local pull encounters merge conflict)
conflict → synced (Local auto-resolves or human resolves conflict)
* → offline (Git push/pull fails 3x)
offline → synced (Git remote accessible again, sync completes)
```

**Conflict Resolution Rules** (Dashboard.md example):
1. Cloud owns `/## Updates/` section (timestamped status messages)
2. Local owns main content (task table, statistics)
3. On conflict: Accept Cloud's `/## Updates/`, keep Local's main content, log to `vault/Logs/Local/git_conflicts.md`

---

### 4. DashboardApproval (New in Platinum)

**Description**: Represents a single pending approval displayed in Next.js dashboard UI.

**Attributes**:
- `approval_id` (string, PK): Unique ID (e.g., `EMAIL_DRAFT_12345`, `LINKEDIN_POST_2026-02-15`)
- `category` (enum): Approval type: `"Email"`, `"LinkedIn"`, `"WhatsApp"`, `"Odoo"`, `"Social"` (Facebook/Instagram/Twitter)
- `title` (string): Human-readable title (e.g., `"Reply to John Doe"`, `"LinkedIn Post: Product Launch"`)
- `preview_text` (string): First 100 characters of draft body (for dashboard card)
- `timestamp` (datetime): When draft was created
- `status` (enum): Current state: `"pending"`, `"approved"`, `"rejected"`, `"sent"`, `"failed"`
- `file_path` (string): Absolute path to draft file in vault (e.g., `vault/Pending_Approval/Email/EMAIL_DRAFT_12345.md`)

**File Representation**: Derived from vault files in `vault/Pending_Approval/{category}/`, not stored separately

**Validation Rules**:
- `title` max 60 characters (truncate for UI display)
- `preview_text` max 100 characters (truncate from draft body)
- `category` MUST match folder structure (`/Pending_Approval/Email/` → category="Email")
- `file_path` MUST exist when status="pending"

**State Transitions**:
```
pending → approved (user clicks "Approve" button)
pending → rejected (user clicks "Reject" button)
approved → sent (MCP action completes successfully)
approved → failed (MCP action fails after 3 retries)
rejected → (terminal state, moved to /Done/)
sent → (terminal state, moved to /Done/)
failed → pending (retry queued to /Needs_Action/)
```

**Dashboard API Mapping**:
- `GET /api/status`: Returns array of DashboardApproval objects (read from vault/Pending_Approval/)
- `POST /api/approve`: Moves file from `/Pending_Approval/` to `/Approved/`, updates status to "approved"
- `POST /api/reject`: Moves file from `/Pending_Approval/` to `/Rejected/`, updates status to "rejected"

---

### 5. WhatsAppNotification (New in Platinum)

**Description**: Represents a cross-platform alert sent by Cloud Agent to user's WhatsApp.

**Attributes**:
- `notification_id` (string, PK): Unique ID (e.g., `NOTIFY_2026-02-15_143025`)
- `event_type` (enum): Trigger event: `"urgent_email"`, `"critical_error"`, `"approval_summary"`, `"confirmation"`
- `recipient_number` (string): WhatsApp phone number (E.164 format, e.g., `+1234567890`)
- `message_text` (string): Full notification message (max 500 characters)
- `sent_timestamp` (datetime): When notification was sent
- `delivery_status` (enum): Current state: `"sent"`, `"failed"`, `"fallback_email"`

**File Representation**: `vault/Logs/Cloud/notifications.md` (append-only log)

**Validation Rules**:
- `message_text` max 500 characters (WhatsApp Web message limit)
- `recipient_number` MUST match `WHATSAPP_NOTIFICATION_NUMBER` from .env.cloud
- `event_type` determines message template (see Message Templates section)

**State Transitions**:
```
(created) → sent (Playwright send succeeds)
(created) → failed (Playwright send fails 3x)
failed → fallback_email (send email to FALLBACK_EMAIL instead)
```

**Message Templates**:

1. **urgent_email**:
   ```
   ⚠️ [URGENT] Email from {sender_name}
   Subject: {subject}
   AI drafted reply ready
   Approve: {dashboard_url}/approvals/email/{draft_id}
   Or check vault/Pending_Approval/Email/
   ```

2. **critical_error**:
   ```
   🚨 [ERROR] {error_type}
   {brief_description}
   Check logs: vault/Logs/Cloud/errors.md
   Action: {recommended_action}
   ```

3. **approval_summary**:
   ```
   📋 Good morning! {count} items pending approval:
   - {email_count} Email drafts
   - {linkedin_count} LinkedIn posts
   - {whatsapp_count} WhatsApp replies
   Review: {dashboard_url}/approvals
   ```

4. **confirmation**:
   ```
   ✅ {action_type} completed
   {action_summary}
   Logged: vault/Logs/MCP_Actions/{timestamp}.md
   ```

---

### 6. MCPServerHealth (New in Platinum)

**Description**: Real-time health status of each configured MCP server.

**Attributes**:
- `mcp_name` (string, PK): MCP server identifier (e.g., `"email"`, `"whatsapp"`, `"linkedin"`, `"odoo"`)
- `status` (enum): Current health: `"online"`, `"offline"`, `"degraded"`
- `last_successful_call_timestamp` (datetime): Last time MCP returned success
- `last_call_status` (enum): Result of last call: `"success"`, `"error"`, `"timeout"`
- `error_message` (string, nullable): Error details if last call failed (max 200 chars)

**File Representation**: `vault/Logs/MCP_Health/{mcp_name}.md` (updated on each health check)

**Validation Rules**:
- `mcp_name` MUST match configured MCP in `~/.config/claude-code/mcp.json`
- `status` transitions:
  - `online`: Last 3 calls succeeded
  - `degraded`: 1-2 of last 3 calls failed
  - `offline`: All last 3 calls failed OR no successful call in last 60 minutes
- `error_message` truncated to 200 chars for UI display

**State Transitions**:
```
online → degraded (1-2 failures in last 3 calls)
degraded → offline (3 consecutive failures)
offline → degraded (1 success after offline period)
degraded → online (3 consecutive successes)
```

**Health Check Implementation**:
```python
def check_mcp_health(mcp_name: str) -> MCPServerHealth:
    try:
        result = invoke_mcp_health_endpoint(mcp_name, timeout=5)
        return MCPServerHealth(
            mcp_name=mcp_name,
            status="online" if result.ok else "degraded",
            last_successful_call_timestamp=now(),
            last_call_status="success",
            error_message=None
        )
    except TimeoutError:
        return MCPServerHealth(status="offline", last_call_status="timeout")
```

---

### 7. APIUsageLog (New in Platinum)

**Description**: Record of a single Claude API call for cost tracking and CEO Briefing.

**Attributes**:
- `log_id` (string, PK): Unique ID (e.g., `API_2026-02-15_143025_12345`)
- `timestamp` (datetime): When API call was made
- `agent_id` (enum): Agent that made call: `"cloud"`, `"local"`
- `model` (string): Claude model used (e.g., `"claude-sonnet-4.5"`)
- `prompt_tokens` (int): Input token count
- `completion_tokens` (int): Output token count
- `cost_usd` (float): Calculated cost in USD (formula: `(prompt_tokens * 3 + completion_tokens * 15) / 1_000_000`)
- `task_type` (enum): What task triggered API call: `"email_draft"`, `"linkedin_draft"`, `"ceo_briefing"`, `"whatsapp_draft"`, `"social_draft"`, `"priority_analysis"`

**File Representation**: `vault/Logs/API_Usage/YYYY-MM-DD.md` (one file per day, append-only)

**File Format Example**:
```yaml
---
date: 2026-02-15
total_calls: 47
total_cost_usd: 1.23
---

| Timestamp | Agent | Model | Prompt Tokens | Completion Tokens | Cost USD | Task Type |
|-----------|-------|-------|---------------|-------------------|----------|-----------|
| 14:30:25 | cloud | claude-sonnet-4.5 | 1200 | 350 | 0.009 | email_draft |
| 14:32:10 | cloud | claude-sonnet-4.5 | 800 | 200 | 0.006 | linkedin_draft |
```

**Validation Rules**:
- `prompt_tokens` and `completion_tokens` MUST be > 0
- `cost_usd` MUST match formula: `(prompt_tokens * 3 + completion_tokens * 15) / 1_000_000`
- `model` MUST be valid Claude model name (claude-sonnet-4.5, claude-opus-4, claude-haiku-3.5)
- `agent_id` MUST be "cloud" or "local"

**Aggregation Queries** (for Dashboard API Usage page):
- **Daily cost**: Sum `cost_usd` WHERE `date = today`
- **Weekly cost**: Sum `cost_usd` WHERE `date >= monday_of_this_week`
- **Monthly cost**: Sum `cost_usd` WHERE `date >= first_day_of_month`
- **Cost by agent**: `GROUP BY agent_id`

---

### 8. OdooInstance (New in Platinum)

**Description**: Represents the cloud-deployed Odoo Community server on Oracle VM.

**Attributes**:
- `odoo_url` (string): HTTPS URL to Odoo instance (e.g., `https://odoo.yourdomain.com:8069`)
- `database_name` (string): Odoo PostgreSQL database name (e.g., `platinum_business`)
- `version` (string): Odoo version (e.g., `"19.0"`)
- `ssl_cert_expiry` (datetime): Let's Encrypt SSL certificate expiration date
- `last_backup_timestamp` (datetime): Last successful database backup
- `health_status` (enum): Current state: `"online"`, `"offline"`, `"degraded"`

**File Representation**: `vault/Logs/Cloud/odoo_health.md` (updated daily)

**Validation Rules**:
- `odoo_url` MUST use HTTPS (enforce SSL)
- `ssl_cert_expiry` MUST be > 7 days in future (alert if <7 days)
- `last_backup_timestamp` MUST be < 25 hours ago (daily backup verification)
- `health_status`:
  - `online`: HTTP 200 from `/web/health` endpoint
  - `degraded`: HTTP 5xx errors OR slow response (>5s)
  - `offline`: Connection timeout OR no response in 10s

**State Transitions**:
```
online → degraded (5xx errors OR slow response)
online → offline (connection timeout)
degraded → online (successful health check)
offline → online (connection restored)
```

**Backup Verification** (daily cron):
```bash
#!/bin/bash
# /etc/cron.daily/odoo-backup-verify
LATEST_BACKUP=$(ls -t /opt/odoo_backups/odoo_db_*.sql.gz | head -1)
if [ -z "$LATEST_BACKUP" ] || [ $(find "$LATEST_BACKUP" -mtime +1) ]; then
    echo "Backup missing or old" | vault/Logs/Cloud/odoo_health.md
fi
```

---

### 9. PM2Process (New in Platinum)

**Description**: Represents a single managed background process (watcher, orchestrator, dashboard).

**Attributes**:
- `process_name` (string, PK): PM2 process identifier (e.g., `"cloud_orchestrator"`, `"nextjs_dashboard"`)
- `agent_type` (enum): Where process runs: `"cloud"`, `"local"`
- `status` (enum): Current PM2 status: `"online"`, `"stopped"`, `"errored"`, `"launching"`
- `uptime_seconds` (int): Seconds since process started
- `restart_count` (int): Number of times PM2 restarted process
- `cpu_percent` (float): Current CPU usage (0-100%)
- `memory_mb` (int): Current memory usage in MB
- `log_file_path` (string): Absolute path to PM2 log file (e.g., `~/.pm2/logs/cloud_orchestrator-out.log`)

**File Representation**: Runtime state from `pm2 jlist` command (not stored in vault)

**Validation Rules**:
- `process_name` MUST match name in ecosystem.config.js
- `status` transitions:
  - `launching` → `online` (process starts successfully)
  - `online` → `errored` (process crashes)
  - `errored` → `launching` (PM2 auto-restart)
  - `online` → `stopped` (manual `pm2 stop`)
- `restart_count` > 5 in 1 minute → crash loop alert

**State Transitions**:
```
stopped → launching (pm2 start)
launching → online (process ready)
online → errored (uncaught exception)
errored → launching (PM2 auto-restart after restart_delay)
online → stopped (pm2 stop)
```

**Health Monitoring** (Cloud Agent health_monitor.py):
```python
def check_pm2_health():
    processes = subprocess.check_output(['pm2', 'jlist']).decode()
    for proc in json.loads(processes):
        if proc['pm2_env']['restart_time'] > 5 and proc['pm2_env']['uptime'] < 60000:
            # Crash loop detected (>5 restarts, uptime <1min)
            send_whatsapp_notification(f"🚨 {proc['name']} crash loop detected")
```

---

## Entity Relationships

```
CloudAgent 1:N WhatsAppNotification (sends)
CloudAgent 1:1 GitSyncState (manages push)
LocalAgent 1:1 GitSyncState (manages pull)
LocalAgent 1:N DashboardApproval (processes)
LocalAgent 1:N MCPServerHealth (monitors)

DashboardApproval N:1 EmailDraft (extends)
DashboardApproval N:1 LinkedInDraft (extends)
DashboardApproval N:1 WhatsAppDraft (extends)
DashboardApproval N:1 OdooDraft (extends)

MCPServerHealth 1:N APIUsageLog (tracked per MCP call)

PM2Process N:1 CloudAgent (runs on)
PM2Process N:1 LocalAgent (runs on)

OdooInstance 1:1 CloudAgent (deployed on same VM)
```

---

## Inherited Entities (from Gold Tier)

The following entities are defined in Gold tier and remain unchanged in Platinum:

- **EmailDraft** (FR-G002–FR-G008)
- **LinkedInDraft** (FR-G009–FR-G015)
- **WhatsAppDraft** (FR-G016–FR-G033)
- **Plan** (FR-G034–FR-G042)
- **PlanStep** (part of Plan entity)
- **ExecutionState** (Ralph Wiggum loop state)
- **MCPActionLog** (FR-G043–FR-G046, FR-G075–FR-G077)
- **CEOBriefing** (FR-G047–FR-G051)
- **OdooDraft** (FR-G052–FR-G055)
- **FacebookDraft** (FR-G056–FR-G070)
- **InstagramDraft** (FR-G056–FR-G070)
- **TwitterDraft** (FR-G056–FR-G070)

All Gold entities continue to function identically in Platinum tier (backward compatibility guarantee).

---

## Validation Summary

### Security Partition Validation (Constitution VI)

**Cloud Agent MUST NOT have**:
- WhatsApp session files (`*.session`, `WHATSAPP_SESSION_PATH`)
- SMTP credentials (`SMTP_PASSWORD`)
- Banking credentials (`BANK_API_TOKEN`)
- Payment tokens (`PAYMENT_API_KEY`)
- Odoo password (`ODOO_PASSWORD`)

**Cloud Agent MAY have**:
- `ANTHROPIC_API_KEY` (read-only Claude API)
- `GIT_REMOTE_URL` + SSH key (read-only Git pull/push)
- `WHATSAPP_NOTIFICATION_NUMBER` (send-only via MCP)

**Enforcement**: Startup validation script checks `.env.cloud` for prohibited vars, refuses to start if found.

### Git Sync Validation

**.gitignore MUST exclude**:
- `.env`, `.env.*`
- `*.session`, `*.pem`, `*.key`
- `credentials.json`, `vault/.secrets/`
- `node_modules/`, `__pycache__/`, `.next/`
- `odoo_backups/`, `*.log`, `*.sqlite`

**Enforcement**: Pre-commit Git hook blocks commits containing these patterns.

---

**Data model complete. Ready for Phase 1 API contracts and quickstart guide.**
