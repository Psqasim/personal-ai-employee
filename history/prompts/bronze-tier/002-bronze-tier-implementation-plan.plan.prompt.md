---
id: 002
title: Bronze Tier Implementation Plan
stage: plan
date: 2026-02-10
surface: agent
model: claude-sonnet-4-5
feature: bronze-tier
branch: main
user: ps_qasim
command: /sp.plan
labels: ["bronze-tier", "implementation-plan", "architecture", "polling-watcher", "atomic-writes", "agent-skills"]
links:
  spec: specs/bronze-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/bronze-tier/plan.md
tests:
  - (None - planning artifact, tests defined within plan)
---

## Prompt

/sp.plan

Create Bronze tier implementation plan using these technologies:

TECH STACK
- Python 3.11+ with watchdog, pyyaml
- Pure Python agent_skills/ modules (no external APIs)
- scripts/watch_inbox.py for continuous monitoring
- Obsidian 1.11.7 with standard markdown

ARCHITECTURE
File Watcher → Dashboard Updater → Agent Skills API

Key components:
1. scripts/watch_inbox.py - Polls vault/Inbox/ every 30s
2. agent_skills/dashboard_updater.py - Updates Dashboard.md atomically
3. agent_skills/vault_watcher.py - 4 functions for Claude Code queries
4. scripts/init_vault.py - One-time vault setup

ERROR HANDLING
- Obsidian file lock → Retry next cycle
- Dashboard corruption → Restore from .bak
- Missing handbook → Exit with error message

TESTING
- pytest unit tests for each agent skill
- Integration test: Drop file → Detect → Update → Query
- Target: 80%+ coverage

Reference specs/bronze-tier/spec.md for all requirements.

## Response snapshot

Created comprehensive Bronze Tier implementation plan following architect guidelines:

**1. Scope and Dependencies**:
- **In Scope**: Vault initialization (5 folders, 2 templates), file watcher (30s polling), Dashboard.md updates (atomic writes with backups), Agent Skills API (4 functions), handbook validation
- **Out of Scope**: AI analysis (Silver), auto file movement (Silver), external APIs (Gold), reflection loops (Platinum)
- **Dependencies**: watchdog>=3.0.0, pyyaml>=6.0, pytest>=7.0, black, mypy, Obsidian 1.5+
- **Ownership**: All dependencies external (PyPI, user-installed), low risk (stable libraries, pinned versions)

**2. Key Decisions and Rationale**:
- **Decision 1: Polling (30s) vs. Real-Time Events** → Chose polling for simplicity, lower CPU, predictable behavior (30s delay acceptable for Bronze). Reversible in Silver tier.
- **Decision 2: Atomic Writes with Backups** → Chose atomic rename + timestamped backups for data integrity (constitution Principle II). Non-negotiable safety requirement.
- **Decision 3: Pure Functions vs. Stateful Class** → Chose pure functions for simpler testing, explicit dependencies, natural Claude Code integration. Reversible in Silver tier.
- **Decision 4: Graceful Degradation vs. Fail-Fast** → Chose graceful degradation (log error, continue) for 99% uptime target. Immediate retry on next 30s cycle.
- **Decision 5: Startup-Only Validation** → Chose startup validation (not continuous) for Bronze simplicity. User restarts watcher if handbook changed. Reversible in Silver tier.

**3. Interfaces and API Contracts**:
- **Agent Skills API (vault_watcher.py)**: 4 pure functions with type hints, docstrings (Args/Returns/Raises/Example)
  - `read_vault_file(vault_path, filepath) -> str` - Read markdown file (<500ms for 100KB files)
  - `list_vault_folder(vault_path, folder_name) -> list[str]` - List .md files in folder (<100ms for 1000 files)
  - `get_dashboard_summary(vault_path) -> dict[str, int]` - Parse Dashboard.md → task counts (<200ms)
  - `validate_handbook(vault_path) -> tuple[bool, list[str]]` - Check 5 required sections
- **Dashboard Updater (dashboard_updater.py)**:
  - `update_dashboard(vault_path, new_files) -> bool` - Atomic update with backup (<2s)
  - `restore_from_backup(vault_path, backup_filename=None) -> bool` - Restore from .bak
- **Watcher Entry Point (scripts/watch_inbox.py)**:
  - `main(vault_path, config=None) -> None` - Polling loop, signal handling (SIGINT, SIGTERM, SIGHUP)
- **Vault Initialization (scripts/init_vault.py)**:
  - `main(vault_path, overwrite=False) -> None` - Create 5 folders + 2 templates
- **Logging Format (vault/Logs/watcher-YYYY-MM-DD.md)**: Human-readable markdown with timestamps, event types, file lists

**4. Non-Functional Requirements and Budgets**:
- **Performance**: Dashboard update <2s, file read <500ms, polling cycle 30s, vault scan <5s (1000 files), memory <100MB, CPU <5%
- **Reliability**: Watcher uptime 99% (24h), dashboard integrity 100%, idempotency 100%, error recovery <30s
- **Security**: Zero network requests, filesystem limited to vault/, no code execution, read-only except Dashboard.md and Logs/
- **Cost**: $0 (no API costs, 100% offline)

**5. Data Management and Migration**:
- **Dashboard.md Schema**: Markdown table [Filename, Date Added, Status, Priority] + Statistics section + Last Updated timestamp
- **Company_Handbook.md Schema**: YAML frontmatter (version, tier, last_updated) + 5 required sections
- **Backup Retention**: Keep last 5 backups per day (delete older), prune logs after 7 days
- **Source of Truth**: Vault filesystem (Inbox/, Needs_Action/, Done/), Dashboard.md is derived view
- **Migration Strategy**: No migration needed for Bronze v0.1.0 (stable format), migration script template provided for future versions

