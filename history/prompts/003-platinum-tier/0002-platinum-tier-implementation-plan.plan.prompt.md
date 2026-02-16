---
id: 0002
title: Platinum tier implementation plan
stage: plan
date: 2026-02-15
surface: agent
model: claude-sonnet-4.5
feature: 003-platinum-tier
branch: 003-platinum-tier
user: Psqasim
command: /sp.plan
labels: ["planning", "architecture", "platinum-tier", "dual-agent", "nextjs", "git-sync"]
links:
  spec: /specs/003-platinum-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-platinum-tier/plan.md
  - specs/003-platinum-tier/research.md
  - specs/003-platinum-tier/data-model.md
  - specs/003-platinum-tier/contracts/dashboard-api.yaml
  - specs/003-platinum-tier/contracts/git-sync-protocol.md
  - specs/003-platinum-tier/contracts/notification-schema.yaml
  - specs/003-platinum-tier/contracts/mcp-health-check.yaml
  - specs/003-platinum-tier/quickstart.md
tests:
  - None (planning phase, no tests generated yet)
---

## Prompt

Create comprehensive implementation plan for Platinum tier.

CRITICAL REQUIREMENTS:
1. Use existing Agent Skills from .claude/skills/
2. Reference Context7 MCP for documentation
3. Incremental delivery:
   - Phase 1: Cloud setup (Oracle VM)
   - Phase 2: Git vault sync
   - Phase 3: Next.js dashboard
   - Phase 4: WhatsApp notifications
   - Phase 5: Production deployment

ARCHITECTURE DECISIONS NEEDED:
1. Next.js deployment (Vercel vs self-hosted)
2. Database for UI state (SQLite vs PostgreSQL vs none)
3. Real-time updates (WebSockets vs polling)
4. Authentication (NextAuth vs simple token vs skip)
5. Git sync strategy (auto-commit vs manual triggers)

TECH STACK:
- Frontend: Next.js 14, TypeScript, Tailwind, shadcn/ui
- Backend: Next.js API routes OR FastAPI
- Cloud: Oracle Cloud Free Tier (Ubuntu 22.04)
- Database: TBD based on complexity
- Process Manager: PM2 (both cloud + local)
- Vault Sync: Git with auto-pull/push
- Monitoring: PM2 dashboard + custom health checks

DELIVERABLES:
1. Implementation plan (plan.md)
2. Technology decisions (research.md)
3. Data model (data-model.md)
4. API contracts (contracts/)
5. Deployment guide (quickstart.md)

Reference Gold tier patterns from specs/002-gold-tier/
Make decisions optimized for portfolio + production use.

## Response snapshot

**Phase 0: Research & Architecture Decisions**

Created comprehensive research.md resolving all architectural unknowns:

1. **Next.js Deployment**: Self-hosted on Local Agent (port 3000) — aligns with local-first architecture, zero cost, instant vault access
2. **Database**: None (read vault directly) — simplicity, vault is source of truth, <500ms performance sufficient
3. **Real-Time Updates**: HTTP polling (5s interval) — simple, acceptable latency, stateless, survives PM2 restarts
4. **Authentication**: Simple bcrypt password + cookie — single-user, optional disable for localhost-only
5. **Git Sync**: Batched commits (60s interval) — atomic batches, reduces noise, meets <10s sync latency requirement
6. **Odoo Deployment**: systemd service on Oracle VM — 24/7 availability, free infrastructure, production-grade
7. **PM2 Configuration**: Ecosystem files (Cloud + Local) — unified process management, systemd startup, log rotation
8. **WhatsApp Notifications**: Playwright automation — free, works with personal account, proven pattern from Gold tier

**Phase 1: Design Artifacts**

1. **plan.md**: Comprehensive technical architecture with:
   - Summary: Dual-agent (Cloud + Local) with Next.js dashboard, Git sync, WhatsApp notifications
   - Technical Context: Python 3.11+, Next.js 14, Oracle Cloud VM, PM2, GitPython
   - Constitution Check: ✅ All Platinum requirements met, backward compatibility guaranteed
   - Project Structure: Dual-agent web application (cloud_agent/, local_agent/, nextjs_dashboard/, shared agent_skills/)

