# Tasks: Platinum Tier - Always-On Cloud + Local Executive

**Input**: Design documents from `/specs/003-platinum-tier/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks grouped by user story (US1-US8) with clear dependencies and effort estimates
**Tests**: Integration tests included for critical workflows (Git sync, dual-agent coordination, dashboard approval flow)

**Priority Phases** (per user request):
- Phase 1: Cloud VM + Git sync (critical path) → US4, US5
- Phase 2: Next.js dashboard (portfolio value) → US2, US8
- Phase 3: WhatsApp notifications (user experience) → US3
- Phase 4: Production hardening (monitoring, health checks) → US1, US6, US7

**Effort Scale**: S=Small (1-2h), M=Medium (3-5h), L=Large (6-8h), XL=Extra Large (1-2 days)

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US8)
- Include exact file paths in descriptions
- Effort estimate in parentheses after description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dual-agent directory structure
**Effort**: 2-3 hours total

- [ ] T001 Create dual-agent project structure per plan.md (cloud_agent/, local_agent/, agent_skills/, nextjs_dashboard/, deployment/, tests/) (M)
- [ ] T002 [P] Initialize Python dependencies in requirements.txt (gitpython, bcrypt, all Gold dependencies) (S)
- [ ] T003 [P] Initialize Next.js 14 project in nextjs_dashboard/ with TypeScript, Tailwind, dependencies from plan.md (M)
- [ ] T004 [P] Configure ESLint and Prettier for Next.js dashboard (S)
- [ ] T005 [P] Configure pytest and testing infrastructure for integration tests (S)
- [ ] T006 Create .env.cloud.example and .env.local.example templates with security partition comments (M)
- [ ] T007 Create .gitignore with security rules (.env, *.session, credentials.json, vault/.secrets/, node_modules/) (S)
- [ ] T008 Setup Git pre-commit hook in deployment/git-hooks/pre-commit to block .env, *.session commits (M)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation
**Effort**: 6-8 hours total

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create CloudAgent entity in agent_skills/entities.py (agent_id, vault_path, git_remote_url, whatsapp_notification_number) (M)
- [ ] T010 [P] Create LocalAgent entity in agent_skills/entities.py (agent_id, vault_path, mcp_servers, session_files_path) (M)
- [ ] T011 [P] Create GitSyncState entity in agent_skills/entities.py (last_pull_timestamp, commit_hash_cloud, sync_status) (M)
- [ ] T012 Implement git_manager.py in agent_skills/ (GitPython wrapper, commit, push, pull, conflict detection) (L)
- [ ] T013 Implement claim_manager.py in agent_skills/ (claim-by-move file operations, atomic move, ownership check) (M)
- [ ] T014 [P] Implement api_usage_tracker.py in agent_skills/ (log Claude API calls to vault/Logs/API_Usage/YYYY-MM-DD.md, cost calculation) (M)
- [ ] T015 Create vault subdirectories: vault/Logs/Cloud/, vault/Logs/Local/, vault/Logs/API_Usage/, vault/Logs/MCP_Health/ (S)
- [ ] T016 Setup environment variable validation module in agent_skills/env_validator.py (check Cloud .env has no secrets, Local has all MCP credentials) (M)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 4 - Vault Sync via Git with Claim-by-Move (Priority: P1) 🎯 CRITICAL PATH

**Goal**: Enable Cloud and Local Agents to sync vault state via Git push/pull every 60s with claim-by-move to prevent race conditions

**Independent Test**: (1) Cloud creates file in vault/Inbox/, commits, pushes. (2) Within 60s, Local pulls and sees file. (3) Both agents detect same file in /Needs_Action/. (4) Only first agent to move to /In_Progress/{agent}/ proceeds; second skips.

**Effort**: 12-15 hours (critical path)

### Implementation for User Story 4

- [ ] T017 [P] [US4] Implement Cloud git_sync.py in cloud_agent/src/ (60s cycle: git add, commit with "Cloud: {summary}", push with retry logic) (L)
- [ ] T018 [P] [US4] Implement Local git_sync.py in local_agent/src/ (60s cycle: git pull --rebase, auto-resolve Dashboard.md conflicts, log conflicts) (L)
- [ ] T019 [US4] Implement conflict resolution algorithm in agent_skills/git_manager.py (Dashboard.md: accept Cloud /Updates/, keep Local main, log to git_conflicts.md) (L)
- [ ] T020 [US4] Implement retry logic with exponential backoff (3 retries: 10s, 30s, 90s) in agent_skills/git_manager.py for push/pull failures (M)
- [ ] T021 [US4] Implement GitSyncState persistence to vault/.git_sync_state.md (YAML frontmatter: commit hashes, sync_status, pending_conflicts) (M)
- [ ] T022 [US4] Implement claim-by-move rules in agent_skills/claim_manager.py (atomic file move from /Needs_Action/ to /In_Progress/{agent_id}/) (M)
- [ ] T023 [US4] Add Git sync failure alerts: create vault/Needs_Action/git_sync_failed.md when offline >5 min (M)
- [ ] T024 [US4] Create deployment/git-hooks/pre-commit to verify no .gitignore violations before commit (S)

### Integration Tests for User Story 4

- [ ] T025 [P] [US4] Integration test: Cloud push → Local pull workflow in tests/integration/test_dual_agent_sync.py (M)
- [ ] T026 [P] [US4] Integration test: Claim-by-move race condition prevention (100 concurrent tasks) in tests/integration/test_claim_by_move.py (L)
- [ ] T027 [P] [US4] Integration test: Dashboard.md merge conflict auto-resolution in tests/integration/test_git_conflict.py (M)

**Checkpoint**: Git sync operational between Cloud and Local Agents; claim-by-move prevents duplicate processing

---

## Phase 4: User Story 5 - Work-Zone Specialization (Priority: P1) 🎯 SECURITY PARTITION

**Goal**: Enforce security partition: Cloud Agent NEVER accesses WhatsApp sessions, banking credentials, or final send actions; Local Agent handles all sensitive operations

**Independent Test**: (1) Audit Cloud .env, verify WHATSAPP_SESSION_PATH, SMTP_PASSWORD, BANK_API_TOKEN absent. (2) Verify Cloud code cannot execute Email/WhatsApp/Social MCP send actions. (3) Trigger email draft approval, verify only Local Agent invokes Email MCP send.

**Effort**: 6-8 hours

### Implementation for User Story 5

- [ ] T028 [P] [US5] Create Cloud Agent orchestrator.py in cloud_agent/src/ (main loop: email triage, social drafts, Git push, WhatsApp notifications) (L)
- [ ] T029 [P] [US5] Create Local Agent orchestrator.py in local_agent/src/ (main loop: approval processing, MCP execution, Git pull) (L)
- [ ] T030 [US5] Implement Cloud Agent environment validation in cloud_agent/src/startup_validator.py (check .env.cloud has NO SMTP, WhatsApp session, bank tokens; refuse start if found) (M)
- [ ] T031 [US5] Implement email_draft.py in cloud_agent/src/generators/ (AI draft generation only, save to vault/Pending_Approval/Email/, NO send) (M)
- [ ] T032 [P] [US5] Implement linkedin_draft.py in cloud_agent/src/generators/ (AI LinkedIn post draft, NO post) (M)
- [ ] T033 [P] [US5] Implement social_draft.py in cloud_agent/src/generators/ (AI Facebook/Instagram/Twitter drafts, NO post) (M)
- [ ] T034 [US5] Implement approval_handler.py in local_agent/src/ (monitor vault/Approved/ folders, trigger MCP send actions) (M)
- [ ] T035 [P] [US5] Implement email_sender.py in local_agent/src/executors/ (Email MCP invocation with SMTP credentials from Local .env) (M)
- [ ] T036 [P] [US5] Implement social_poster.py in local_agent/src/executors/ (LinkedIn/Facebook/Instagram/Twitter MCP invocations) (M)
- [ ] T037 [US5] Add security audit logging: Cloud Agent logs all file writes to vault/Logs/Cloud/security_audit.md (paths, timestamps) (S)
- [ ] T038 [US5] Update .gitignore enforcement: verify vault/.secrets/, *.session, .env never committed (pre-commit hook validates) (S)

### Integration Test for User Story 5

- [ ] T039 [US5] Integration test: Cloud drafts email → Local approves → Local sends (verify Cloud never calls Email MCP) in tests/integration/test_security_partition.py (M)

**Checkpoint**: Security partition enforced; Cloud drafts only, Local executes only

---

## Phase 5: User Story 1 - Cloud Agent Email Triage & Draft Generation (Priority: P1)

**Goal**: Cloud Agent continuously monitors inbox, drafts replies for high-priority emails 24/7, alerts user via WhatsApp when urgent

**Independent Test**: (1) Send test email at 3AM while Local offline. (2) Within 2 min, Cloud creates EMAIL_{id}.md in vault/Inbox/, generates draft in vault/Pending_Approval/Email/, commits to Git. (3) Local comes online at 8AM, pulls, sees draft in Obsidian. (4) User moves to vault/Approved/, Local sends via Email MCP.

**Effort**: 8-10 hours (depends on US4, US5)

### Implementation for User Story 1

- [ ] T040 [US1] Implement gmail_watcher.py in cloud_agent/src/watchers/ (24/7 Gmail inbox monitoring, detect high-priority, create vault/Inbox/ tasks) (L)
- [ ] T041 [US1] Integrate email_draft.py (from US5) with AI priority analysis from agent_skills/ai_analyzer.py (detect urgent keywords, generate draft within 15s) (M)
- [ ] T042 [US1] Implement Dashboard.md updater in Cloud orchestrator: append "Pending Local Approval: Email draft for {sender}" to /Updates/ section (M)
- [ ] T043 [US1] Implement urgent email detection: keywords="urgent", "asap", "emergency", "deadline today" → trigger WhatsApp notification (M)
- [ ] T044 [US1] Add retry logic: Cloud Agent vault write failure → retry 3x, log to vault/Logs/Cloud/errors.md, send WhatsApp alert (M)

### Integration Test for User Story 1

- [ ] T045 [US1] Integration test: Email arrives while Local offline → Cloud drafts → Local pulls → User approves → Email MCP sends in tests/integration/test_platinum_demo.py (L)

**Checkpoint**: Cloud Agent drafts emails 24/7; Local Agent sends after approval

---

## Phase 6: User Story 2 - Next.js Dashboard with One-Click Approvals (Priority: P1) 🎯 PORTFOLIO VALUE

**Goal**: Responsive web dashboard showing pending approvals (email, LinkedIn, WhatsApp, Odoo) with preview and one-click approve/reject buttons accessible on mobile

**Independent Test**: (1) Start Next.js server on Local Agent. (2) Open http://localhost:3000 in mobile browser. (3) Verify dashboard displays pending approval cards. (4) Click "Approve" on email draft. (5) Within 2s, file moved to vault/Approved/Email/, Email MCP sends, dashboard shows "Sent ✓".

**Effort**: 16-20 hours

### Implementation for User Story 2

- [ ] T046 [P] [US2] Create Next.js 14 App Router structure: app/page.tsx (home), app/approvals/page.tsx, app/health/page.tsx, app/api-usage/page.tsx, app/login/page.tsx (M)
- [ ] T047 [P] [US2] Create API route /api/status in app/api/status/route.ts (read vault/Pending_Approval/, return JSON: approval counts by category) (M)
- [ ] T048 [P] [US2] Create API route /api/approve in app/api/approve/route.ts (POST: move file from /Pending_Approval/ to /Approved/, return success JSON) (M)
- [ ] T049 [P] [US2] Create API route /api/reject in app/api/reject/route.ts (POST: move file to /Rejected/, append rejection reason to YAML frontmatter) (M)
- [ ] T050 [US2] Implement vault.ts utility in lib/vault.ts (read vault markdown files via filesystem, parse YAML frontmatter with gray-matter) (M)
- [ ] T051 [P] [US2] Create ApprovalCard.tsx component in components/ (type badge, title, preview text, Approve/Reject buttons) (M)
- [ ] T052 [P] [US2] Create PreviewModal.tsx component in components/ (full draft text, metadata, Approve/Reject in modal) (M)
- [ ] T053 [US2] Implement client-side polling in app/page.tsx (useEffect: fetch /api/status every 5s, update state without page reload) (M)
- [ ] T054 [US2] Implement Approve button handler: POST to /api/approve, show loading spinner, update UI to "Approved - Sending...", auto-remove card after 3s (M)
- [ ] T055 [US2] Implement Reject button handler: POST to /api/reject with optional reason text input, update UI to "Rejected", remove card (M)
- [ ] T056 [US2] Implement mobile-responsive layout with Tailwind CSS (cards stack vertically <768px, buttons ≥44px touch target, no horizontal scroll) (M)
- [ ] T057 [P] [US2] Implement DarkModeToggle.tsx component (localStorage persistence, Tailwind dark: classes, theme switch <200ms) (S)
- [ ] T058 [US2] Create Tailwind config in tailwind.config.js with dark mode colors (bg-[#1e1e1e], text-[#e0e0e0], cards bg-[#2d2d2d]) (S)
- [ ] T059 [US2] Implement simple password authentication in app/api/auth/login/route.ts (bcrypt.compare password, set session cookie 7-day expiry) (M)
- [ ] T060 [US2] Create middleware.ts to redirect unauthenticated users to /login (check session cookie, verify NEXT_AUTH_ENABLED=true) (M)
- [ ] T061 [P] [US2] Create login page UI in app/login/page.tsx (username/password form, submit to /api/auth/login) (S)
- [ ] T062 [US2] Implement offline fallback page in app/offline/page.tsx (cached message: "Dashboard offline - use Obsidian at {VAULT_PATH}") (S)

### Integration Tests for User Story 2

- [ ] T063 [P] [US2] Integration test: Dashboard API approve workflow (create draft → fetch /api/status → POST /api/approve → verify file moved) in tests/integration/test_dashboard_approval.py (M)
- [ ] T064 [P] [US2] E2E test: Dashboard mobile responsive layout (Playwright test at 375px width, verify cards stack, buttons ≥44px) in tests/e2e/test_dashboard_mobile.py (M)

**Checkpoint**: Next.js dashboard fully functional; one-click approvals work on desktop and mobile

---

## Phase 7: User Story 8 - Dashboard API Usage & MCP Health Monitoring (Priority: P2)

**Goal**: Dashboard displays real-time Claude API usage (calls today, cost this week) and MCP server health status (online/offline)

**Independent Test**: (1) Open dashboard. (2) Verify "API Usage" shows "Claude API: 47 calls today, $1.23 this week". (3) Verify "MCP Health" shows "Email MCP: ✓ Online (last call: 2 min ago), WhatsApp MCP: ✗ Offline (last call: 12 hours ago)".

**Effort**: 6-8 hours (depends on US2)

### Implementation for User Story 8

- [ ] T065 [P] [US8] Create API route /api/health in app/api/health/route.ts (poll MCP servers, return status grid: mcp_name, status, last_call_timestamp) (M)
- [ ] T066 [P] [US8] Create API route /api/api-usage in app/api/api-usage/route.ts (read vault/Logs/API_Usage/*.md, aggregate daily/weekly/monthly costs) (M)
- [ ] T067 [US8] Implement api-usage.ts utility in lib/api-usage.ts (parse YAML frontmatter from API_Usage logs, calculate totals, cost formula) (M)
- [ ] T068 [P] [US8] Create MCPHealthGrid.tsx component in components/ (grid layout: MCP name, ✓/✗ status, last call, Test button) (M)
- [ ] T069 [P] [US8] Create APIUsageChart.tsx component using Recharts (bar chart: daily cost for last 7 days, data from /api/api-usage) (M)
- [ ] T070 [US8] Integrate API usage logging in cloud_agent/src/orchestrator.py (log every Claude API call: timestamp, model, tokens, cost to vault/Logs/API_Usage/YYYY-MM-DD.md) (M)
- [ ] T071 [P] [US8] Integrate API usage logging in local_agent/src/orchestrator.py (same logging format, agent_id="local") (M)
- [ ] T072 [US8] Implement MCP health check in local_agent/src/executors/ (ping Email/WhatsApp/LinkedIn/Odoo MCPs, update vault/Logs/MCP_Health/{mcp}.md with status, last_call) (M)
- [ ] T073 [US8] Add cost alert logic: if weekly cost > COST_ALERT_THRESHOLD, dashboard shows warning banner, send WhatsApp alert (M)
- [ ] T074 [US8] Integrate API usage summary in CEO Briefing generator (weekly total, breakdown by agent, trend vs previous week) (S)

**Checkpoint**: Dashboard displays API costs and MCP health; cost alerts functional

---

## Phase 8: User Story 3 - Cross-Platform Notifications (Priority: P1)

**Goal**: Cloud Agent sends instant WhatsApp alerts when detecting urgent emails, critical errors, or time-sensitive approvals

**Independent Test**: (1) Configure Cloud with WHATSAPP_NOTIFICATION_NUMBER. (2) Trigger urgent email on Cloud. (3) Within 60s, WhatsApp notification received on phone: "⚠️ [URGENT] Email from {sender} | Approve: {url}". (4) Click dashboard URL, opens approval page.

**Effort**: 8-10 hours (depends on US1)

### Implementation for User Story 3

- [ ] T075 [US3] Implement whatsapp_notifier.py in cloud_agent/src/notifications/ (Playwright automation: send WhatsApp message, session persistence, retry 2x on failure) (L)
- [ ] T076 [US3] Implement WhatsApp notification message templates in whatsapp_notifier.py (urgent_email, critical_error, approval_summary, confirmation per contracts/notification-schema.yaml) (M)
- [ ] T077 [US3] Integrate WhatsApp notification trigger in gmail_watcher.py: when urgent email detected → send notification within 60s (M)
- [ ] T078 [US3] Implement critical error alert: Cloud Agent errors (Git sync failing >5 min, vault write failure, API quota exceeded) → WhatsApp notification (M)
- [ ] T079 [US3] Implement Local Agent approval summary: when Local comes online after Cloud generated 5+ drafts → send WhatsApp summary "📋 Good morning! 5 items pending..." (M)
- [ ] T080 [US3] Implement confirmation notification: after user approves + MCP sends → WhatsApp "✅ Email sent to {recipient}" (M)
- [ ] T081 [US3] Implement fallback to email: if WhatsApp send fails 3x → send email to FALLBACK_EMAIL instead, log to vault/Logs/Cloud/notification_failures.md (M)
- [ ] T082 [US3] Implement notification rate limiting: max 1 notification per minute (avoid WhatsApp spam detection) (S)
- [ ] T083 [US3] Add ENABLE_WHATSAPP_NOTIFICATIONS=false flag: skip sends but still log to vault/Notifications/sent.md for audit (S)

**Checkpoint**: WhatsApp notifications functional; urgent emails trigger instant alerts

---

## Phase 9: User Story 6 - Odoo Community 24/7 Cloud Deployment (Priority: P2)

**Goal**: Odoo Community hosted on Oracle Cloud VM with HTTPS, automated backups, health monitoring; Cloud Agent creates draft invoices/expenses 24/7

**Independent Test**: (1) SSH to Oracle VM. (2) Verify Odoo service running (systemctl status odoo). (3) Access https://{vm_ip}:8069. (4) Cloud Agent creates invoice draft task, verify Odoo draft entry created via JSON-RPC.

**Effort**: 10-12 hours (Oracle VM setup, Odoo installation, Nginx HTTPS, backups)

### Implementation for User Story 6

- [ ] T084 [US6] Create Oracle Cloud VM setup script in deployment/oracle-cloud/setup-vm.sh (provision VM, configure security list for ports 22, 443, 8069) (M)
- [ ] T085 [US6] Create Odoo installation script in deployment/oracle-cloud/install-odoo.sh (Ubuntu 22.04: install Odoo 19+, PostgreSQL, create platinum_business database) (L)
- [ ] T086 [US6] Create Nginx reverse proxy config in deployment/oracle-cloud/nginx-odoo.conf (proxy_pass to localhost:8069, HTTPS on port 443) (M)
- [ ] T087 [US6] Create Let's Encrypt SSL setup script in deployment/oracle-cloud/certbot-setup.sh (obtain SSL cert, auto-renewal cron) (M)
- [ ] T088 [US6] Create Odoo systemd service config with watchdog (Restart=always, RestartSec=5, auto-restart on crash within 60s) (S)
- [ ] T089 [US6] Create daily Odoo backup script in deployment/oracle-cloud/odoo-backup.sh (cron at 03:00 UTC: pg_dump to /opt/odoo_backups/, retain 30 days, log to /var/log/odoo_backup.log) (M)
- [ ] T090 [US6] Implement Odoo draft generator in cloud_agent/src/generators/odoo_draft.py (detect accounting tasks type="invoice"|"expense", AI extract data, save to vault/Pending_Approval/Odoo/) (L)
- [ ] T091 [US6] Implement Odoo MCP executor in local_agent/src/executors/odoo_poster.py (read vault/Approved/Odoo/, call Odoo JSON-RPC object.execute_kw to create draft, state="draft" not posted) (M)
- [ ] T092 [US6] Implement Odoo health monitor in cloud_agent/src/watchers/health_monitor.py (poll https://{odoo_url}/web/health every 5 min, update vault/Logs/Cloud/odoo_health.md) (M)
- [ ] T093 [US6] Implement Odoo health alerts: if service down → WhatsApp notification "🚨 Odoo restarted on cloud VM" (S)

**Checkpoint**: Odoo deployed on Oracle VM, accessible via HTTPS; Cloud creates drafts, Local posts to Odoo

---

## Phase 10: User Story 7 - Watchdog Auto-Restart with PM2 (Priority: P2)

**Goal**: All critical processes (watchers, orchestrator, Next.js) managed by PM2 with auto-restart on crash, startup on boot, health monitoring

**Independent Test**: (1) Start all via PM2 (pm2 start ecosystem.config.js). (2) Verify pm2 list shows all online. (3) Kill gmail_watcher (pm2 delete gmail_watcher). (4) Within 10s, PM2 auto-restarts. (5) Reboot VM, verify all auto-start.

**Effort**: 6-8 hours (PM2 config, systemd integration, log rotation)

### Implementation for User Story 7

- [ ] T094 [P] [US7] Create PM2 ecosystem config for Cloud in deployment/pm2/ecosystem.config.cloud.js (processes: cloud_orchestrator, gmail_watcher, git_sync_cloud with autorestart, max_restarts=10) (M)
- [ ] T095 [P] [US7] Create PM2 ecosystem config for Local in deployment/pm2/ecosystem.config.local.js (processes: local_orchestrator, whatsapp_watcher, git_sync_local, nextjs_dashboard) (M)
- [ ] T096 [US7] Configure PM2 startup hooks in quickstart.md (pm2 startup systemd, pm2 save, auto-start on VM/laptop boot) (S)
- [ ] T097 [US7] Configure PM2 log rotation (pm2 install pm2-logrotate: max_size=10M, retain=10, compress=true) (S)
- [ ] T098 [US7] Implement PM2 health monitoring in cloud_agent/src/watchers/health_monitor.py (check pm2 jlist, detect crash loops >5 restarts in 1 min, send WhatsApp alert) (M)
- [ ] T099 [US7] Implement PM2 resource monitoring: if process CPU >80% for >5 min OR memory >90%, log warning to ~/.pm2/logs/pm2.log (M)
- [ ] T100 [US7] Add graceful shutdown handlers in cloud_agent/src/orchestrator.py and local_agent/src/orchestrator.py (handle SIGTERM, save state before exit) (M)

**Checkpoint**: PM2 manages all processes; auto-restart on crash, startup on boot verified

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Production hardening, documentation, validation, deployment guides

**Effort**: 8-10 hours

- [ ] T101 [P] Create deployment guide in docs/platinum/deployment-guide.md (Oracle Cloud setup, Odoo installation, Next.js dashboard, Git sync initialization) (L)
- [ ] T102 [P] Create architecture diagram (text-based) in docs/platinum/architecture.md (Cloud Agent, Local Agent, Git Remote, WhatsApp notifications, Odoo flows) (M)
- [ ] T103 [P] Create security partition guide in docs/platinum/security-partition.md (Cloud vs Local credential boundaries, .gitignore enforcement, audit checklist) (M)
- [ ] T104 [P] Create Git sync strategy guide in docs/platinum/git-sync-strategy.md (60s batched commits, conflict resolution, retry policy) (M)
- [ ] T105 [P] Create upgrade checklist in docs/upgrade/gold-to-platinum.md (prerequisites, Cloud VM setup, Git remote config, backward compatibility validation) (M)
- [ ] T106 Validate quickstart.md: run full deployment from scratch on fresh Oracle VM and local machine, fix any errors (XL)
- [ ] T107 Run integration test suite: test_dual_agent_sync.py, test_claim_by_move.py, test_git_conflict.py, test_dashboard_approval.py, test_platinum_demo.py (M)
- [ ] T108 Verify backward compatibility: set ENABLE_CLOUD_AGENT=false, verify all Gold success criteria (SC-G001 through SC-G013) still pass (L)
- [ ] T109 [P] Create API usage cost tracking validation: log 100 Claude API calls, verify cost calculation accuracy within ±$0.05 (M)
- [ ] T110 [P] Create 30-day stability test plan: Cloud Agent runs 30 days, uptime ≥99%, zero unrecoverable errors, zero manual restarts (document in docs/platinum/stability-test.md) (S)
- [ ] T111 Security audit: scan Cloud .env for prohibited credentials (SMTP, WhatsApp session, bank tokens), verify .gitignore blocks sensitive files, check Git history for leaks (M)
- [ ] T112 Performance validation: Git sync <10s per cycle, dashboard load <2s (Lighthouse score >90), WhatsApp notification <60s, dashboard button click to file move <2s (M)
- [ ] T113 Create CEO Briefing API cost section: weekly total calls, total cost, breakdown by agent (Cloud: $X, Local: $Y), trend vs previous week (S)
- [ ] T114 Final code cleanup: remove debug logging, fix linting errors (ESLint for Next.js, flake8 for Python), update inline comments (M)
- [ ] T115 Create demo video script in docs/platinum/demo-script.md: email arrives 3AM while Local offline → Cloud drafts → WhatsApp notification → Local approves via dashboard → Email sends (S)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all user stories
- **User Story 4 (Git Sync) (Phase 3)**: Depends on Foundational (Phase 2) - **CRITICAL PATH** blocks US1, US3, US5
- **User Story 5 (Security Partition) (Phase 4)**: Depends on Foundational (Phase 2), US4 (Git Sync) - blocks US1, US6
- **User Story 1 (Email Triage) (Phase 5)**: Depends on US4 (Git Sync), US5 (Security Partition)
- **User Story 2 (Dashboard) (Phase 6)**: Depends on Foundational (Phase 2) - can start in parallel with US4/US5
- **User Story 8 (Dashboard Monitoring) (Phase 7)**: Depends on US2 (Dashboard)
- **User Story 3 (WhatsApp Notifications) (Phase 8)**: Depends on US1 (Email Triage), US4 (Git Sync)
- **User Story 6 (Odoo) (Phase 9)**: Depends on US5 (Security Partition), US4 (Git Sync)
- **User Story 7 (PM2 Watchdog) (Phase 10)**: Depends on US1, US2 (processes must exist to manage)
- **Polish (Phase 11)**: Depends on all user stories being complete

### Critical Path (Longest Dependency Chain)

```
Setup (Phase 1, 2-3h)
  ↓
