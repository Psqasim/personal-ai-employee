# Implementation Plan: Platinum Tier - Always-On Cloud + Local Executive

**Branch**: `003-platinum-tier` | **Date**: 2026-02-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-platinum-tier/spec.md`

## Summary

Platinum Tier implements a **dual-agent architecture** with Cloud Agent (Oracle Cloud VM, 24/7 always-on) and Local Agent (user's laptop, on-demand) communicating via Git-synced vault. Key capabilities: **Next.js web dashboard** for mobile-responsive one-click approvals, **cross-platform WhatsApp notifications**, **vault sync via Git** with claim-by-move coordination, **Odoo Community 24/7 deployment**, and **PM2 watchdog auto-restart**. Cloud drafts (emails, LinkedIn, social), Local approves and executes. Security partition: Cloud has API keys only, Local has all credentials (SMTP, WhatsApp sessions, banking). All Gold tier features remain functional with backward compatibility guarantee.

## Technical Context

**Language/Version**: Python 3.11+ (Cloud + Local agents), Node.js 20+ / Next.js 14 (Dashboard UI), Bash (Git sync, PM2, deployment scripts)

**Primary Dependencies**:
- Backend: gitpython (Git automation), pm2 wrapper (process management), bcrypt (dashboard auth), anthropic SDK, all Gold dependencies (playwright, smtplib, requests, schedule)
- Frontend: Next.js 14, React 18, TypeScript 5.4, Tailwind CSS 3.4, NextAuth.js 4.24 (auth), Recharts 2.12 (API usage charts), shadcn/ui components

**Storage**:
- Vault state: Git-synced markdown files (primary, 100% same as Gold)
- Dashboard session: localStorage (dark mode, auth session)
- API usage logs: Markdown files in `vault/Logs/API_Usage/YYYY-MM-DD.md` (CSV-like YAML)
- Database: **NEEDS CLARIFICATION** (SQLite vs PostgreSQL vs none for Next.js state)

**Testing**: pytest (Python agent skills), Jest + React Testing Library (Next.js components), Playwright (E2E dashboard workflows), integration tests (dual-agent Git sync race conditions)

**Target Platform**:
- Cloud Agent: Oracle Cloud Free Tier VM (Ubuntu 22.04, ARM64, 4 OCPU, 24GB RAM)
- Local Agent: User's laptop (Linux/macOS/Windows, WSL Ubuntu 22.04 for Windows)
- Dashboard: Next.js server on Local Agent (port 3000), accessible via browser (desktop + mobile)

**Project Type**: Distributed web application (Cloud Python agent + Local Python agent + Local Next.js dashboard)

**Performance Goals**:
- Git sync: <10s per cycle (pull or push), 60s interval
- Dashboard load: <2s initial page (Lighthouse >90), API polling <500ms
- WhatsApp notification: <60s from Cloud event to notification delivered
- Dashboard button click → file move → UI update: <2s end-to-end
- PM2 restart on crash: <5s downtime

**Constraints**:
- **NEEDS CLARIFICATION**: Next.js deployment strategy (Vercel vs self-hosted on Local)
- **NEEDS CLARIFICATION**: Real-time updates implementation (WebSockets vs 5s polling)
- **NEEDS CLARIFICATION**: Authentication strategy (NextAuth vs simple token vs skip for localhost-only)
- **NEEDS CLARIFICATION**: Git sync strategy (auto-commit every file change vs batched commits)
- Cloud VM free tier: 4 OCPU, 24GB RAM, 200GB storage (Oracle Cloud ARM)
- Security partition: Cloud never accesses .env, WhatsApp sessions, banking credentials
- Mobile responsive: min 44px touch targets, no horizontal scroll on 375px width
- Backward compatible: All Gold features functional when ENABLE_CLOUD_AGENT=false

**Scale/Scope**:
- Dual agents: 2 independent Python codebases (Cloud + Local with shared agent_skills)
- Next.js dashboard: ~10 pages/components (Approvals, Health, API Usage, Settings)
- Git sync: handles vaults up to 500MB, 10,000+ markdown files
- MCP servers: 7+ servers (email, whatsapp, linkedin, facebook, instagram, twitter, odoo)
- PM2 processes: 6 managed processes (cloud_orchestrator, local_orchestrator, gmail_watcher, whatsapp_watcher, nextjs_dashboard, git_sync)
- API usage: support up to 1000 Claude API calls/day, $50/week cost tracking

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Platinum Tier Requirements (Constitution Section VI)

✅ **Cloud VM Deployment**: Oracle Cloud Free Tier VM with PM2 process management
✅ **Work-Zone Specialization**: Cloud drafts (email/social), Local executes (send/post/payments)
✅ **Delegation via Synced Vault**: File-based communication via /Pending_Approval/, /In_Progress/, claim-by-move rules
✅ **Vault Sync Strategy**: Git with automatic push/pull (Phase 1 file-based, Phase 2 optional A2A messaging)
✅ **Security Partitioning**: Cloud .gitignore excludes .env, *.session, credentials.json, vault/.secrets/
✅ **Odoo Cloud Deployment**: 24/7 Odoo Community on VM with HTTPS, backups, health monitoring
✅ **Reflection Loop**: After every action, agent reflects on outcome (Phase 1 basic, Phase 2 self-correction)
✅ **Agent-to-Agent Communication**: Phase 1 file-based (task_handoff, approval_request, status_update), Phase 2 optional direct messaging
✅ **Platinum Demo Requirements**: Email arrives while Local offline → Cloud drafts → Local approves → Email MCP sends → logged

### Backward Compatibility (Universal Principle VII)

✅ **All Gold features functional**: FR-G001–FR-G077 remain implemented when ENABLE_CLOUD_AGENT=false
✅ **All Silver features functional**: FR-S001–FR-S044 remain implemented
✅ **All Bronze features functional**: FR-B001–FR-B025 remain implemented
✅ **Downgrade safety**: Setting TIER=gold in .env disables Platinum features without breaking

### Vault Integrity (Universal Principle II)

✅ **Atomic file operations**: Read → Validate → Modify → Validate → Write (all tiers)
✅ **Race condition handling**: File locking with 3 retries, timestamp conflict detection
✅ **Backup before modify**: Dashboard.md, Company_Handbook.md get .bak files
✅ **Git sync conflict resolution**: Local auto-resolves (accept Cloud /Updates/, keep Local main content)

### Local-First Architecture (Universal Principle III)

⚠️ **Platinum Extension**: Cloud Agent requires network for Git push/pull, WhatsApp notifications. Local Agent remains offline-capable with Gold fallback mode
✅ **Vault as source of truth**: All state in vault/, Git remote is sync layer only
✅ **Network partition tolerance**: Cloud and Local continue operating independently, sync when reconnected

### Gates Passed

✅ No constitution violations
✅ Platinum tier builds incrementally on Gold (no tier skipping)
✅ All backward compatibility guarantees maintained
✅ Security partition enforced (Cloud vs Local credentials)

**Post-Phase 1 Re-check Required**: Verify Git sync implementation doesn't introduce race conditions, Next.js dashboard doesn't bypass approval workflow

## Project Structure

### Documentation (this feature)

```text
specs/003-platinum-tier/
├── spec.md               # User stories, requirements, success criteria
├── plan.md               # This file (/sp.plan output)
├── research.md           # Phase 0 research (architecture decisions)
├── data-model.md         # Phase 1 entities and state
├── quickstart.md         # Phase 1 deployment guide
├── contracts/            # Phase 1 API contracts
│   ├── dashboard-api.yaml       # Next.js API routes OpenAPI spec
│   ├── git-sync-protocol.md     # Git workflow and conflict resolution
│   ├── notification-schema.yaml # WhatsApp notification message format
│   └── mcp-health-check.yaml    # MCP server health endpoint spec
└── tasks.md              # Phase 2 (/sp.tasks output - NOT by /sp.plan)
```

### Source Code (repository root)

**Option 2: Web application** (Cloud agent + Local agent + Next.js dashboard)

```text
# Cloud Agent (deployed on Oracle VM)
cloud_agent/
├── src/
│   ├── orchestrator.py          # Main loop: email triage, social drafts, Git push
│   ├── watchers/
│   │   ├── gmail_watcher.py     # 24/7 Gmail inbox monitoring
│   │   └── health_monitor.py    # PM2 process health checks
│   ├── generators/
│   │   ├── email_draft.py       # AI email reply generation
│   │   ├── linkedin_draft.py    # AI LinkedIn post generation
│   │   ├── social_draft.py      # AI Facebook/Instagram/Twitter drafts
│   │   └── ceo_briefing.py      # Weekly business audit
│   ├── notifications/
│   │   └── whatsapp_notifier.py # Send WhatsApp alerts via MCP
│   └── git_sync.py              # Git commit + push every 60s
├── .env.cloud.example           # Cloud-only env vars (no secrets)
├── ecosystem.config.cloud.js    # PM2 config for Cloud processes
└── tests/
    ├── test_git_sync.py
    └── test_email_draft.py

