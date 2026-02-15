---
id: "0003"
title: Gold Tier Implementation Plan
stage: plan
date: 2026-02-13
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-gold-tier
branch: 002-gold-tier
user: ps_qasim
command: /sp.plan
labels: ["plan","gold-tier","playwright","mcp","ralph-wiggum-loop","email-draft","whatsapp-draft","linkedin-post"]
links:
  spec: specs/002-gold-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-gold-tier/plan.md
  - specs/002-gold-tier/research.md
  - specs/002-gold-tier/data-model.md
  - specs/002-gold-tier/contracts/email-mcp.md
  - specs/002-gold-tier/contracts/whatsapp-mcp.md
  - specs/002-gold-tier/contracts/linkedin-mcp.md
  - specs/002-gold-tier/contracts/mcp-protocol.md
  - specs/002-gold-tier/quickstart.md
  - history/prompts/002-gold-tier/0003-gold-tier-implementation-plan.plan.prompt.md
tests:
  - none (plan phase, implementation tasks defined in plan.md)
---

## Prompt

002-gold-tier

## Response snapshot

Generated comprehensive implementation plan for Gold Tier with Phase 0 (Research) and Phase 1 (Design & Contracts) complete:

**plan.md** (Main Implementation Plan):
- Technical Context: Python 3.11+, Playwright, MCP servers (email, whatsapp, linkedin), Ralph Wiggum loop (max 10 iterations)
- Constitution Check: All gates pass ✅ (Tier Progression, Vault Integrity, Local-First, Agent Skills, Test-Driven, Audit Logging)
- Project Structure: agent_skills/, scripts/, mcp_servers/, vault/ (with Gold extensions: Pending_Approval/, Approved/, In_Progress/, Briefings/)
- Complexity Justification: Playwright for WhatsApp (no official API), 3 MCP servers (isolated permissions), Ralph Wiggum loop (autonomous multi-step)
- Risks & Mitigation: WhatsApp UI changes, MCP crashes, loop iterations, race conditions, API costs, vault corruption

**research.md** (Phase 0 - Technical Discovery):
- Playwright WhatsApp automation patterns with session persistence (QR auth once, headless sends)
- MCP server architecture (JSON-RPC 2.0 over stdin/stdout, isolated processes)
- Ralph Wiggum loop pattern (async, max 10 iterations, state persistence in vault/In_Progress/)
- Email/WhatsApp/LinkedIn draft generation prompts with Claude API
- File-based approval workflow (watchdog + filelock for race condition safety)

**data-model.md** (Phase 1 - Entities):
- 8 entities: EmailDraft, WhatsAppDraft, LinkedInDraft, Plan, PlanStep, ExecutionState, MCPActionLog, CEOBriefing
- All file-based (YAML frontmatter + markdown body) for local-first architecture
- State transitions documented (pending_approval → approved → sent/posted/executed)
- Validation rules (character limits, email formats, dependency checks)

**contracts/** (Phase 1 - MCP Server Interfaces):
- email-mcp.md: send_email tool (SMTP via smtplib)
- whatsapp-mcp.md: authenticate_qr, send_message tools (Playwright automation)
- linkedin-mcp.md: create_post tool (LinkedIn API v2 OAuth2)
- mcp-protocol.md: JSON-RPC 2.0 patterns, error codes, server template

**quickstart.md** (Phase 1 - Setup Guide):
- Step-by-step upgrade from Silver → Gold (10 steps)
- Gmail app password setup, LinkedIn OAuth2 token, WhatsApp QR auth
- MCP server configuration in ~/.config/claude-code/mcp.json
- Vault folder initialization (Pending_Approval/, Approved/, etc.)
- 4 end-to-end tests (email, whatsapp, linkedin, multi-step plan)
- Troubleshooting guide for common issues

## Outcome

- ✅ Impact: Complete implementation plan with all technical decisions made. Gold tier architecture defined with Playwright automation, 3 MCP servers, Ralph Wiggum loop, and file-based approval workflow. Ready for task breakdown and implementation.
- 🧪 Tests: Integration tests defined in quickstart.md (email draft→send, whatsapp draft→send, linkedin draft→post, multi-step plan execution)
- 📁 Files: plan.md, research.md, data-model.md, contracts/ (4 files), quickstart.md
- 🔁 Next prompts: `/sp.tasks 002-gold-tier` to generate dependency-ordered implementation tasks
- 🧠 Reflection: Gold tier plan is extensive (7 deliverable files) due to complexity: 3 MCP servers + WhatsApp Playwright automation + Ralph Wiggum loop + weekly CEO Briefing. All constitution checks pass. Backward compatibility with Bronze+Silver guaranteed.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Constitution Check PASS (all gates), project structure validated
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run /sp.tasks to decompose plan into 50+ implementation tasks, verify task ordering handles MCP server dependencies correctly