Foundational (Phase 2, 6-8h)
  ↓
US4: Git Sync (Phase 3, 12-15h) ← CRITICAL PATH BLOCKER
  ↓
US5: Security Partition (Phase 4, 6-8h)
  ↓
US1: Email Triage (Phase 5, 8-10h)
  ↓
US3: WhatsApp Notifications (Phase 8, 8-10h)
  ↓
Polish (Phase 11, 8-10h)

Total Critical Path: ~60-72 hours
```

### Parallel Opportunities

**After Foundational (Phase 2) completes**:
- US4 (Git Sync) + US2 (Dashboard) can start in parallel (different codebases)

**After US4 (Git Sync) completes**:
- US5 (Security Partition) + US6 (Odoo) can start in parallel (different files)
- US2 (Dashboard) can continue independently

**After US2 (Dashboard) completes**:
- US8 (Dashboard Monitoring) can start immediately

**After US5 (Security Partition) completes**:
- US1 (Email Triage) can start immediately

**After US1 (Email Triage) completes**:
- US3 (WhatsApp Notifications) can start immediately

**Independent Work Streams** (can run in parallel if team capacity allows):
1. **Backend**: US4 → US5 → US1 → US3 (Cloud/Local agents, Git sync)
2. **Frontend**: US2 → US8 (Next.js dashboard)
3. **Infrastructure**: US6 (Odoo) + US7 (PM2) after US5

### User Story Dependencies Matrix

| Story | Depends On | Can Start After |
|-------|-----------|-----------------|
| US1 (Email Triage) | US4 (Git), US5 (Security) | Phase 2 + US4 + US5 |
| US2 (Dashboard) | Foundational only | Phase 2 |
| US3 (WhatsApp) | US1 (Email), US4 (Git) | Phase 2 + US1 + US4 |
| US4 (Git Sync) | Foundational only | Phase 2 ← **START HERE** |
| US5 (Security) | US4 (Git) | Phase 2 + US4 |
| US6 (Odoo) | US5 (Security), US4 (Git) | Phase 2 + US4 + US5 |
| US7 (PM2) | US1, US2 (processes exist) | Phase 2 + US1 + US2 |
| US8 (Monitoring) | US2 (Dashboard) | Phase 2 + US2 |

### Within Each User Story

- Tests (if included) → Implementation (ensure tests fail first)
- Models/entities → Services → API routes/executors
- Core implementation → Integration → Validation
- Story complete before moving to next priority

---

## Parallel Example: After Foundational Phase

**Team of 3 developers after Phase 2 completes:**

```bash
# Developer A (Backend Focus): Critical Path
Phase 3: US4 (Git Sync) - T017-T027 (12-15h)
  ↓