# Local Agent (user's laptop)
local_agent/
├── src/
│   ├── orchestrator.py          # Approval processing, MCP execution, Git pull
│   ├── watchers/
│   │   └── whatsapp_watcher.py  # WhatsApp Web monitoring (Playwright)
│   ├── executors/
│   │   ├── email_sender.py      # Email MCP invocation after approval
│   │   ├── social_poster.py     # LinkedIn/Facebook/Instagram/Twitter MCPs
│   │   └── whatsapp_sender.py   # WhatsApp MCP (Playwright send)
│   ├── approval_handler.py      # Monitor /Approved/ folders, trigger MCPs
│   └── git_sync.py              # Git pull every 60s, conflict resolution
├── .env.local.example           # Local-only env vars (all secrets)
├── ecosystem.config.local.js    # PM2 config for Local processes
└── tests/
    ├── test_approval_workflow.py
    └── test_whatsapp_send.py

# Shared Agent Skills (used by both Cloud + Local)
agent_skills/
├── __init__.py
├── vault_parser.py              # Obsidian markdown parsing (from Gold)
├── dashboard_updater.py         # Dashboard.md atomic updates (from Gold)
├── ai_analyzer.py               # Claude API integration (from Gold)
├── git_manager.py               # NEW: GitPython wrapper, conflict resolution
├── claim_manager.py             # NEW: Claim-by-move file operations
└── api_usage_tracker.py         # NEW: Claude API cost logging