**6. Operational Readiness**:
- **Observability**: Human-readable logs (vault/Logs/watcher-YYYY-MM-DD.md), INFO level default, 6 event types (watcher_started, file_detected, dashboard_updated, error, etc.)
- **Alerting**: Passive (user reads logs), WARNING for performance degradation, ERROR for corruption/crashes
- **Runbooks**: 4 runbooks (watcher won't start, dashboard not updating, dashboard corrupted, watcher keeps restarting)
- **Deployment**: Local-only (pip install, init vault, start watcher), process management (PM2 or systemd), rollback = revert code version

**7. Risk Analysis and Mitigation**:
- **Risk 1: Dashboard Corruption on Power Loss** → Atomic writes + backups + corruption detection (risk: Medium/High, mitigation: 3-layer defense)
- **Risk 2: File Lock Conflicts with Obsidian** → Graceful degradation + retry next cycle + user guidance (risk: High/Medium, acceptable 30s delay)
- **Risk 3: Vault Size >1000 Files** → Performance warning + graceful degradation + cleanup strategy (risk: Low/Medium, Bronze limit enforced)

**8. Evaluation and Validation**:
- **Definition of Done**: 10-point checklist (functional completeness, testing, code quality, documentation, operational readiness, user validation)
- **Output Validation**: Dashboard.md validation (markdown table, wiki links, status values), handbook validation (5 sections, valid YAML)
- **Acceptance Tests**: Integration test (drop file → detect → update → query) with 35s timeout
- **Safety Audit**: Security checks (no eval/exec, no shell injection, path validation, zero network), data integrity checks (atomic writes, backups, corruption recovery, race conditions), Obsidian compatibility checks

**9. Architecture Decision Records (ADRs)**:
- **ADR Suggestion 1**: Polling vs. Real-Time Monitoring → `/sp.adr polling-vs-realtime-monitoring`
- **ADR Suggestion 2**: Atomic Dashboard Updates → `/sp.adr atomic-dashboard-updates`
- **ADR Suggestion 3**: Agent Skills API Design → `/sp.adr agent-skills-api-design`

**Constitution Alignment**:
- ✅ Vault Integrity First (Principle II): Atomic writes, backups, corruption recovery
- ✅ Local-First Architecture (Principle III): 100% offline, no external APIs
- ✅ Test-Driven Safety (Principle IV): 80% coverage, integration tests, idempotency tests
- ✅ Incremental Development (Principle V): Bronze is foundation, no Silver/Gold features
- ✅ Code Organization (Principle VI): agent_skills/, scripts/, tests/, vault/ separation
- ✅ Performance Requirements: <2s dashboard updates, 99% uptime, 1000-file support

**Project Structure**:
- agent_skills/__init__.py, vault_watcher.py (4 functions), dashboard_updater.py (atomic updates)
- scripts/init_vault.py (setup), watch_inbox.py (polling loop)
- tests/unit/ (vault_watcher, dashboard_updater), integration/ (end-to-end), fixtures/ (sample vault, corrupted dashboard)
- vault/Inbox/, Needs_Action/, Done/, Plans/, Logs/, Dashboard.md, Company_Handbook.md

**Implementation Sequence** (Recommended):
- Phase 1 (Foundation): init_vault.py → vault_watcher.py + tests → dashboard_updater.py + tests
- Phase 2 (Monitoring): watch_inbox.py → integration test → 1000-file performance test
- Phase 3 (Validation): handbook validation + tests
- Phase 4 (Polish): runbooks → README.md → full test suite → process management

**Next Steps**: Review plan → Run `/sp.tasks bronze-tier` → Setup dev environment → Implement Phase 1

## Outcome

- ✅ Impact: Comprehensive implementation plan created with detailed architecture (5 key decisions with rationale), API contracts (4 Agent Skills + dashboard updater + watcher), NFRs (performance/reliability/security budgets), risk analysis (top 3 risks with mitigation), and operational readiness (observability, alerting, runbooks, deployment)
- 🧪 Tests: Plan defines testing strategy (80% coverage for agent_skills/, integration test for end-to-end flow, performance tests for 1000-file vault, idempotency tests, safety audit checklist)
- 📁 Files: Created `specs/bronze-tier/plan.md` (comprehensive architecture document with 9 sections following architect guidelines)
- 🔁 Next prompts:
  - `/sp.tasks bronze-tier` - Generate dependency-ordered implementation tasks
  - `/sp.adr polling-vs-realtime-monitoring` - Document polling decision (optional)
  - `/sp.adr atomic-dashboard-updates` - Document atomic write strategy (optional)
  - `/sp.adr agent-skills-api-design` - Document pure functions vs. classes (optional)
  - Review plan with stakeholders before proceeding to tasks phase
- 🧠 Reflection: Plan successfully balances technical detail (API signatures with type hints, atomic write algorithm, error taxonomy) with strategic decisions (polling vs. events, pure functions vs. classes). All 5 key decisions are measurable, reversible (except atomic writes = safety requirement), and aligned with smallest viable change principle. Ready for task generation phase.

## Evaluation notes (flywheel)

- Failure modes observed: None (planning phase successful)
- Graders run and results (PASS/FAIL): Constitution check passed (all principles satisfied), complexity tracking shows zero violations, ADR detection identified 3 significant decisions
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to `/sp.tasks bronze-tier` to generate implementation tasks, starting with Phase 1 (Foundation) - implement init_vault.py, vault_watcher.py, dashboard_updater.py with unit tests before moving to Phase 2 (Monitoring)
