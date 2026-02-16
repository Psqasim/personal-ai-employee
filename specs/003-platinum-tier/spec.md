# Feature Specification: Platinum Tier - Always-On Cloud + Local Executive

**Feature Branch**: `003-platinum-tier`
**Created**: 2026-02-15
**Status**: Draft
**Input**: User description: "BISMILLAH! Starting Platinum Tier with Next.js UI + Notifications - 24/7 Cloud deployment (Oracle Cloud), Work-Zone Specialization (Cloud vs Local), Next.js Dashboard, Cross-platform Notifications, Agent Skills Integration"

## Overview

Platinum Tier transforms the Gold foundation into a production-grade, always-on AI Employee with **dual-agent architecture (Cloud + Local), Next.js web dashboard, cross-platform notifications, and 24/7 autonomous operation**. The Cloud Agent handles email triage, social media drafting, and business analysis while the Local Agent manages approvals, WhatsApp sessions, payments, and final execution of sensitive actions. Both agents communicate via Git-synced vault with claim-by-move rules to prevent double-work.

**Core Principle**: Cloud drafts, Local approves and executes. The Cloud Agent is your 24/7 proactive assistant; the Local Agent is your secure execution gatekeeper.

**Key Additions** (building on Gold):
- **Dual-agent architecture**: Cloud Agent (Oracle Cloud Free VM, 24/7) + Local Agent (user's laptop, on-demand)
- **Next.js Dashboard UI**: Web-based approval interface with real-time status, one-click approve/reject buttons, mobile-responsive, dark mode
- **Cross-platform notifications**: Cloud → WhatsApp alerts for urgent emails, pending approvals, system errors
- **Vault sync via Git**: Automatic push/pull between Cloud and Local with merge conflict resolution
- **Claim-by-move rules**: First agent to move task from `/Needs_Action/` to `/In_Progress/{agent}/` owns it
- **Work-Zone Specialization**: Cloud owns email triage, social drafts, analysis; Local owns approvals, WhatsApp, payments, final send/post
- **Odoo Community 24/7**: Cloud-hosted Odoo with HTTPS, backups, health monitoring
- **Security partition**: WhatsApp sessions, banking creds, API keys never sync to cloud
- **Watchdog auto-restart**: PM2 process management for watcher scripts, orchestrator, and Next.js server
- **API usage tracking**: Claude API cost tracking with weekly reports in CEO Briefing

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cloud Agent Email Triage & Draft Generation (24/7) (Priority: P1)

As a **professional receiving emails 24/7**, I want the Cloud Agent to continuously monitor my inbox, draft replies for high-priority emails even when my laptop is offline, and alert me via WhatsApp when urgent action is needed so I never miss critical client communication regardless of time or location.

**Why this priority**: 24/7 email triage is the defining capability of Platinum tier. It demonstrates autonomous operation without human presence, directly solving the "missed urgent email while sleeping" problem. This is the primary justification for cloud deployment costs.

**Independent Test**: (1) Send test email to monitored inbox at 3:00 AM while Local Agent is offline. (2) Within 2 minutes, verify Cloud Agent creates `EMAIL_{id}.md` in `vault/Inbox/`, generates draft reply in `vault/Pending_Approval/Email/`, commits changes to Git. (3) When Local Agent comes online (8:00 AM), Git pull succeeds, user sees draft in Obsidian. (4) User moves draft to `vault/Approved/Email/`, Local Agent sends via Email MCP.

**Acceptance Scenarios**:

1. **Given** Cloud Agent is running on Oracle Cloud VM with Gmail watcher active 24/7, **When** a high-priority email arrives at any time, **Then** Cloud Agent creates task file in `vault/Inbox/` within 2 minutes, generates AI draft reply within 15 seconds, saves to `vault/Pending_Approval/Email/`, commits to Git, and pushes to remote within 30 seconds

2. **Given** Local Agent is offline (laptop closed), **When** Cloud Agent generates email draft, **Then** Cloud Agent does NOT send the email (defers to Local), updates `vault/Dashboard.md` with "Pending Local Approval: Email draft for [sender]", commits Dashboard update to Git

3. **Given** Cloud Agent detects urgent email (keywords: "urgent", "asap", "emergency", "deadline today"), **When** draft is generated, **Then** Cloud Agent sends WhatsApp notification to user: "⚠️ [URGENT] Email from {sender} | AI drafted reply | Approve: {dashboard_url} | Or check vault/" within 60 seconds

4. **Given** Local Agent comes online after being offline, **When** Git pull completes, **Then** Local Agent detects new files in `vault/Pending_Approval/Email/`, updates local Dashboard.md with count of pending approvals, and displays notification in Next.js UI

5. **Given** both Cloud and Local Agents process tasks simultaneously, **When** both agents detect the same file in `vault/Needs_Action/`, **Then** only the first agent to move file to `/In_Progress/{agent_id}/` proceeds; the second agent skips (claim-by-move rule enforced)

6. **Given** Cloud Agent vault write fails (Git conflict, disk full), **When** the failure occurs, **Then** Cloud Agent retries 3 times (exponential backoff), logs error to `vault/Logs/Cloud/errors.md`, sends WhatsApp alert to user, and queues task for retry on next cycle

---

### User Story 2 - Next.js Dashboard with One-Click Approvals (Priority: P1)

As a **busy professional managing approvals on mobile**, I want a responsive web dashboard showing all pending approvals (email, LinkedIn, WhatsApp, Odoo) with preview and one-click approve/reject buttons so I can handle approvals in 10 seconds on my phone during commute without opening Obsidian.

**Why this priority**: The Next.js dashboard is the user-facing innovation of Platinum tier and the portfolio centerpiece. It transforms file-based approval into a modern web interface, making the system accessible to non-technical users. Without this, Platinum is just "Gold on a cloud VM."

**Independent Test**: (1) Start Next.js server on Local Agent. (2) Open `http://localhost:3000` in mobile browser. (3) Verify dashboard displays pending approval cards for email/LinkedIn/WhatsApp with preview text. (4) Click "Approve" on email draft card. (5) Within 2 seconds, verify file moved to `vault/Approved/Email/`, Email MCP sends, dashboard updates to show "Sent ✓".

**Acceptance Scenarios**:

1. **Given** Next.js server is running on Local Agent, **When** user navigates to `http://localhost:3000`, **Then** dashboard loads within 2 seconds showing: Pending Approvals count by category (Email, LinkedIn, WhatsApp, Odoo, Social), Real-time Task Status (active plans, completed today), MCP Server Health (email ✓/✗, whatsapp ✓/✗, linkedin ✓/✗), API Usage Stats (Claude API calls today, cost this week), Recent Activity Log (last 10 actions)

2. **Given** pending approval files exist in `vault/Pending_Approval/{Email,LinkedIn,WhatsApp}/`, **When** dashboard loads, **Then** each approval displays as a card with: Type (Email/LinkedIn/WhatsApp), Subject/Title, Preview (first 100 chars), Timestamp, "Approve" button (green), "Reject" button (red), "Preview Full" button (opens modal)

3. **Given** user clicks "Approve" on email draft card, **When** the click event fires, **Then** dashboard API moves file from `vault/Pending_Approval/Email/` to `vault/Approved/Email/` within 500ms, shows loading spinner, and updates to "Approved - Sending…" status

4. **Given** file is moved to `vault/Approved/Email/`, **When** Email MCP completes send, **Then** dashboard receives real-time update (WebSocket or 5s polling), card transitions to "Sent ✓" with timestamp, and card auto-removes from Pending section after 3 seconds

5. **Given** user clicks "Reject" on LinkedIn draft card, **When** the click event fires, **Then** dashboard moves file from `vault/Pending_Approval/LinkedIn/` to `vault/Rejected/`, logs rejection reason (optional text input), updates dashboard to show "Rejected" status, and removes card

6. **Given** user clicks "Preview Full" on WhatsApp draft card, **When** the modal opens, **Then** modal displays: original WhatsApp message (full text), AI draft reply (full text), metadata (from, timestamp, keywords matched), and modal includes "Approve" and "Reject" buttons for direct action

7. **Given** dashboard is accessed on mobile (screen width <768px), **When** page renders, **Then** layout is responsive: cards stack vertically, buttons are touch-friendly (min 44px height), fonts scale appropriately, no horizontal scroll

8. **Given** user enables Dark Mode toggle, **When** toggle is clicked, **Then** dashboard theme switches to dark (background: #1e1e1e, text: #e0e0e0, cards: #2d2d2d) within 200ms, preference is saved to localStorage, and persists across page reloads

9. **Given** authentication is enabled (NEXT_AUTH_ENABLED=true), **When** user navigates to dashboard without session, **Then** dashboard redirects to `/login`, displays simple auth form (username/password), validates against `DASHBOARD_PASSWORD` in .env, and creates session on success

10. **Given** Next.js server is unreachable (offline), **When** user attempts to load dashboard, **Then** browser displays cached offline page with message "Dashboard offline - use Obsidian for manual approvals" and local file paths

---

### User Story 3 - Cross-Platform Notifications (Cloud → WhatsApp) (Priority: P1)

As a **user relying on Cloud Agent while mobile**, I want instant WhatsApp alerts when the Cloud Agent detects urgent emails, critical errors, or time-sensitive approvals so I can respond immediately without constantly checking the dashboard.

**Why this priority**: WhatsApp notifications bridge the gap between 24/7 Cloud operation and human availability. Without proactive alerts, the Cloud Agent's work goes unnoticed until the user manually checks. This is P1 because it enables true "fire and forget" operation.

**Independent Test**: (1) Configure Cloud Agent with WHATSAPP_NOTIFICATION_NUMBER in .env. (2) Trigger urgent email arrival on Cloud Agent. (3) Within 60 seconds, verify WhatsApp notification received on user's phone with format: "⚠️ [URGENT] Email from {sender} | AI drafted reply | Approve: {url} | Or check vault/". (4) Click dashboard URL in notification, verify it opens Next.js approval page.

**Acceptance Scenarios**:

1. **Given** Cloud Agent detects urgent email (priority="High", keywords match), **When** email draft is generated, **Then** Cloud Agent sends WhatsApp notification within 60 seconds with message format: "⚠️ [URGENT] Email from {sender_name}\nSubject: {subject}\nAI drafted reply ready\nApprove: {dashboard_url}/approvals/email/{draft_id}\nOr check vault/Pending_Approval/Email/"

2. **Given** Cloud Agent encounters critical error (vault write failure, API quota exceeded, MCP server down), **When** error is logged, **Then** Cloud Agent sends WhatsApp alert within 60 seconds with message format: "🚨 [ERROR] {error_type}\n{brief_description}\nCheck logs: vault/Logs/Cloud/errors.md\nAction: {recommended_action}"

3. **Given** Local Agent comes online after Cloud Agent generated 5+ pending approvals, **When** Local Agent Git pull completes, **Then** Local Agent sends WhatsApp summary: "📋 Good morning! 5 items pending approval:\n- 3 Email drafts\n- 1 LinkedIn post\n- 1 WhatsApp reply\nReview: {dashboard_url}/approvals"

4. **Given** user approves draft via Next.js dashboard, **When** MCP action completes successfully, **Then** confirmation WhatsApp message sent within 30 seconds: "✅ Email sent to {recipient}\n{action_summary}\nLogged: vault/Logs/MCP_Actions/{timestamp}.md"

5. **Given** WhatsApp MCP (Playwright) fails to send notification, **When** the send attempt times out, **Then** Cloud Agent retries 2 times (5s, 10s backoff), logs failure to `vault/Logs/Cloud/notification_failures.md`, and falls back to email notification to user's configured FALLBACK_EMAIL

6. **Given** user disables WhatsApp notifications (ENABLE_WHATSAPP_NOTIFICATIONS=false), **When** Cloud Agent processes urgent tasks, **Then** no WhatsApp messages are sent, but events are still logged to `vault/Notifications/sent.md` for audit

---

### User Story 4 - Vault Sync via Git with Claim-by-Move (Priority: P1)

As a **deployer of dual-agent architecture**, I want Cloud and Local Agents to automatically sync vault state via Git push/pull every 60 seconds with claim-by-move rules to prevent both agents from processing the same task so workflows remain consistent and race conditions are eliminated.

**Why this priority**: Git sync is the communication backbone of Platinum tier. Without it, Cloud and Local agents operate in isolation with no state synchronization. This is P1 because dual-agent operation depends entirely on reliable sync.

**Independent Test**: (1) Cloud Agent creates `vault/Inbox/EMAIL_test.md`. (2) Cloud Agent commits and pushes to Git remote. (3) Within 60 seconds, Local Agent Git pull completes and sees new file. (4) Local Agent moves file to `/In_Progress/local/`. (5) Cloud Agent's next cycle detects file is claimed by `local`, skips processing.

**Acceptance Scenarios**:

1. **Given** Cloud Agent generates new file in `vault/Pending_Approval/Email/`, **When** file is written, **Then** Cloud Agent stages file (`git add`), commits with message "Cloud: Email draft {id} generated", pushes to remote origin within 30 seconds, and logs Git operation to `vault/Logs/Cloud/git_sync.md`

2. **Given** Local Agent is online, **When** Git sync cycle runs (every 60 seconds), **Then** Local Agent pulls from remote (`git pull --rebase`), resolves merge conflicts if any (auto-accept non-conflicting changes, log conflicts to `vault/Logs/Local/git_conflicts.md`), and updates local vault

3. **Given** both Cloud and Local Agents detect the same file in `vault/Needs_Action/`, **When** both agents attempt to claim, **Then** the agent that successfully moves file to `/In_Progress/{agent_id}/` first (atomic file move) proceeds; the second agent's move fails, logs "Task already claimed by {other_agent}", skips task

4. **Given** Git push from Cloud Agent fails (network error, remote unreachable), **When** push times out, **Then** Cloud Agent retries 3 times (exponential backoff: 10s, 30s, 90s), queues failed push to `vault/.git_queue/` for next cycle, and continues processing other tasks (non-blocking failure)

5. **Given** Local Agent pulls changes with merge conflict (both agents modified Dashboard.md), **When** conflict is detected, **Then** Local Agent auto-resolves: accepts Cloud's changes for `/Updates/` section, keeps Local's changes for main content, commits merge, logs conflict details to `vault/Logs/Local/git_conflicts.md`

6. **Given** Git remote is unavailable for >5 minutes, **When** Cloud Agent detects prolonged failure, **Then** Cloud Agent sends WhatsApp alert to user: "🚨 Git sync failing for 5+ min\nCloud/Local agents out of sync\nAction: Check network/remote Git server", logs to errors.md

---

### User Story 5 - Work-Zone Specialization (Cloud vs Local Security Boundaries) (Priority: P1)

As a **security-conscious user**, I want Cloud Agent to NEVER access WhatsApp sessions, banking credentials, or final send/post actions, while Local Agent handles all sensitive operations so my credentials remain on my local machine and cloud compromise doesn't leak payment data.

**Why this priority**: Security partition is the Platinum tier's key architectural constraint per hackathon requirements. It enables 24/7 cloud operation without sacrificing security. This is P1 because violating this boundary breaks the trust model.

**Independent Test**: (1) Audit Cloud Agent .env file, verify WHATSAPP_SESSION_PATH, BANK_API_TOKEN, SMTP_PASSWORD are absent. (2) Verify Cloud Agent code cannot execute Email/WhatsApp/Social MCP send actions (only draft creation). (3) Trigger email draft approval, verify only Local Agent invokes Email MCP send.

**Acceptance Scenarios**:

1. **Given** Cloud Agent .env configuration, **When** agent starts, **Then** the following variables MUST NOT exist in Cloud .env: WHATSAPP_SESSION_PATH, BANK_API_TOKEN, BANK_API_SECRET, SMTP_PASSWORD, PAYMENT_API_KEY, ODOO_PASSWORD (any MCP send credentials). Cloud .env includes only: ANTHROPIC_API_KEY, VAULT_PATH, GIT_REMOTE_URL, WHATSAPP_NOTIFICATION_NUMBER

2. **Given** Cloud Agent processes email task, **When** high-priority email is detected, **Then** Cloud Agent creates draft in `vault/Pending_Approval/Email/`, commits to Git, and stops. Cloud Agent does NOT invoke Email MCP send action (send function not in Cloud codebase)

3. **Given** Local Agent processes approved email draft, **When** file appears in `vault/Approved/Email/`, **Then** Local Agent invokes Email MCP send with SMTP credentials from Local .env, sends email, logs action, and moves file to `vault/Done/`

4. **Given** WhatsApp MCP is configured on Local Agent, **When** WhatsApp watcher runs, **Then** watcher accesses `WHATSAPP_SESSION_PATH` on Local filesystem only. Cloud Agent never polls WhatsApp Web and has no Playwright session

5. **Given** Odoo draft is created by Cloud Agent, **When** draft is saved to `vault/Pending_Approval/Odoo/`, **Then** Cloud Agent commits draft without posting to Odoo. Local Agent invokes Odoo MCP with ODOO_PASSWORD from Local .env to create draft entry in Odoo

6. **Given** user reviews security partition, **When** checking codebase, **Then** Cloud Agent code (in `cloud_agent/`) has no imports for: smtplib, playwright, payment APIs. Only Local Agent code (in `local_agent/`) includes these modules

7. **Given** Cloud Agent vault sync, **When** Git push occurs, **Then** Cloud Agent MUST NOT commit files matching `.env`, `*.session`, `credentials.json`, or any file in `vault/.secrets/` (gitignore enforced)

---

### User Story 6 - Odoo Community 24/7 Cloud Deployment (Priority: P2)

As a **business owner needing accounting automation**, I want Odoo Community hosted on the same Oracle Cloud VM as Cloud Agent with HTTPS, automated backups, and health monitoring so I can access accounting from anywhere and Cloud Agent can create draft invoices/expenses 24/7.

**Why this priority**: 24/7 Odoo is a Platinum hackathon requirement. It demonstrates full business system integration. This is P2 because it's infrastructure setup, and the core Platinum features (dual-agent, dashboard, notifications) deliver value without Odoo.

**Independent Test**: (1) SSH to Oracle Cloud VM. (2) Verify Odoo service running (`systemctl status odoo`). (3) Access Odoo via HTTPS (`https://{vm_public_ip}:8069`). (4) Cloud Agent creates invoice draft task, verify Odoo draft entry created via JSON-RPC API without posting.

**Acceptance Scenarios**:

1. **Given** Odoo Community 19+ is installed on Oracle Cloud VM, **When** Odoo service starts, **Then** Odoo is accessible at `https://{vm_public_ip}:8069` with valid Let's Encrypt SSL certificate, database `platinum_business` configured, admin user created

2. **Given** Cloud Agent detects accounting task (type="invoice" or type="expense") in `vault/Inbox/`, **When** task is processed, **Then** Cloud Agent generates Odoo draft entry data (partner_id, amount, description) via AI analysis, saves to `vault/Pending_Approval/Odoo/ODOO_DRAFT_{id}.md`, commits to Git

3. **Given** Local Agent approves Odoo draft (file in `vault/Approved/Odoo/`), **When** Odoo MCP is invoked, **Then** Local Agent calls Odoo JSON-RPC API (`object.execute_kw`) to create draft invoice/expense (state="draft", not posted), receives Odoo record_id, logs to MCP actions

4. **Given** Odoo service on cloud VM, **When** daily backup cron runs (3:00 AM UTC), **Then** backup script dumps Odoo database to `/opt/odoo_backups/odoo_db_{YYYY-MM-DD}.sql.gz`, retains last 30 days of backups, logs backup success to `/var/log/odoo_backup.log`

5. **Given** Odoo health monitor (systemd watchdog), **When** Odoo service becomes unresponsive, **Then** systemd restarts Odoo service within 60 seconds, logs restart event, sends WhatsApp alert to user: "🚨 Odoo restarted on cloud VM\nCheck logs: /var/log/odoo/odoo.log"

6. **Given** Odoo API is unreachable (VM offline, network issue), **When** Local Agent attempts Odoo MCP call, **Then** system retries 3 times (exponential backoff), creates `vault/Needs_Action/odoo_unreachable_{id}.md`, logs error, and continues processing other tasks

---

### User Story 7 - Watchdog Auto-Restart with PM2 (Priority: P2)

As a **Platinum tier deployer**, I want all critical processes (watchers, orchestrator, Next.js server) managed by PM2 with auto-restart on crash, startup on boot, and health monitoring so the system recovers automatically from failures without manual SSH intervention.

**Why this priority**: PM2 watchdog is the reliability backbone of 24/7 operation. Without it, any watcher crash requires manual restart, breaking the "always-on" promise. This is P2 because the system can function manually for short periods, but P2 is still critical for production.

**Independent Test**: (1) Start all processes via PM2 (`pm2 start ecosystem.config.js`). (2) Verify `pm2 list` shows all processes running. (3) Kill gmail_watcher process (`pm2 delete gmail_watcher`). (4) Within 10 seconds, verify PM2 auto-restarts gmail_watcher. (5) Reboot VM, verify all processes auto-start after boot.

**Acceptance Scenarios**:

1. **Given** PM2 is installed on Oracle Cloud VM and Local machine, **When** `pm2 start ecosystem.config.js` is executed, **Then** PM2 launches processes: `cloud_orchestrator` (Cloud only), `local_orchestrator` (Local only), `gmail_watcher` (Cloud), `whatsapp_watcher` (Local), `nextjs_dashboard` (Local), `git_sync` (both)

2. **Given** `cloud_orchestrator` process crashes (uncaught exception), **When** PM2 detects process exit, **Then** PM2 restarts `cloud_orchestrator` within 5 seconds, logs restart event to `~/.pm2/logs/cloud_orchestrator-error.log`, increments restart counter

3. **Given** PM2 startup hook is configured (`pm2 startup`), **When** Oracle Cloud VM reboots, **Then** all PM2-managed processes auto-start within 60 seconds of boot, and Cloud Agent resumes Git sync and email monitoring without manual intervention

4. **Given** `nextjs_dashboard` process on Local machine, **When** Next.js server crashes, **Then** PM2 restarts server within 5 seconds, dashboard becomes accessible again, and users see brief "Reconnecting…" message in UI

5. **Given** PM2 health monitoring is enabled, **When** any process exceeds 80% CPU for >5 minutes or 90% memory, **Then** PM2 logs resource warning to `~/.pm2/logs/pm2.log` and optionally sends webhook alert (if configured in ecosystem.config.js)

6. **Given** `pm2 list` command is executed, **When** output is displayed, **Then** all processes show status (online/stopped), uptime, restarts count, CPU%, memory%, and log file paths

---

### User Story 8 - Next.js Dashboard API Usage & MCP Health Monitoring (Priority: P2)

As a **cost-conscious user**, I want the Next.js dashboard to display real-time Claude API usage (calls today, cost this week) and MCP server health status (online/offline, last successful call) so I can monitor expenses and detect service outages before they cause failures.

**Why this priority**: Cost tracking and health monitoring transform the dashboard from "approval UI" into a full operations console. This is P2 because it's monitoring/observability rather than core functionality.

**Independent Test**: (1) Open Next.js dashboard. (2) Verify "API Usage" section shows "Claude API: 47 calls today, $1.23 this week". (3) Verify "MCP Health" section shows "Email MCP: ✓ Online (last call: 2 min ago), WhatsApp MCP: ✗ Offline (last call: 12 hours ago)".

**Acceptance Scenarios**:

1. **Given** dashboard loads, **When** API Usage section renders, **Then** display shows: "Claude API: {count} calls today, ${cost} this week" calculated from `vault/Logs/API_Usage/YYYY-MM-DD.md` entries (each entry: timestamp, model, tokens_in, tokens_out, cost)

2. **Given** Cloud or Local Agent invokes Claude API, **When** API call completes, **Then** agent logs to `vault/Logs/API_Usage/{date}.md` with YAML frontmatter: timestamp, agent_id (cloud|local), model (claude-sonnet-4.5), prompt_tokens, completion_tokens, cost_usd (calculated at $3/MTok input, $15/MTok output)

3. **Given** dashboard "MCP Health" section, **When** section renders, **Then** display shows status for each configured MCP: Email MCP (✓/✗, last_call_timestamp, last_status), LinkedIn MCP (✓/✗, last_call_timestamp), WhatsApp MCP (✓/✗, last_call_timestamp), Odoo MCP (✓/✗, last_call_timestamp)

4. **Given** MCP server is offline (email-mcp not responding), **When** dashboard polls MCP health, **Then** Email MCP status shows "✗ Offline" with red indicator, last successful call timestamp, and tooltip: "Last successful call: 12 hours ago - Check MCP server logs"

5. **Given** weekly CEO Briefing is generated, **When** Briefing includes "API Cost This Week" section, **Then** Briefing displays: total Claude API calls, total cost, average cost per call, breakdown by agent (Cloud: $X, Local: $Y), and trend vs previous week (+/-%)

6. **Given** user enables cost alerts (COST_ALERT_THRESHOLD=50 in .env), **When** weekly API cost exceeds $50, **Then** dashboard displays warning banner: "⚠️ API cost this week: ${cost} (exceeds threshold: $50)" and sends WhatsApp alert

---

### Edge Cases

- **What happens when Cloud and Local Agents both modify Dashboard.md simultaneously?** → Git merge conflict occurs; Local Agent auto-resolves by accepting Cloud's `/Updates/` section and keeping Local's main content; conflict logged to `vault/Logs/Local/git_conflicts.md`

- **What happens when Git remote is down for 24 hours?** → Cloud and Local agents operate independently; Cloud continues drafting, Local continues approving; when Git remote recovers, agents pull and push backlog; potential merge conflicts are logged and queued for human review in `vault/Needs_Action/git_sync_manual.md`

- **What happens when user approves draft via Obsidian file move while simultaneously approving same draft via Next.js dashboard?** → Both actions move file to `vault/Approved/`; first move succeeds, second attempt fails (file not found); MCP action executes once based on first successful move; duplicate action attempt is logged as "skipped - already approved"

- **What happens when WhatsApp notification fails 3 times?** → Cloud Agent logs notification failure to `vault/Logs/Cloud/notification_failures.md`, falls back to email notification to FALLBACK_EMAIL, and continues operation without blocking other tasks

- **What happens when Oracle Cloud VM runs out of disk space?** → Cloud Agent's file write fails; agent detects disk full error, logs critical alert, sends WhatsApp notification "🚨 Cloud VM disk full - urgent action required", pauses non-critical operations (keeps email monitoring but stops CEO Briefing generation)

- **What happens when Next.js dashboard authentication password is forgotten?** → User accesses Local Agent machine, reads `DASHBOARD_PASSWORD` from `.env`, or disables auth temporarily by setting `NEXT_AUTH_ENABLED=false`, restarts Next.js server

- **What happens when Odoo SSL certificate expires?** → Odoo HTTPS becomes inaccessible; Cloud Agent's Odoo draft creation continues (drafts saved to vault); Local Agent's Odoo MCP calls fail (SSL verification error); system creates `vault/Needs_Action/odoo_ssl_expired.md` with renewal instructions

- **What happens when user changes Git remote URL?** → User updates `GIT_REMOTE_URL` in Cloud and Local .env files; next Git sync cycle fails (authentication error); agents log error, pause sync, create `vault/Needs_Action/git_remote_update_required.md` instructing user to run `git remote set-url origin {new_url}` manually

- **What happens when Local Agent is offline for 7 days?** → Cloud Agent continues drafting, committing to Git remote; when Local Agent comes back online, Git pull retrieves 7 days of drafts; Local Agent processes backlog (up to 100 pending approvals displayed in dashboard); older drafts (>7 days) are auto-archived to `vault/Archive/old_drafts/`

- **What happens when PM2 process restart loop (crashing every 2 seconds)?** → PM2 detects restart storm (>5 restarts in 1 minute), stops process permanently, logs to `~/.pm2/logs/{process}-error.log`; user receives WhatsApp alert "🚨 {process} crash loop detected - manual intervention required"; system continues other processes

---

## Requirements *(mandatory)*

### Functional Requirements

#### Dual-Agent Architecture (Platinum Core)

- **FR-P001**: System MUST provide two independent agent codebases: `cloud_agent/` (deployed on Oracle Cloud VM) and `local_agent/` (runs on user's laptop). Both agents share vault structure but have separate .env configurations

- **FR-P002**: Cloud Agent MUST run 24/7 on Oracle Cloud Free Tier VM (VM.Standard.A1.Flex, 4 OCPU, 24GB RAM recommended) with Ubuntu 22.04 LTS, systemd services, and PM2 process management

- **FR-P003**: Cloud Agent MUST NOT have access to: WHATSAPP_SESSION_PATH, SMTP_PASSWORD, BANK_API_TOKEN, payment API keys, or any MCP send credentials. Cloud .env limited to: ANTHROPIC_API_KEY, VAULT_PATH, GIT_REMOTE_URL, WHATSAPP_NOTIFICATION_NUMBER

- **FR-P004**: Local Agent MUST have full MCP access: Email MCP (send), WhatsApp MCP (send), LinkedIn MCP (post), Social MCP (Facebook/Instagram/Twitter post), Odoo MCP (draft create)

- **FR-P005**: Cloud Agent MUST execute: email triage (detect high-priority inbox items), email draft generation, LinkedIn post draft generation, social media draft generation (Facebook/Instagram/Twitter), business analysis, CEO Briefing generation

- **FR-P006**: Local Agent MUST execute: approval processing (move files from Pending to Approved), MCP send actions (email, WhatsApp, social posts), WhatsApp session management, payment processing, Odoo draft submission

#### Vault Sync via Git (Platinum Core)

- **FR-P007**: System MUST configure Git remote repository (GitHub, GitLab, or self-hosted) for vault sync with SSH key authentication (no password prompts in automated sync)

- **FR-P008**: Cloud Agent MUST run Git sync cycle every 60 seconds: `git add .`, `git commit -m "Cloud: {summary}"`, `git push origin main` (configurable branch via GIT_BRANCH in .env)

- **FR-P009**: Local Agent MUST run Git sync cycle every 60 seconds: `git pull --rebase origin main`, auto-resolve non-conflicting changes, log conflicts to `vault/Logs/Local/git_conflicts.md`

- **FR-P010**: Git sync MUST enforce .gitignore rules: exclude `.env`, `*.session`, `credentials.json`, `vault/.secrets/`, `node_modules/`, `__pycache__/`, `.next/` (Next.js build artifacts)

- **FR-P011**: On Git merge conflict (both agents modified same file), Local Agent MUST auto-resolve: for Dashboard.md, accept Cloud's `/Updates/` section, keep Local's main content; for other files, accept most recent timestamp; log all conflicts with diff to `vault/Logs/Local/git_conflicts.md`

- **FR-P012**: If Git push/pull fails (network error, remote unreachable), agent MUST retry 3 times (exponential backoff: 10s, 30s, 90s), queue failed operation to `vault/.git_queue/pending_ops.md`, and continue processing tasks (non-blocking)

#### Claim-by-Move Rules (Platinum Core)

- **FR-P013**: System MUST implement claim-by-move: when agent detects file in `vault/Needs_Action/`, agent attempts atomic move to `vault/In_Progress/{agent_id}/` (agent_id = "cloud" or "local")

- **FR-P014**: If file move succeeds, agent owns task and proceeds with processing. If move fails (file not found = already claimed), agent logs "Task {id} claimed by {other_agent}" and skips

- **FR-P015**: Completed tasks MUST be moved from `/In_Progress/{agent_id}/` to `vault/Done/` with YAML frontmatter updated: `processed_by: {agent_id}`, `completed_at: {timestamp}`

- **FR-P016**: Stale in-progress files (in `/In_Progress/` for >24 hours without status update) MUST be detected by both agents' cleanup cycle (daily at 00:00), moved back to `vault/Needs_Action/` with YAML frontmatter: `retry_count: {count}`, `last_failure: {reason}`

#### Next.js Dashboard UI (Platinum Core)

- **FR-P017**: System MUST provide Next.js 14+ web application in `nextjs_dashboard/` directory with TypeScript, Tailwind CSS, React Server Components, and API routes

- **FR-P018**: Dashboard MUST run on Local Agent only (NEXT_PUBLIC_AGENT_TYPE=local in .env), accessible at `http://localhost:3000` or configured PORT

- **FR-P019**: Dashboard home page (`/`) MUST display: Pending Approvals (count by category: Email, LinkedIn, WhatsApp, Odoo, Social with clickable cards), Real-time Task Status (active plans, completed today, failed today), MCP Server Health (status grid: email ✓/✗, whatsapp ✓/✗, linkedin ✓/✗, odoo ✓/✗), API Usage Stats (Claude API calls today, cost this week, cost this month), Recent Activity Log (last 10 actions with timestamps, types, statuses)

- **FR-P020**: Pending Approvals section (`/approvals`) MUST display cards for each pending approval with: Type badge (Email/LinkedIn/WhatsApp/Odoo/Social), Title/Subject (truncated to 60 chars), Preview (first 100 chars of body), Timestamp (relative: "2 hours ago"), Buttons: "Approve" (green, primary), "Reject" (red, secondary), "Preview Full" (opens modal)

- **FR-P021**: Approve button click MUST trigger API route `/api/approve` with POST request body: `{type: "email"|"linkedin"|"whatsapp"|"odoo"|"social", draft_id, category: "Email"|"LinkedIn"|etc}`, which moves file from `vault/Pending_Approval/{category}/` to `vault/Approved/{category}/`, returns success JSON

- **FR-P022**: Reject button click MUST trigger API route `/api/reject` with POST request body: `{type, draft_id, category, reason: "optional text"}`, which moves file from `vault/Pending_Approval/{category}/` to `vault/Rejected/`, appends rejection reason to file YAML frontmatter, returns success JSON

- **FR-P023**: Preview Full modal MUST display: original content (email body, WhatsApp message, LinkedIn context), AI draft reply/post (full text, formatted with line breaks), metadata (from, to, timestamp, keywords_matched for WhatsApp, business_goal_reference for LinkedIn), action buttons (Approve, Reject, Close modal)

- **FR-P024**: Dashboard MUST be mobile-responsive (Tailwind breakpoints: sm: 640px, md: 768px, lg: 1024px): cards stack vertically on <768px, buttons min 44px touch target, fonts scale (text-sm on mobile, text-base on desktop), no horizontal scroll

- **FR-P025**: Dashboard MUST support Dark Mode toggle (button in header): Dark theme colors: bg-[#1e1e1e], text-[#e0e0e0], cards bg-[#2d2d2d], borders border-gray-700. Light theme: bg-white, text-gray-900, cards bg-gray-50. Preference stored in localStorage, persists across reloads

- **FR-P026**: Dashboard authentication (if NEXT_AUTH_ENABLED=true in .env) MUST use NextAuth.js with credentials provider: login page (`/login`), password validation against DASHBOARD_PASSWORD from .env, session cookie (7-day expiry), redirect unauthenticated users to `/login`, logout button in header

- **FR-P027**: Dashboard MCP Health section (`/health`) MUST display grid of MCP servers: For each MCP (email, whatsapp, linkedin, facebook, instagram, twitter, odoo): Status (✓ Online / ✗ Offline / ⚠️ Degraded), Last successful call (timestamp), Last call status (success/error/timeout), Test button (triggers health check API route)

- **FR-P028**: Dashboard API Usage section (`/api-usage`) MUST display: Total Claude API calls today (count), Cost today ($X.XX), Cost this week ($X.XX), Cost this month ($X.XX), Average cost per call, Chart (daily cost bar chart for last 7 days), data read from `vault/Logs/API_Usage/*.md`

- **FR-P029**: Dashboard MUST poll vault state every 5 seconds (API route `/api/status`) for real-time updates: pending approval counts, active plan status, recent activity log entries. Frontend updates UI without full page reload (React state update)

- **FR-P030**: Dashboard MUST provide offline fallback: if Next.js server unreachable (ECONNREFUSED), browser displays cached offline page with message "Dashboard offline - use Obsidian at file://{VAULT_PATH}" and links to vault folders

#### Cross-Platform Notifications (Platinum Core)

- **FR-P031**: Cloud Agent MUST send WhatsApp notifications via WhatsApp MCP (Playwright automation) for events: urgent email detected (priority="High"), critical error (vault write failure, API quota exceeded, MCP crash), pending approvals count >5 when Local Agent online

- **FR-P032**: WhatsApp notification message format for urgent email MUST be: "⚠️ [URGENT] Email from {sender_name}\nSubject: {subject}\nAI drafted reply ready\nApprove: {dashboard_url}/approvals/email/{draft_id}\nOr check vault/Pending_Approval/Email/{filename}" (max 500 chars)

- **FR-P033**: WhatsApp notification message format for critical error MUST be: "🚨 [ERROR] {error_type}\n{brief_description} (max 100 chars)\nCheck logs: vault/Logs/Cloud/errors.md\nAction: {recommended_action}" (max 400 chars)

- **FR-P034**: WhatsApp notification message format for Local Agent summary MUST be: "📋 Good morning! {count} items pending approval:\n- {email_count} Email drafts\n- {linkedin_count} LinkedIn posts\n- {whatsapp_count} WhatsApp replies\n- {odoo_count} Odoo drafts\nReview: {dashboard_url}/approvals"

- **FR-P035**: Confirmation WhatsApp notification (after user approval + MCP send) MUST be: "✅ {action_type} completed\n{action_summary} (e.g., 'Email sent to client@example.com')\nLogged: vault/Logs/MCP_Actions/{timestamp}.md" (max 300 chars)

- **FR-P036**: If WhatsApp MCP send fails (timeout, element not found, session expired), Cloud Agent MUST retry 2 times (5s, 10s backoff), log failure to `vault/Logs/Cloud/notification_failures.md`, and fall back to email notification to FALLBACK_EMAIL

- **FR-P037**: If ENABLE_WHATSAPP_NOTIFICATIONS=false in .env, Cloud Agent MUST NOT send WhatsApp messages but still log notification events to `vault/Notifications/sent.md` with YAML frontmatter (timestamp, event_type, recipient, message_preview, status="disabled")

#### Odoo Community 24/7 Deployment (Platinum Extension)

- **FR-P038**: Odoo Community 19+ MUST be deployed on Oracle Cloud VM with: installation path `/opt/odoo`, systemd service `odoo.service`, PostgreSQL 15+ database `platinum_business`, admin user configured

- **FR-P039**: Odoo MUST be accessible via HTTPS at `https://{vm_public_ip}:8069` with Let's Encrypt SSL certificate (auto-renewal via certbot)

- **FR-P040**: Odoo daily backup script MUST run via cron at 03:00 UTC: dump database to `/opt/odoo_backups/odoo_db_{YYYY-MM-DD}.sql.gz`, retain last 30 backups, delete backups >30 days old, log to `/var/log/odoo_backup.log`

- **FR-P041**: Odoo systemd service MUST include watchdog configuration: `Restart=always`, `RestartSec=5`, `StartLimitInterval=0` (unlimited restarts), auto-restart on crash within 60 seconds

- **FR-P042**: Cloud Agent Odoo draft generation MUST: detect accounting tasks (type="invoice"|"expense") in `vault/Inbox/`, extract data (partner_name, amount, description, date) via AI analysis, save to `vault/Pending_Approval/Odoo/ODOO_DRAFT_{id}.md`, commit to Git

- **FR-P043**: Local Agent Odoo MCP MUST: read approved draft from `vault/Approved/Odoo/`, invoke Odoo JSON-RPC API (`object.execute_kw`) to create draft invoice/expense (state="draft", not posted/confirmed), receive Odoo record_id, log to `vault/Logs/MCP_Actions/odoo_{timestamp}.md`

#### Watchdog & Process Management (Platinum Reliability)

- **FR-P044**: System MUST provide PM2 ecosystem configuration file (`ecosystem.config.js`) for Cloud and Local agents with processes: `cloud_orchestrator` (Cloud only), `local_orchestrator` (Local only), `gmail_watcher` (Cloud only), `whatsapp_watcher` (Local only), `nextjs_dashboard` (Local only), `git_sync` (both)

- **FR-P045**: PM2 processes MUST auto-restart on crash: `max_restarts: 10`, `min_uptime: 5000` (5s min uptime before restart), `autorestart: true`, `restart_delay: 1000` (1s delay between restarts)

- **FR-P046**: PM2 startup hook MUST be configured: `pm2 startup systemd` (Linux), processes auto-start on VM boot, `pm2 save` freezes process list

- **FR-P047**: PM2 logs MUST be stored: stdout to `~/.pm2/logs/{process}-out.log`, stderr to `~/.pm2/logs/{process}-error.log`, log rotation enabled (max 10 files, 10MB each)

- **FR-P048**: If process exceeds resource limits (CPU >80% for >5 min, memory >90%), PM2 MUST log warning to `~/.pm2/logs/pm2.log` and optionally send webhook alert (if PM2_WEBHOOK_URL configured)

#### API Usage Tracking (Platinum Observability)

- **FR-P049**: Cloud and Local Agents MUST log every Claude API call to `vault/Logs/API_Usage/YYYY-MM-DD.md` with YAML frontmatter: timestamp, agent_id ("cloud"|"local"), model (e.g., "claude-sonnet-4.5"), prompt_tokens, completion_tokens, cost_usd (calculated)

- **FR-P050**: Cost calculation MUST use Claude API pricing: Input: $3/MTok, Output: $15/MTok. Formula: `cost_usd = (prompt_tokens * 3 + completion_tokens * 15) / 1_000_000`

- **FR-P051**: Dashboard API Usage section MUST aggregate costs: daily total (sum of today's entries), weekly total (last 7 days), monthly total (current calendar month), average per call

- **FR-P052**: Weekly CEO Briefing MUST include "API Cost This Week" section: total calls, total cost, breakdown by agent (Cloud: $X, Local: $Y), trend vs previous week (+/-%), cost per completed task

- **FR-P053**: If weekly cost exceeds COST_ALERT_THRESHOLD (default: $50), dashboard MUST display warning banner and send WhatsApp alert: "⚠️ API cost this week: ${cost} (exceeds threshold)"

#### Security & .gitignore (Platinum Mandate)

- **FR-P054**: Git repository MUST enforce .gitignore rules excluding: `.env`, `*.session`, `credentials.json`, `vault/.secrets/`, `node_modules/`, `__pycache__/`, `.next/`, `*.log`, `*.sqlite`, `odoo_backups/`

- **FR-P055**: Cloud Agent vault sync MUST verify before commit: no files matching .gitignore patterns are staged; if violation detected, abort commit and log to `vault/Logs/Cloud/security_violations.md`

- **FR-P056**: WhatsApp session files (`WHATSAPP_SESSION_PATH`) MUST exist only on Local Agent filesystem, never synced to Git, verified by Local Agent startup check

- **FR-P057**: MCP credentials in .env MUST be validated on agent startup: Cloud .env must NOT contain SMTP_PASSWORD, BANK_API_TOKEN, etc.; if violation detected, agent refuses to start and logs error

#### Backward Compatibility (Platinum Guarantee)

- **FR-P058**: All Gold tier functional requirements (FR-G001 through FR-G077) MUST remain functional in Platinum tier when Cloud Agent is disabled (ENABLE_CLOUD_AGENT=false)

- **FR-P059**: All Silver tier functional requirements (FR-S001 through FR-S044) MUST remain functional in Platinum tier

- **FR-P060**: All Bronze tier functional requirements (FR-B001 through FR-B025) MUST remain functional in Platinum tier

- **FR-P061**: When ENABLE_CLOUD_AGENT=false, system MUST operate identically to Gold tier (Local Agent only, no Git sync, no Cloud notifications)

### Non-Functional Requirements

#### Performance (NFR-P-PERF)

- **NFR-P-PERF-001**: Git sync cycle (pull or push) MUST complete within 10 seconds under normal conditions (vault size <500MB, stable network)
- **NFR-P-PERF-002**: Next.js dashboard initial page load MUST complete within 2 seconds (measured via Lighthouse Performance score >90)
- **NFR-P-PERF-003**: Dashboard API polling (`/api/status`) MUST respond within 500ms (vault read + JSON response)
- **NFR-P-PERF-004**: WhatsApp notification MUST be sent within 60 seconds of triggering event (Cloud Agent event → notification delivered)
- **NFR-P-PERF-005**: Dashboard approve/reject button click → file move → UI update MUST complete within 2 seconds (perceived responsiveness)
- **NFR-P-PERF-006**: PM2 process restart (on crash) MUST complete within 5 seconds (process down to process online)

#### Reliability (NFR-P-REL)

- **NFR-P-REL-001**: Cloud Agent uptime MUST be ≥99% (measured monthly). Downtime includes: VM reboot, process crash without auto-restart, unrecoverable errors
- **NFR-P-REL-002**: Git sync MUST handle network outages gracefully: retry failed operations, queue for next cycle, never block agent processing
- **NFR-P-REL-003**: Claim-by-move race condition MUST be prevented: atomic file moves, first-mover wins, zero duplicate task processing verified by audit log
- **NFR-P-REL-004**: PM2 process crash loop (>5 restarts in 1 minute) MUST trigger permanent stop and human alert (WhatsApp notification)
- **NFR-P-REL-005**: Next.js dashboard MUST survive Local Agent offline periods: cached offline page displayed, no data loss, reconnect automatically when agent returns

#### Security (NFR-P-SEC)

- **NFR-P-SEC-001**: Cloud Agent MUST NEVER access: WhatsApp session files, SMTP passwords, banking API tokens, payment credentials, or any credential in `vault/.secrets/`
- **NFR-P-SEC-002**: Git commits MUST NEVER include: .env files, session files, credentials, or any file matching .gitignore rules. Verified by pre-commit hook
- **NFR-P-SEC-003**: Next.js dashboard authentication (when enabled) MUST use bcrypt-hashed passwords, secure session cookies (httpOnly, sameSite=strict), 7-day session expiry
- **NFR-P-SEC-004**: Odoo HTTPS MUST use valid SSL certificate (Let's Encrypt), enforce TLS 1.2+, disable insecure ciphers
- **NFR-P-SEC-005**: WhatsApp notification content MUST NOT include: email addresses, phone numbers, account numbers, full message bodies (max 100 chars preview)

#### Usability (NFR-P-USE)

- **NFR-P-USE-001**: Upgrade path Gold→Platinum MUST be documented: Oracle Cloud VM setup, Git remote config, Cloud Agent deployment, Next.js dashboard installation. Zero data migration required
- **NFR-P-USE-002**: Next.js dashboard MUST be accessible to non-technical users: no CLI commands required for approvals, intuitive button labels, error messages in plain English
- **NFR-P-USE-003**: Dashboard mobile experience MUST be touch-friendly: buttons min 44px, no hover-dependent UI, large tap targets, no accidental approvals (confirm dialog for bulk actions)
- **NFR-P-USE-004**: Error messages in `vault/Needs_Action/` MUST include: clear problem description, recommended resolution steps, links to relevant docs, example commands to run

---

### Key Entities

- **CloudAgent**: Autonomous agent running on Oracle Cloud VM 24/7
  - Attributes: agent_id="cloud", vault_path, git_remote_url, whatsapp_notification_number, api_key, last_sync_timestamp, uptime_hours

- **LocalAgent**: User's laptop-based agent handling approvals and sensitive operations
  - Attributes: agent_id="local", vault_path, mcp_servers (array), session_files_path, last_online_timestamp

- **GitSyncState**: Current state of vault Git synchronization
  - Attributes: last_pull_timestamp, last_push_timestamp, commit_hash_cloud, commit_hash_local, pending_conflicts (array), sync_status ("synced"|"diverged"|"conflict"|"offline")

- **DashboardApproval**: Pending approval displayed in Next.js UI
  - Attributes: approval_id, category ("Email"|"LinkedIn"|"WhatsApp"|"Odoo"|"Social"), title, preview_text, timestamp, status ("pending"|"approved"|"rejected"), file_path

- **WhatsAppNotification**: Cross-platform alert sent by Cloud Agent
  - Attributes: notification_id, event_type ("urgent_email"|"critical_error"|"approval_summary"|"confirmation"), recipient_number, message_text, sent_timestamp, delivery_status ("sent"|"failed"|"fallback_email")

- **MCPServerHealth**: Real-time health status of MCP server
  - Attributes: mcp_name ("email"|"whatsapp"|"linkedin"|"odoo"|etc), status ("online"|"offline"|"degraded"), last_successful_call_timestamp, last_call_status ("success"|"error"|"timeout"), error_message

- **APIUsageLog**: Single Claude API call record
  - Attributes: log_id, timestamp, agent_id ("cloud"|"local"), model, prompt_tokens, completion_tokens, cost_usd, task_type ("email_draft"|"linkedin_draft"|"ceo_briefing"|etc)

- **OdooInstance**: Cloud-deployed Odoo Community server
  - Attributes: odoo_url, database_name, version, ssl_cert_expiry, last_backup_timestamp, health_status ("online"|"offline"|"degraded")

- **PM2Process**: Managed background process
  - Attributes: process_name, agent_type ("cloud"|"local"), status ("online"|"stopped"|"errored"), uptime_seconds, restart_count, cpu_percent, memory_mb, log_file_path

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-P001**: Cloud Agent operates 24/7 with ≥99% uptime (measured monthly). Downtime <7.2 hours per month. Verified by PM2 uptime logs and Cloud Agent heartbeat commits to Git

- **SC-P002**: Email drafts generated by Cloud Agent while Local Agent offline are available for approval within 60 seconds of Local Agent coming online (Git pull + vault refresh)

- **SC-P003**: Next.js dashboard loads on mobile (iPhone Safari, Android Chrome) within 2 seconds, all approve/reject buttons are touch-friendly (≥44px), no horizontal scroll, dark mode persists across sessions

- **SC-P004**: User approves email draft via Next.js dashboard: click "Approve" → file moved → Email MCP sends → dashboard shows "Sent ✓" within 5 seconds total (end-to-end latency)

- **SC-P005**: WhatsApp notifications for urgent emails delivered within 60 seconds of Cloud Agent detection. Notification includes clickable dashboard URL that loads approval page directly

- **SC-P006**: Git sync prevents race conditions: 100 concurrent tasks processed by Cloud and Local agents simultaneously, zero duplicate task executions verified by audit log cross-check (each task processed exactly once)

- **SC-P007**: Vault merge conflicts (both agents modify Dashboard.md) are auto-resolved by Local Agent in 100% of cases during testing. Manual conflict intervention required 0 times over 30-day test period

- **SC-P008**: Odoo accessible via HTTPS on Oracle Cloud VM. SSL certificate valid. Daily backups created at 03:00 UTC, last 30 backups retained. Odoo service auto-restarts within 60 seconds of crash

- **SC-P009**: PM2 manages all critical processes (6 processes across Cloud and Local). Process crash triggers auto-restart within 5 seconds. PM2 startup hook ensures processes resume after VM reboot

- **SC-P010**: Dashboard API Usage section displays accurate Claude API costs: ±$0.05 variance from manual calculation over 1-week period. Cost alerts trigger when weekly cost exceeds threshold

- **SC-P011**: Security partition verified: Cloud Agent .env contains zero sensitive credentials (SMTP_PASSWORD, WHATSAPP_SESSION_PATH, BANK_API_TOKEN absent). Cloud Agent code cannot execute MCP send actions (only draft creation)

- **SC-P012**: All Gold tier success criteria (SC-G001 through SC-G013) remain met in Platinum tier when Cloud Agent is enabled

- **SC-P013**: Backward compatibility verified: Disable Cloud Agent (ENABLE_CLOUD_AGENT=false), system operates identically to Gold tier, all Gold success criteria pass

### Definition of Done

Platinum Tier is **Done** when:

1. ✅ All 8 user stories have passing acceptance tests
2. ✅ All 61 functional requirements (FR-P001 through FR-P061) are implemented
3. ✅ All non-functional requirements (NFR-P-*) are verified
4. ✅ All 13 success criteria (SC-P001 through SC-P013) are met
5. ✅ All Gold + Silver + Bronze tests still pass (backward compatibility confirmed)
6. ✅ Oracle Cloud VM provisioned with Cloud Agent deployed, PM2 configured, systemd startup enabled
7. ✅ Next.js dashboard accessible at `http://localhost:3000`, mobile-responsive verified (Chrome DevTools + real device), dark mode functional
8. ✅ Integration test passes: Cloud Agent detects urgent email → drafts reply → commits to Git → WhatsApp notification sent → Local Agent pulls → user approves via dashboard → Email MCP sends → confirmation notification
9. ✅ Git sync test passes: 100 concurrent task creations on Cloud and Local → claim-by-move prevents duplicates → all tasks processed exactly once
10. ✅ Security audit passes: Cloud Agent .env scanned, zero sensitive credentials found, .gitignore rules enforced, no credentials in Git history
11. ✅ Odoo deployment verified: accessible via HTTPS, SSL valid, daily backup created, systemd watchdog restarts on crash
12. ✅ PM2 process management verified: all 6 processes managed, auto-restart on crash (<5s downtime), startup on boot
13. ✅ API usage tracking verified: 100 Claude API calls logged, costs calculated accurately (±$0.05), dashboard displays correct totals
14. ✅ WhatsApp notification test passes: trigger urgent email → Cloud Agent sends WhatsApp alert → notification delivered within 60 seconds → dashboard URL clickable
15. ✅ 30-day stability test: Cloud Agent runs continuously for 30 days, uptime ≥99%, zero unrecoverable errors, zero manual restarts

---

## Dependencies

### Inherits From Gold Tier

- All Gold dependencies (anthropic, watchdog, gmail API, playwright, aiohttp, pytest, smtplib, requests, schedule)
- All Gold agent_skills modules (ai_analyzer, vault_parser, dashboard_updater, etc.)
- All Gold scripts (gmail_watcher, linkedin_generator, whatsapp_watcher, ceo_briefing)

### New Python Packages (Platinum additions to pyproject.toml)

```toml
# Platinum additions
"gitpython>=3.1.40",                    # Git sync automation
"pm2>=0.1.0",                           # PM2 Python wrapper (or subprocess calls)
"bcrypt>=4.1.0",                        # Password hashing for dashboard auth
```

### New Node.js Packages (Next.js dashboard)

```json
// nextjs_dashboard/package.json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "next-auth": "^4.24.0",
    "recharts": "^2.12.0",
    "date-fns": "^3.6.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/node": "^20.12.0",
    "@types/react": "^18.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### Infrastructure Requirements

- **Oracle Cloud Free Tier VM**: VM.Standard.A1.Flex, 4 OCPU, 24GB RAM, 200GB storage, Ubuntu 22.04 LTS
- **Git Remote Repository**: GitHub, GitLab, or self-hosted (Gitea) with SSH access, webhook support optional
- **Domain + SSL (for Odoo)**: Optional custom domain, Let's Encrypt SSL via certbot
- **WhatsApp Business API (optional)**: For production WhatsApp notifications instead of Playwright automation

### Configuration Files (.env additions)

```bash
# Inherits all Gold .env variables

# Platinum tier activation
ENABLE_CLOUD_AGENT=true
TIER=platinum

# Git sync configuration
GIT_REMOTE_URL=git@github.com:user/ai-employee-vault.git
GIT_BRANCH=main
GIT_SYNC_INTERVAL=60                     # Seconds between sync cycles

# Cloud Agent configuration
CLOUD_AGENT_ID=cloud
WHATSAPP_NOTIFICATION_NUMBER=+1234567890
FALLBACK_EMAIL=user@example.com

# Local Agent configuration
LOCAL_AGENT_ID=local
DASHBOARD_URL=http://localhost:3000

# Next.js Dashboard
NEXT_PUBLIC_AGENT_TYPE=local
NEXT_AUTH_ENABLED=true
DASHBOARD_PASSWORD=your-secure-password   # bcrypt-hashed in production
SESSION_SECRET=random-secret-key
PORT=3000

# Odoo Cloud Deployment (Oracle VM)
ODOO_URL=https://{vm_public_ip}:8069
ODOO_SSL_CERT_PATH=/etc/letsencrypt/live/{domain}/fullchain.pem
ODOO_BACKUP_PATH=/opt/odoo_backups

# PM2 Configuration
PM2_WEBHOOK_URL=https://example.com/webhook  # Optional health alerts

# Cost Alerts
COST_ALERT_THRESHOLD=50                   # Weekly USD threshold
```

---

## Out of Scope (Deferred to Future Work)

### Deferred to Diamond Tier (Hypothetical)
- ❌ Multi-cloud deployment (AWS, Azure, GCP support)
- ❌ Agent-to-agent communication via message queue (RabbitMQ, Redis Pub/Sub) instead of file-based
- ❌ Voice interface (Alexa/Google Assistant integration)
- ❌ Autonomous learning (agent self-improvement via reinforcement learning)

### Never in Platinum (Safety Boundaries)
- ❌ Cloud Agent sending emails/WhatsApp/posts directly (security violation)
- ❌ Cloud Agent accessing WhatsApp sessions or banking credentials (security violation)
- ❌ Auto-approving any action without human gate (safety violation)
- ❌ Executing code from vault task files (security violation)
- ❌ Deleting user data without explicit trash/archive (data safety)
- ❌ Committing .env files or credentials to Git (security violation)

---

## Assumptions

- **Assumption 1**: User has Oracle Cloud Free Tier account with VM quota available (4 OCPU ARM instance)
- **Assumption 2**: User has Git remote repository (GitHub/GitLab) with SSH key configured for passwordless push/pull
- **Assumption 3**: User's Local Agent machine has stable internet for Git sync (not air-gapped)
- **Assumption 4**: Oracle Cloud VM has public IP address (for Odoo HTTPS access and WhatsApp notifications)
- **Assumption 5**: User operates in single timezone (no multi-timezone Cloud/Local coordination complexity)
- **Assumption 6**: WhatsApp notifications use personal WhatsApp account with Playwright automation (not WhatsApp Business API)
- **Assumption 7**: Next.js dashboard authentication is optional (NEXT_AUTH_ENABLED defaults to false for local-only access)
- **Assumption 8**: User manually resolves Git merge conflicts if auto-resolution fails (escalation via `vault/Needs_Action/git_sync_manual.md`)
- **Assumption 9**: Odoo Community Edition (free, self-hosted) is used, not Odoo Enterprise (paid)
- **Assumption 10**: Local Agent and Cloud Agent never run on the same machine simultaneously (separate physical/virtual machines)

---

## Architecture Diagrams (Text Descriptions)

### System Architecture (Cloud + Local Split)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLATINUM TIER ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                       CLOUD AGENT (Oracle VM)                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  PM2 Managed Processes                                   │ │
│  │  - cloud_orchestrator (24/7)                             │ │
│  │  - gmail_watcher (24/7 email monitoring)                 │ │
│  │  - git_sync (push every 60s)                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Capabilities                                            │ │
│  │  ✓ Email triage + draft generation                      │ │
│  │  ✓ LinkedIn/Social post draft generation                │ │
│  │  ✓ Business analysis + CEO Briefing                     │ │
│  │  ✓ WhatsApp notifications (alerts only)                 │ │
│  │  ✗ No MCP send actions (email/whatsapp/social)          │ │
│  │  ✗ No sensitive credentials (SMTP, bank, WhatsApp session)│ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Odoo Community (Port 8069, HTTPS)                      │ │
│  │  - 24/7 accounting system                                │ │
│  │  - Daily backups (03:00 UTC)                             │ │
│  │  - Systemd watchdog                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                             ↕ Git Sync (SSH)
                    ┌────────────────────────┐
                    │  Git Remote (GitHub)   │
                    │  - SSH auth            │
                    │  - Branch: main        │
                    └────────────────────────┘
                             ↕ Git Sync (SSH)
┌────────────────────────────────────────────────────────────────┐
│                    LOCAL AGENT (User's Laptop)                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  PM2 Managed Processes                                   │ │
│  │  - local_orchestrator (on-demand)                        │ │
│  │  - whatsapp_watcher (WhatsApp Web monitoring)            │ │
│  │  - nextjs_dashboard (Port 3000)                          │ │
│  │  - git_sync (pull every 60s)                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Capabilities                                            │ │
│  │  ✓ Approval processing (via Obsidian or Dashboard)      │ │
│  │  ✓ MCP send actions (email, WhatsApp, social, Odoo)     │ │
│  │  ✓ WhatsApp session management (Playwright)             │ │
│  │  ✓ Payment processing (browser automation)              │ │
│  │  ✓ Full credential access (SMTP, bank, sessions)        │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Next.js Dashboard (http://localhost:3000)              │ │
│  │  - Pending Approvals (all categories)                   │ │
│  │  - Real-time Task Status                                │ │
│  │  - MCP Server Health                                    │ │
│  │  - API Usage Stats                                      │ │
│  │  - One-click Approve/Reject                             │ │
│  │  - Mobile-responsive, Dark Mode                         │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘

                             ↕ WhatsApp Notifications
┌────────────────────────────────────────────────────────────────┐
│                         USER DEVICE                            │
│  - WhatsApp alerts from Cloud Agent                            │
│  - Dashboard access on mobile browser                          │
│  - Obsidian vault (local filesystem)                           │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow: Urgent Email (Cloud → Local)

```
1. Email arrives at 03:00 AM (Local Agent offline)
   ↓
2. Cloud Agent gmail_watcher detects (within 2 min)
   ↓
3. Cloud Agent creates vault/Inbox/EMAIL_{id}.md
   ↓
4. Cloud Agent AI generates draft reply
   ↓
5. Cloud Agent saves vault/Pending_Approval/Email/EMAIL_DRAFT_{id}.md
   ↓
6. Cloud Agent commits to Git + pushes
   ↓
7. Cloud Agent sends WhatsApp notification: "⚠️ [URGENT] Email from Client..."
   ↓
8. User wakes at 08:00 AM, sees WhatsApp notification
   ↓
9. Local Agent comes online, Git pull retrieves draft
   ↓
10. User opens Next.js dashboard on phone
   ↓
11. User clicks "Approve" on email draft card
   ↓
12. Dashboard API moves file to vault/Approved/Email/
   ↓
13. Local Agent Email MCP sends email via SMTP
   ↓
14. Local Agent logs send to vault/Logs/MCP_Actions/
   ↓
15. Cloud Agent sends WhatsApp confirmation: "✅ Email sent to Client"
```

### Security Model (Secrets Partition)

```
┌─────────────────────────────────────────────────────────────────┐
│                        SECURITY PARTITION                       │
└─────────────────────────────────────────────────────────────────┘

CLOUD AGENT (Oracle VM) - RESTRICTED ACCESS
┌────────────────────────────────────────┐
│ Allowed Credentials:                   │
│ ✓ ANTHROPIC_API_KEY (read-only)       │
│ ✓ GIT_REMOTE_URL + SSH key (read-only)│
│ ✓ WHATSAPP_NOTIFICATION_NUMBER (send)  │
│                                        │
│ Prohibited Credentials:                │
│ ✗ SMTP_PASSWORD                        │
│ ✗ WHATSAPP_SESSION_PATH                │
│ ✗ BANK_API_TOKEN                       │
│ ✗ PAYMENT_API_KEY                      │
│ ✗ ODOO_PASSWORD                        │
│                                        │
│ Capabilities:                          │
│ - Draft generation (email, social)    │
│ - Business analysis                    │
│ - WhatsApp alerts (notification only) │
│ - NO MCP send actions                  │
└────────────────────────────────────────┘

LOCAL AGENT (User's Laptop) - FULL ACCESS
┌────────────────────────────────────────┐
│ All Credentials Available:             │
│ ✓ ANTHROPIC_API_KEY                    │
│ ✓ SMTP_PASSWORD (email send)           │
│ ✓ WHATSAPP_SESSION_PATH (session)      │
│ ✓ BANK_API_TOKEN (payment)             │
│ ✓ ODOO_PASSWORD (draft create)         │
│ ✓ LinkedIn/Facebook/Twitter tokens     │
│                                        │
│ Capabilities:                          │
│ - All MCP send actions                 │
│ - WhatsApp Web session management      │
│ - Payment processing                   │
│ - Final approval authority             │
└────────────────────────────────────────┘

GIT REMOTE (GitHub) - PUBLIC SYNC
┌────────────────────────────────────────┐
│ Synced Files:                          │
│ ✓ vault/**/*.md (all markdown)         │
│ ✓ vault/Logs/ (audit logs)             │
│ ✓ vault/Plans/ (execution plans)       │
│                                        │
│ Never Synced (.gitignore):             │
│ ✗ .env                                 │
│ ✗ *.session (WhatsApp)                 │
│ ✗ credentials.json                     │
│ ✗ vault/.secrets/                      │
│ ✗ node_modules/                        │
└────────────────────────────────────────┘
```

---

**Next Step**: Proceed to `/sp.clarify 003-platinum-tier` to resolve any unclear requirements, or `/sp.plan 003-platinum-tier` to design the implementation architecture.