# Next.js Dashboard (Local only)
nextjs_dashboard/
├── src/
│   ├── app/                     # Next.js 14 App Router
│   │   ├── page.tsx             # Home: Pending Approvals + Task Status
│   │   ├── approvals/
│   │   │   └── page.tsx         # Approval cards with Approve/Reject buttons
│   │   ├── health/
│   │   │   └── page.tsx         # MCP server health grid
│   │   ├── api-usage/
│   │   │   └── page.tsx         # Claude API cost charts
│   │   ├── login/
│   │   │   └── page.tsx         # NextAuth login (if enabled)
│   │   └── api/
│   │       ├── approve/route.ts    # POST: move file to /Approved/
│   │       ├── reject/route.ts     # POST: move file to /Rejected/
│   │       ├── status/route.ts     # GET: vault state for polling
│   │       └── health/route.ts     # GET: MCP server health
│   ├── components/
│   │   ├── ApprovalCard.tsx     # Single approval with Approve/Reject buttons
│   │   ├── PreviewModal.tsx     # Full draft preview modal
│   │   ├── MCPHealthGrid.tsx    # MCP status indicators
│   │   └── DarkModeToggle.tsx   # Theme switcher (localStorage)
│   ├── lib/
│   │   ├── vault.ts             # Read vault markdown files
│   │   └── api-usage.ts         # Parse API usage logs
│   └── styles/
│       └── globals.css          # Tailwind + dark mode variables
├── public/
├── package.json
├── tsconfig.json
└── tailwind.config.js