Phase 4: US5 (Security Partition) - T028-T039 (6-8h)
  ↓
Phase 5: US1 (Email Triage) - T040-T045 (8-10h)
  ↓
Phase 8: US3 (WhatsApp Notifications) - T075-T083 (8-10h)

# Developer B (Frontend Focus): Dashboard Track
Phase 6: US2 (Dashboard) - T046-T064 (16-20h)
  ↓
Phase 7: US8 (Dashboard Monitoring) - T065-T074 (6-8h)

# Developer C (Infrastructure Focus): Deployment Track
Phase 9: US6 (Odoo) - T084-T093 (10-12h) [wait for US5]
  ↓
Phase 10: US7 (PM2 Watchdog) - T094-T100 (6-8h) [wait for US1, US2]
```

**Coordination Points:**
- All wait for Phase 2 (Foundational) to complete
- Developer C waits for US5 (T028-T039) before starting US6
- Developer C waits for US1 + US2 before starting US7
- All converge at Phase 11 (Polish) for integration testing and deployment validation

---

## Implementation Strategy

### MVP First (Minimal Viable Platinum)

**Goal**: Demonstrate core Platinum capability: "Cloud drafts while Local offline, Local approves and sends"

**MVP Scope** (minimum for demo):
1. Phase 1: Setup (T001-T008) - 2-3h
2. Phase 2: Foundational (T009-T016) - 6-8h
3. Phase 3: US4 Git Sync (T017-T024, skip integration tests) - 10-12h
4. Phase 4: US5 Security Partition (T028-T031, T034-T035, skip tests) - 4-6h
5. Phase 5: US1 Email Triage (T040-T042, skip US3 WhatsApp) - 4-6h
6. Phase 6: US2 Dashboard (T046-T054, minimal UI, skip auth) - 10-12h

**MVP Total**: ~40-50 hours
**MVP Deliverable**: Cloud Agent drafts email while Local offline → Local Agent pulls via Git → User approves via basic dashboard → Email sends

### Incremental Delivery (Full Platinum)

**Iteration 1 (MVP)**: Setup + Foundational + US4 + US5 (minimal) + US1 (minimal) + US2 (minimal) → Demo: Cloud drafts, Local approves
**Iteration 2 (Enhanced)**: Add US3 (WhatsApp Notifications) + US8 (Dashboard Monitoring) → Demo: Instant WhatsApp alerts, API cost tracking
**Iteration 3 (Production)**: Add US6 (Odoo) + US7 (PM2 Watchdog) → Demo: 24/7 Odoo, auto-restart on crash
**Iteration 4 (Polish)**: Phase 11 (Documentation, integration tests, security audit, 30-day stability test) → Production-ready

---

## Effort Summary

| Phase | User Story | Tasks | Effort (Hours) |
|-------|-----------|-------|----------------|
| Phase 1 | Setup | T001-T008 | 2-3 |
| Phase 2 | Foundational | T009-T016 | 6-8 |
| Phase 3 | US4 (Git Sync) | T017-T027 | 12-15 |
| Phase 4 | US5 (Security) | T028-T039 | 6-8 |
| Phase 5 | US1 (Email Triage) | T040-T045 | 8-10 |
| Phase 6 | US2 (Dashboard) | T046-T064 | 16-20 |
| Phase 7 | US8 (Monitoring) | T065-T074 | 6-8 |
| Phase 8 | US3 (WhatsApp) | T075-T083 | 8-10 |
| Phase 9 | US6 (Odoo) | T084-T093 | 10-12 |
| Phase 10 | US7 (PM2) | T094-T100 | 6-8 |
| Phase 11 | Polish | T101-T115 | 8-10 |
| **TOTAL** | **All Phases** | **115 tasks** | **88-112 hours** |

**MVP Estimate** (Iterations 1-2): ~50-60 hours
**Production-Ready Estimate** (All iterations): ~88-112 hours

---

## Notes

- **[P] tasks**: Different files, no dependencies within phase → can run in parallel
- **[Story] label**: Maps task to user story (US1-US8) for traceability
- **Effort estimates**: S=1-2h, M=3-5h, L=6-8h, XL=1-2 days (use for planning, not strict deadlines)
- **Critical path**: US4 (Git Sync) is the bottleneck → prioritize this for fastest delivery
- **Parallel opportunities**: US2 (Dashboard) can run independently while US4/US5 are in progress
- **Integration tests**: Included for critical workflows (Git sync, dashboard, security partition)
- **Backward compatibility**: T108 validates all Gold features still work (no regression)
- **Security partition**: T030, T038, T111 enforce Cloud never accesses sensitive credentials
- **Commit frequently**: After each task or logical group, commit to Git for incremental progress
- **Avoid**: Same-file edits across parallel tasks, cross-story dependencies that break independence

---

**Tasks.md generated. Ready for `/sp.implement` or manual implementation in priority order (US4 → US5 → US1 → US2 → US3 → US6 → US7 → US8 → Polish).**
