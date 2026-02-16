---
id: 0001
title: Create Platinum tier spec
stage: spec
date: 2026-02-15
surface: agent
model: claude-sonnet-4.5
feature: 003-platinum-tier
branch: 003-platinum-tier
user: system
command: /sp.specify
labels: ["platinum-tier", "cloud-deployment", "nextjs-dashboard", "whatsapp-notifications", "dual-agent", "git-sync"]
links:
  spec: specs/003-platinum-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/003-platinum-tier/spec.md
tests:
 - none (specification phase)
---

## Prompt

```
003-platinum-tier
BISMILLAH! Starting Platinum Tier with Next.js UI + Notifications.

IMPORTANT REFERENCES:
1. Read hackathon requirements: Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md
2. Use Context7 MCP for documentation and knowledge retrieval
3. Leverage existing Agent Skills from .claude/skills/

Create comprehensive Platinum tier specification:

PLATINUM CORE (from Hackathon Doc):
- 24/7 Cloud deployment (Oracle Cloud Free VM)
- Work-Zone Specialization:
  * Cloud: Email triage, draft replies, social post drafts
  * Local: Approvals, WhatsApp session, payments, final send/post
- Vault sync via Git (Phase 1) with claim-by-move rules
- Agent-to-agent communication via vault files
- Security: Cloud never stores WhatsApp sessions, banking creds
- Odoo Community on cloud VM (24/7)
- Health monitoring + watchdog auto-restart

NEXT.JS UI (Portfolio Addition):
- Dashboard showing:
  * Pending approvals from all platforms
  * Real-time task status
  * MCP server health
  * API usage stats
  * Recent activity log
- Features:
  * One-click approve/reject buttons
  * Mobile-responsive (Tailwind CSS)
  * Dark mode
  * Preview draft before approval
  * Authentication (simple auth or skip for MVP)
- Tech Stack: Next.js 14, React, TypeScript, Tailwind

CROSS-PLATFORM NOTIFICATIONS:
- Cloud → WhatsApp alerts when:
  * Urgent email arrives
  * Important task needs approval
  * System errors/issues
- Message format:
  "⚠️ [URGENT] Email from Client A
   AI drafted reply
   Approve: [link to UI]
   Or check vault/"
- Confirmation messages after actions

AGENT SKILLS INTEGRATION:
- Reuse existing skills for Platinum features
- Package Platinum functionality as new skills
- Document skill usage patterns

CONTEXT7 MCP:
- Use for documentation search
- Knowledge retrieval for deployment
- Reference external docs

DELIVERABLES:
1. Complete Platinum spec with all user stories
2. Architecture diagram (Cloud + Local split)
3. Data flow diagrams
4. Security model (secrets partition)
5. Deployment guide
6. UI mockups/wireframes (text description)

Make this production-grade and portfolio-worthy!
Reference Gold tier (specs/002-gold-tier/) for structure.
```

## Response snapshot

Created comprehensive Platinum tier specification (specs/003-platinum-tier/spec.md) with:

**8 User Stories (Prioritized P1-P2):**
1. Cloud Agent Email Triage & Draft Generation (24/7) - P1
2. Next.js Dashboard with One-Click Approvals - P1
3. Cross-Platform Notifications (Cloud → WhatsApp) - P1
4. Vault Sync via Git with Claim-by-Move - P1
5. Work-Zone Specialization (Security Boundaries) - P1
6. Odoo Community 24/7 Cloud Deployment - P2
7. Watchdog Auto-Restart with PM2 - P2
8. Next.js Dashboard API Usage & MCP Health Monitoring - P2

**61 Functional Requirements (FR-P001 through FR-P061):**
- Dual-agent architecture (Cloud + Local)
- Git sync with conflict resolution
- Claim-by-move rules (race condition prevention)
- Next.js Dashboard UI (30 sub-requirements)
- WhatsApp notifications (7 sub-requirements)
- Odoo 24/7 deployment
- PM2 process management
- API usage tracking
- Security partition enforcement
- Backward compatibility with Gold/Silver/Bronze

**Non-Functional Requirements:**
- Performance: Dashboard <2s load, Git sync <10s, WhatsApp notify <60s
- Reliability: 99% Cloud Agent uptime, zero race conditions, auto-recovery
- Security: Secrets partition, no credentials in Git, bcrypt auth
- Usability: Zero-data-migration upgrade, mobile-friendly dashboard

**9 Key Entities:**
CloudAgent, LocalAgent, GitSyncState, DashboardApproval, WhatsAppNotification, MCPServerHealth, APIUsageLog, OdooInstance, PM2Process

**13 Success Criteria:**
Including 99% Cloud uptime, <60s draft availability, <5s dashboard approval flow, zero race conditions, accurate API cost tracking, and full backward compatibility

**Architecture Diagrams (ASCII):**
1. System Architecture (Cloud + Local split with PM2 processes)
2. Data Flow: Urgent Email (15-step Cloud → Local flow)
3. Security Model (Secrets partition across Cloud/Local/Git)

**Dependencies:**
- Inherits all Gold dependencies
- New: GitPython, bcrypt (Python)
- New: Next.js 14, React 18, TypeScript, Tailwind, NextAuth (Node.js)
- Infrastructure: Oracle Cloud VM, Git remote, SSL certs

## Outcome

- ✅ Impact: Production-grade Platinum tier specification ready for planning phase. Portfolio-worthy dual-agent architecture with Next.js dashboard and 24/7 cloud deployment
- 🧪 Tests: Specification phase - no tests yet (planning/implementation phases will add acceptance tests)
- 📁 Files: specs/003-platinum-tier/spec.md (15KB+, 1400+ lines)
- 🔁 Next prompts: /sp.plan 003-platinum-tier (design implementation architecture) or /sp.clarify 003-platinum-tier (resolve unclear requirements)
- 🧠 Reflection: Spec follows Gold tier structure, maintains backward compatibility, prioritizes P1 features (dual-agent, dashboard, notifications) over P2 infrastructure (PM2, Odoo). Security partition is enforced as architectural constraint.

## Evaluation notes (flywheel)

- Failure modes observed: None - spec creation succeeded
- Graders run and results (PASS/FAIL): Spec template validation PASS (all mandatory sections completed)
- Prompt variant (if applicable): Standard /sp.specify workflow
- Next experiment (smallest change to try): Proceed to /sp.plan to validate architecture feasibility