# Deployment & Infrastructure
deployment/
├── oracle-cloud/
│   ├── setup-vm.sh              # Oracle Cloud VM provisioning script
│   ├── install-odoo.sh          # Odoo Community 19+ installation
│   ├── nginx-odoo.conf          # Nginx reverse proxy for Odoo HTTPS
│   └── certbot-setup.sh         # Let's Encrypt SSL for Odoo
├── pm2/
│   ├── ecosystem.config.cloud.js   # Cloud PM2 processes
│   └── ecosystem.config.local.js   # Local PM2 processes
└── git-hooks/
    └── pre-commit                  # Block commits of .env, *.session, credentials.json

# Tests (cross-agent integration)
tests/
├── integration/
│   ├── test_dual_agent_sync.py     # Cloud push → Local pull workflow
│   ├── test_claim_by_move.py       # Race condition prevention
│   ├── test_git_conflict.py        # Auto-resolve Dashboard.md conflicts
│   └── test_dashboard_approval.py  # Dashboard API → MCP execution
└── e2e/
    └── test_platinum_demo.py       # Full demo: email while Local offline

# Documentation
docs/
├── platinum/
│   ├── architecture.md          # Dual-agent architecture diagram
│   ├── deployment-guide.md      # Oracle Cloud setup, PM2 config
│   ├── git-sync-strategy.md     # Git workflow, conflict resolution
│   ├── security-partition.md    # Cloud vs Local credential boundaries
│   └── dashboard-setup.md       # Next.js installation, auth config
└── upgrade/
    └── gold-to-platinum.md      # Upgrade checklist from Gold