2. **data-model.md**: 9 new entities + inherited Gold entities:
   - CloudAgent, LocalAgent (dual-agent architecture)
   - GitSyncState (sync coordination with conflict resolution)
   - DashboardApproval (Next.js UI state)
   - WhatsAppNotification (cross-platform alerts)
   - MCPServerHealth (real-time monitoring)
   - APIUsageLog (cost tracking)
   - OdooInstance (24/7 cloud deployment)
   - PM2Process (watchdog monitoring)

3. **contracts/** (4 files):
   - dashboard-api.yaml (OpenAPI 3.0): POST /api/approve, POST /api/reject, GET /api/status, GET /api/health
   - git-sync-protocol.md: Commit conventions, conflict resolution algorithm (Dashboard.md ownership rules), retry policy
   - notification-schema.yaml: WhatsApp message templates (urgent_email, critical_error, approval_summary, confirmation)
   - mcp-health-check.yaml (OpenAPI 3.0): GET /health endpoint for all MCP servers

4. **quickstart.md**: 6-phase deployment guide (3-4 hour estimated setup):
   - Phase 1: Cloud Agent Setup (Oracle VM provisioning, PM2 config)
   - Phase 2: Odoo Deployment (systemd, Nginx HTTPS, daily backups)
   - Phase 3: Local Agent Setup (WhatsApp session, PM2 config)
   - Phase 4: Next.js Dashboard (build, auth, mobile access)
   - Phase 5: Git Sync Initialization (remote repo, SSH keys, .gitignore)
   - Phase 6: End-to-End Testing (4 integration tests)

**Key Design Decisions**:
- Self-hosted dashboard on Local (not Vercel) preserves local-first architecture
- No separate database; vault markdown files are sufficient (<500ms read performance)
- HTTP polling (5s) over WebSockets for simplicity and stateless operation
- Git batched commits (60s) balance latency vs commit noise
- Structured Dashboard.md merge resolution (Cloud owns /Updates/, Local owns /Pending Approvals/)

## Outcome

- ✅ Impact: All 5 deliverables created (plan.md, research.md, data-model.md, contracts/, quickstart.md). 8 architecture decisions locked. Ready for /sp.tasks to generate implementation tasks.
- 🧪 Tests: No tests in planning phase. Integration tests defined in quickstart.md Phase 6 (dual-agent sync, dashboard approval, WhatsApp notifications, MCP health).
- 📁 Files: 8 files created (1 plan, 1 research, 1 data-model, 4 contracts, 1 quickstart). Project structure defined (cloud_agent/, local_agent/, nextjs_dashboard/, agent_skills/).
- 🔁 Next prompts: /sp.tasks 003-platinum-tier to generate dependency-ordered tasks.md. Then /sp.implement to execute tasks.
- 🧠 Reflection: Successfully balanced complexity (dual-agent, Git sync, Next.js) with simplicity (no DB, HTTP polling, self-hosted). All decisions optimized for hackathon portfolio + production readiness. Security partition (Cloud vs Local credentials) enforced at architecture level.

## Evaluation notes (flywheel)

- Failure modes observed: None during planning. Potential runtime failures identified: Git merge conflicts (mitigated by auto-resolve algorithm), WhatsApp session expiry (mitigated by graceful degradation), MCP offline (mitigated by health monitoring + retry logic).
- Graders run and results (PASS/FAIL): Constitution Check: PASS (all Platinum requirements met, no violations). Backward Compatibility: PASS (all Gold/Silver/Bronze features preserved). Security Partition: PASS (Cloud .env excludes sensitive credentials).
- Prompt variant (if applicable): N/A (standard /sp.plan workflow)
- Next experiment (smallest change to try): Test Git conflict resolution algorithm with synthetic Dashboard.md conflicts before full deployment. Validate WhatsApp Playwright send automation with test notification.
