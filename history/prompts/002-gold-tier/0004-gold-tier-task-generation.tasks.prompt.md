---
id: "0004"
title: Gold Tier Task Generation
stage: tasks
date: 2026-02-13
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-gold-tier
branch: 002-gold-tier
user: ps_qasim
command: /sp.tasks 002-gold-tier
labels: ["tasks", "gold-tier", "task-generation", "implementation-plan", "user-stories", "mcp-servers", "ralph-wiggum-loop", "playwright", "whatsapp"]
links:
  spec: specs/002-gold-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-gold-tier/tasks.md
  - history/prompts/002-gold-tier/0004-gold-tier-task-generation.tasks.prompt.md
tests:
  - none (task generation phase, implementation tasks defined in tasks.md)
---

## Prompt

/sp.tasks 002-gold-tier

## Response snapshot

Generated comprehensive implementation tasks for Gold Tier with 84 dependency-ordered tasks organized by 7 user stories:

**Task Organization**:
- Phase 1: Setup (4 tasks) - Vault structure, dependencies, .env template, docs structure
- Phase 2: Foundational (6 tasks) - mcp_client.py, draft_generator.py, approval_watcher.py, plan_executor.py (Ralph Wiggum loop) - BLOCKS all user stories
- Phase 3: US1 - Email Draft & Send (P1, 7 tasks) - email_mcp, gmail_watcher extension, approval handler
- Phase 4: US2 - LinkedIn Post & Publish (P1, 8 tasks) - linkedin_mcp, post generator, approval handler
- Phase 5: US3 - WhatsApp Draft & Send (P1, 10 tasks) - whatsapp_mcp with Playwright, message watcher, QR auth setup
- Phase 6: US4 - Multi-Step Plan Execution (P1, 10 tasks) - Plan generator, Ralph Wiggum loop, plan_watcher, dashboard integration
- Phase 7: US5 - MCP Multi-Server Integration (P2, 6 tasks) - Health checks, action logging, safety gates
- Phase 8: US6 - CEO Briefing (P2, 4 tasks) - Weekly briefing generator, scheduling, proactive suggestions
- Phase 9: US7 - Odoo Accounting (P3, 7 tasks) - odoo_mcp, draft generator, domain routing (optional)
- Phase 10: Polish (22 tasks) - Documentation, watcher orchestration, error recovery, integration tests, safety validation

**Key Architectural Decisions**:
- Foundational phase (T005-T010) BLOCKS all user stories - must complete first
- User Stories 1-3 (P1) are independent and can run in parallel after Foundational
- User Story 4 (Multi-Step Plans) depends on US1-US3 for MCP actions in plan steps
- MVP scope: Phases 1+2+3+4+5 (30 tasks) = Email + LinkedIn + WhatsApp draft-and-send
- Full Gold: All 84 tasks = All 7 user stories + Ralph Wiggum loop + CEO Briefing + Odoo

**Task Format**:
- All tasks follow strict checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- 20+ tasks marked [P] for parallel execution (different files, no dependencies)
- Each user story has independent test criteria for validation
- Clear file paths for every task (agent_skills/, scripts/, mcp_servers/, vault/, docs/gold/)

**Dependency Graph**:
- Setup → Foundational → User Stories (parallel) → Polish
- Within each user story: MCP servers → Watchers/Generators → Approval Handlers → Validation
- User Story 4 should start after US1/US2/US3 complete (needs MCP actions available)

**Parallel Opportunities**:
- Setup phase: All 4 tasks can run in parallel
- Foundational phase: T006, T007, T008 can run in parallel (different files)
- User Stories: US1, US2, US3, US5, US6 can all start in parallel after Foundational
- Integration tests (Phase 10): All 5 tests (T075-T079) can run in parallel

## Outcome

- ✅ Impact: Complete implementation roadmap with 84 tasks organized by user story. MVP path clear (30 tasks for Email + LinkedIn + WhatsApp). Full Gold tier achievable with all 84 tasks. Each user story independently testable. Ready for `/sp.implement 002-gold-tier` or manual implementation.
- 🧪 Tests: Integration tests defined in Phase 10 (T075-T079): email_workflow, whatsapp_workflow, linkedin_workflow, plan_execution, ceo_briefing. No unit tests requested per spec (tests optional).
- 📁 Files: tasks.md (84 tasks), PHR
- 🔁 Next prompts: `/sp.implement 002-gold-tier` to begin automated implementation starting with Phase 1 Setup, or manual implementation following task order
- 🧠 Reflection: Task organization by user story enables incremental delivery. Foundational phase (6 tasks) is critical blocker for all stories. WhatsApp integration (US3) is most complex (10 tasks) due to Playwright automation and session management. Ralph Wiggum loop (US4) is Gold tier differentiator. MVP scope (30 tasks) delivers immediate value before full Gold tier.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Task format validation PASS (all tasks follow checklist format with ID, file paths, story labels), dependency graph validated PASS (Foundational blocks user stories, no circular dependencies)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Begin implementation with Phase 1 Setup (T001-T004), validate vault structure creation before proceeding to Foundational phase