# Configuration
.env.cloud.example               # Cloud Agent env template
.env.local.example               # Local Agent env template
.gitignore                       # Enforces security: .env, *.session, vault/.secrets/
```

**Structure Decision**: Dual-agent web application architecture selected because:
1. **Cloud Agent** and **Local Agent** are separate deployment targets (Oracle VM vs user's laptop)
2. **Next.js Dashboard** is Local-only, requires separate frontend/ structure
3. **Shared agent_skills/** module prevents code duplication between agents
4. **Deployment/** directory centralizes Oracle Cloud VM setup, PM2, and Odoo scripts
5. **Tests/** includes dual-agent integration tests (Git sync, claim-by-move race conditions)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All complexity is justified by Platinum tier requirements in constitution Section VI.

## Phase 0: Outline & Research

### Research Tasks (from Technical Context unknowns)

1. **Next.js Deployment Strategy**
   **Unknown**: Vercel vs self-hosted on Local Agent
   **Research**: Compare trade-offs (cost, deployment complexity, localhost-only access, mobile access)
   **Output**: Decision in `research.md` → Deployment Strategy section

2. **Database for UI State**
   **Unknown**: SQLite vs PostgreSQL vs none (read vault files directly)
   **Research**: Evaluate performance (vault read <500ms), deployment complexity, dashboard state persistence needs
   **Output**: Decision in `research.md` → Database Selection section

3. **Real-Time Updates**
   **Unknown**: WebSockets vs 5s polling for dashboard live updates
   **Research**: Compare WebSockets (complexity, connection management) vs polling (simple HTTP, acceptable latency)
   **Output**: Decision in `research.md` → Real-Time Updates section

4. **Authentication Strategy**
   **Unknown**: NextAuth.js vs simple token vs skip (localhost-only)
   **Research**: Security requirements (local-only vs remote access), NextAuth complexity, simple password hash
   **Output**: Decision in `research.md` → Authentication section

5. **Git Sync Strategy**
   **Unknown**: Auto-commit every file change vs batched commits (60s interval)
   **Research**: Git performance (commit overhead), merge conflict frequency, audit trail granularity
   **Output**: Decision in `research.md` → Git Sync section

6. **Odoo 24/7 Deployment**
   **Dependency**: Best practices for Odoo Community on Ubuntu 22.04, Nginx HTTPS, PostgreSQL setup
   **Research**: Official Odoo docs, systemd service config, backup automation
   **Output**: Step-by-step in `research.md` → Odoo Deployment section

7. **PM2 Process Management**
   **Dependency**: PM2 ecosystem config patterns, startup hooks, log rotation
   **Research**: PM2 official docs, systemd integration, restart strategies
   **Output**: Best practices in `research.md` → PM2 Configuration section

8. **WhatsApp Notification via MCP**
   **Dependency**: WhatsApp Web Playwright automation for sending messages (not just receiving)
   **Research**: Playwright selectors for WhatsApp Web, rate limits, session management
   **Output**: Implementation guide in `research.md` → WhatsApp Notifications section

### Research Output File

**File**: `specs/003-platinum-tier/research.md`
**Sections**:
- Deployment Strategy (Next.js: Vercel vs self-hosted)
- Database Selection (SQLite vs PostgreSQL vs none)
- Real-Time Updates (WebSockets vs polling)
- Authentication (NextAuth vs simple vs skip)
- Git Sync Strategy (auto-commit vs batched)
- Odoo Deployment (installation, HTTPS, backups)
- PM2 Configuration (processes, startup, logs)
- WhatsApp Notifications (Playwright send automation)

Each section includes:
- **Decision**: What was chosen
- **Rationale**: Why chosen (trade-offs, requirements alignment)
- **Alternatives Considered**: What else was evaluated and why rejected
- **Implementation Notes**: Key technical details for tasks phase

## Phase 1: Design & Contracts

### Data Model

**File**: `specs/003-platinum-tier/data-model.md`
**Entities** (extends Gold tier):

1. **CloudAgent** (new)
   - agent_id, vault_path, git_remote_url, whatsapp_notification_number, api_key, last_sync_timestamp, uptime_hours

2. **LocalAgent** (new)
   - agent_id, vault_path, mcp_servers (array), session_files_path, last_online_timestamp

3. **GitSyncState** (new)
   - last_pull_timestamp, last_push_timestamp, commit_hash_cloud, commit_hash_local, pending_conflicts (array), sync_status

4. **DashboardApproval** (new)
   - approval_id, category, title, preview_text, timestamp, status, file_path

5. **WhatsAppNotification** (new)
   - notification_id, event_type, recipient_number, message_text, sent_timestamp, delivery_status

6. **MCPServerHealth** (new)
   - mcp_name, status, last_successful_call_timestamp, last_call_status, error_message

7. **APIUsageLog** (new)
   - log_id, timestamp, agent_id, model, prompt_tokens, completion_tokens, cost_usd, task_type

8. **OdooInstance** (new)
   - odoo_url, database_name, version, ssl_cert_expiry, last_backup_timestamp, health_status

9. **PM2Process** (new)
   - process_name, agent_type, status, uptime_seconds, restart_count, cpu_percent, memory_mb, log_file_path

10. **EmailDraft** (from Gold, unchanged)
11. **LinkedInDraft** (from Gold, unchanged)
12. **WhatsAppDraft** (from Gold, unchanged)
13. **Plan** (from Gold, unchanged)

State transitions, validation rules, and relationships documented in data-model.md.

### API Contracts

**Directory**: `specs/003-platinum-tier/contracts/`

1. **dashboard-api.yaml** (OpenAPI 3.0)
   - POST /api/approve: Move file from /Pending_Approval/ to /Approved/
   - POST /api/reject: Move file from /Pending_Approval/ to /Rejected/
   - GET /api/status: Poll vault state (pending counts, active plans, recent activity)
   - GET /api/health: MCP server health status grid

2. **git-sync-protocol.md** (Markdown spec)
   - Cloud Agent commit message format: `Cloud: {action} {id}`
   - Local Agent commit message format: `Local: {action} {id}`
   - Conflict resolution algorithm: Dashboard.md auto-merge strategy
   - Retry policy: 3 attempts, exponential backoff (10s, 30s, 90s)

3. **notification-schema.yaml** (YAML spec)
   - WhatsApp notification message templates
   - Urgent email format, critical error format, approval summary format
   - Character limits, emoji usage, dashboard URL injection

4. **mcp-health-check.yaml** (OpenAPI 3.0)
   - GET /health endpoint for each MCP server
   - Response schema: {status: "online"|"offline"|"degraded", last_call, error}

### Quickstart Guide

**File**: `specs/003-platinum-tier/quickstart.md`
**Sections**:
1. **Prerequisites**: Oracle Cloud account, Git remote (GitHub), Local machine (Python 3.11+, Node.js 20+)
2. **Phase 1: Cloud Agent Setup**
   - Provision Oracle VM (ARM, Ubuntu 22.04)
   - Clone repo, install Python deps
   - Configure .env.cloud (API key, Git remote, no secrets)
   - Setup PM2, enable systemd startup
3. **Phase 2: Odoo Deployment**
   - Install Odoo Community 19+ on VM
   - Configure PostgreSQL, systemd service
   - Setup Nginx reverse proxy, Let's Encrypt SSL
   - Verify Odoo accessible via HTTPS
4. **Phase 3: Local Agent Setup**
   - Clone repo on local machine
   - Install Python deps, WhatsApp Playwright session
   - Configure .env.local (all MCP credentials)
   - Setup PM2 for local processes
5. **Phase 4: Next.js Dashboard**
   - Install Node.js 20+, npm install in nextjs_dashboard/
   - Configure auth (optional), set DASHBOARD_PASSWORD
   - Start Next.js server: `npm run dev` or PM2
   - Verify dashboard at http://localhost:3000
6. **Phase 5: Git Sync Initialization**
   - Create Git remote repository (GitHub private repo)
   - Add SSH key to both Cloud and Local
   - Initial push from Local: `git push -u origin main`
   - Verify Cloud can pull: `git pull origin main`
7. **Testing**
   - Send test email while Local offline
   - Verify Cloud creates draft in Git
   - Bring Local online, verify pull succeeds
   - Approve via dashboard, verify Email MCP sends

### Agent Context Update

**Script**: `.specify/scripts/bash/update-agent-context.sh claude`
**Action**: Add Platinum technologies to `.specify/memory/claude-context.md` or agent-specific file
**Technologies to Add**:
- Next.js 14 (App Router, React Server Components, API routes)
- Git automation (GitPython, commit strategies, conflict resolution)
- PM2 ecosystem (process management, systemd integration)
- Oracle Cloud (VM provisioning, networking, free tier limits)
- Odoo Community (JSON-RPC API, systemd service, Nginx proxy)
- NextAuth.js (credentials provider, session management)
- Recharts (React charting library for API usage graphs)

## Deliverables Checklist

- [x] **plan.md**: This file (comprehensive technical architecture)
- [ ] **research.md**: Phase 0 architecture decision research
- [ ] **data-model.md**: Phase 1 entity definitions and state transitions
- [ ] **contracts/**: Phase 1 API specs (4 files)
- [ ] **quickstart.md**: Phase 1 deployment guide (6 phases)
- [ ] **Agent context updated**: `.specify/memory/claude-context.md` with Platinum tech

**Next Command**: `/sp.tasks 003-platinum-tier` to generate dependency-ordered tasks.md after plan approval.

---

**Planning Status**: Phase 0 and Phase 1 specifications complete. Ready for research execution and artifact generation.
