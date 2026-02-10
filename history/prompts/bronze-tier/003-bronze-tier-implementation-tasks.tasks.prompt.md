---
id: 003
title: Bronze Tier Implementation Tasks
stage: tasks
date: 2026-02-10
surface: agent
model: claude-sonnet-4-5
feature: bronze-tier
branch: bronze-tier
user: ps_qasim
command: /sp.tasks
labels: ["bronze-tier", "tasks", "implementation", "4-phase-plan", "dependency-ordered"]
links:
  spec: specs/bronze-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/bronze-tier/tasks.md
tests:
  - (Tasks define testing strategy - 28 test-related tasks out of 69 total)
---

## Prompt

/sp.tasks

Break down Bronze tier into implementation tasks following the 4-phase plan:

Phase 1: Foundation (init_vault.py, vault_watcher.py, tests)
Phase 2: Monitoring (watch_inbox.py, dashboard_updater.py, integration test)
Phase 3: Validation (handbook validator)
Phase 4: Polish (runbooks, README, performance tests)

Reference specs/bronze-tier/spec.md and specs/bronze-tier/plan.md for requirements.

## Response snapshot

Created comprehensive Bronze Tier task breakdown with 69 dependency-ordered tasks across 4 phases:

**Phase 1: Foundation (T001-T022) - 22 tasks, ~10-12 hours**
- **T001-T005**: Project setup (pyproject.toml, mypy, black, pytest)
- **T006-T010**: Vault initialization script (scripts/init_vault.py)
  - create_folder_structure(), create_dashboard(), create_handbook(), main(), signal handling
- **T011-T015**: Agent Skills API (agent_skills/vault_watcher.py) - 4 functions
  - read_vault_file(), list_vault_folder(), get_dashboard_summary(), validate_handbook()
  - All functions with comprehensive docstrings (Args, Returns, Raises, Example)
- **T016-T022**: Unit tests for vault_watcher.py (80%+ coverage target)
  - Test fixtures (sample vault), tests for all 4 functions, coverage verification, mypy + black checks

**Phase 2: Monitoring (T023-T044) - 22 tasks, ~8-10 hours**
- **T023-T029**: Dashboard updater module (agent_skills/dashboard_updater.py)
  - parse_dashboard(), render_dashboard(), create_backup(), validate_dashboard()
  - update_dashboard() (atomic write algorithm), restore_from_backup(), prune_old_backups()
- **T030-T034**: Unit tests for dashboard_updater.py (80%+ coverage)
  - Corrupted dashboard fixture, parse/render tests, backup/restore tests, atomic update tests
- **T035-T041**: File watcher script (scripts/watch_inbox.py)
  - detect_new_files(), log_event(), poll_inbox(), signal handlers (SIGINT, SIGTERM, SIGHUP)
  - main() entry point, config loading from handbook, heartbeat logging
- **T042-T044**: Integration tests (end-to-end, race conditions, file locks)
  - test_drop_file_detect_update_query (full workflow)
  - test_simultaneous_file_detection (10 files at once)
  - test_file_lock_graceful_degradation (Obsidian lock handling)

**Phase 3: Validation (T045-T052) - 8 tasks, ~4-6 hours**
- **T045-T048**: Handbook validation integration (US4)
  - Integrate validate_handbook() into watcher startup (exit code 2 if fails)
  - Re-validation on SIGHUP, unit tests for edge cases, integration test for invalid handbook
- **T049-T052**: Edge case handling tests
  - Dashboard corruption recovery, dashboard deleted (recreate), invalid UTF-8 encoding
  - 1000-file vault performance test (<30s polling, <2s dashboard update)

**Phase 4: Polish & Documentation (T053-T069) - 17 tasks, ~6-8 hours**
- **T053-T056**: Runbooks (4 failure modes)
  - Watcher won't start, Dashboard not updating, Dashboard corrupted, Watcher keeps restarting
- **T057-T060**: Documentation (README.md, API docs, CONTRIBUTING.md, pdoc HTML docs)
- **T061-T064**: Final validation (full test suite 80%+ coverage, mypy, black, manual E2E test)
- **T065-T067**: Process management (PM2 ecosystem.config.js, systemd service, 24-hour uptime test)
- **T068-T069**: Security audit (no eval/exec, no network, directory traversal protection)

**Total Estimated Time**: 28-36 hours (conservative with buffer)

**Task Statistics**:
- Total tasks: 69
- Parallel tasks: 35 (50% can run in parallel, marked [P])
- Test-related tasks: 28 (unit tests, integration tests, coverage verification)
- User story mapping:
  - US1 (Vault Initialization): 5 tasks (T006-T010)
  - US2 (Inbox Detection): 10 tasks (T035-T041, T042-T044)
  - US3 (Dashboard Updates): 15 tasks (T023-T034, T042-T044)
  - US4 (Handbook Validation): 4 tasks (T045-T048)
  - US5 (Agent Skills API): 12 tasks (T011-T022)
  - Setup & Polish: 23 tasks (T001-T005, T049-T069)

**Key Features**:
- All tasks have exact file paths (e.g., `agent_skills/vault_watcher.py`, `scripts/init_vault.py`)
- Clear acceptance criteria for each task (e.g., "Coverage report shows ≥80%")
- Reference to spec/plan sections (e.g., "Reference: Spec FR-B013, Plan section 3.1")
- Time estimates for each task (5-45 minutes)
- Dependency tracking (Phase 1 blocks 2/3/4, Phase 2 blocks 3/4, Phase 3 blocks 4)

**Parallel Opportunities**:
- **Phase 1**: T001-T005 (setup), T011-T014 (vault_watcher functions), T016-T020 (unit tests) = 14 parallel tasks
- **Phase 2**: T030-T032 (dashboard_updater tests) = 3 parallel tasks
- **Phase 4**: T053-T056 (runbooks), T058-T060 (docs), T065-T066 (process mgmt), T068-T069 (security) = 11 parallel tasks

**Execution Strategy** (recommended):
1. **Single Developer (Sequential)**: Complete phases 1→2→3→4 in order
2. **Two Developers (Parallel)**:
   - Dev A: Phase 1 foundation (T001-T022)
   - Dev B: Wait for Phase 1 → Phase 2 monitoring (T023-T044)
   - Both: Split Phase 3 validation and Phase 4 polish tasks

**Constitution Compliance**:
- Git commit messages must reference spec sections (e.g., "Implements US-1: Vault initialization (spec: bronze-tier/spec.md#US-1)")
- 80% test coverage is non-negotiable (constitution requirement)
- Mypy and black checks are quality gates (must pass before PR merge)
- Feature branch: bronze-tier (already created and active)

**Checkpoints** (validate independently at each phase):
- **Phase 1 Checkpoint**: Vault initialization and Agent Skills API complete and tested (US1, US5 functional)
- **Phase 2 Checkpoint**: File watching, dashboard updates, integration tests complete (US2, US3 functional)
- **Phase 3 Checkpoint**: Handbook validation and edge cases handled (US4 functional)
- **Phase 4 Checkpoint**: Production-ready (runbooks, docs, 24-hour uptime test passed)

**Definition of Done** (all 10 criteria from spec):
1. All 5 user stories pass acceptance tests
2. All 25 FRs and 18 NFRs implemented and verified
3. Pytest achieves 80%+ coverage for agent_skills/
4. Integration test passes (drop file → detect → update → query)
5. Performance tests pass (<2s updates, <500ms reads, 1000-file support)
6. Code passes mypy + black checks
7. All 8 edge cases handled gracefully
8. Runbooks created for 4 common failures
9. User can run system without developer assistance (README.md)
10. 24-hour continuous operation at 99% uptime

## Outcome

- ✅ Impact: Created actionable task breakdown for Bronze Tier with 69 dependency-ordered tasks across 4 phases, enabling systematic implementation of all 5 user stories (US1-US5) with clear checkpoints and parallel execution opportunities
- 🧪 Tests: Task list includes 28 test-related tasks (unit tests for vault_watcher.py and dashboard_updater.py, integration tests for end-to-end flow, performance tests for 1000-file vault, security audit)
- 📁 Files: Created `specs/bronze-tier/tasks.md` (comprehensive task list with 69 tasks, each with exact file paths, acceptance criteria, time estimates, and spec/plan references)
- 🔁 Next prompts:
  - Start Phase 1: Execute T001-T005 (project setup) in parallel
  - After T005: Execute T006-T010 (init_vault.py) + T011-T015 (vault_watcher.py) + T016-T020 (unit tests) in parallel
  - After Phase 1 checkpoint: Review progress and proceed to Phase 2
  - Create GitHub issues from tasks: `/sp.taskstoissues bronze-tier` (optional, if tracking in GitHub)
- 🧠 Reflection: Task breakdown successfully balances granularity (69 tasks = ~30 min average per task) with clarity (exact file paths, function signatures, acceptance criteria). Parallel opportunities identified (35 tasks marked [P]) enable efficient execution by multiple developers or CI/CD parallelization. Phase-based organization aligns with 4-phase plan from implementation plan, ensuring systematic progress with validation checkpoints.

## Evaluation notes (flywheel)

- Failure modes observed: None (task generation successful)
- Graders run and results (PASS/FAIL): Task list follows template structure, all tasks reference spec/plan sections, acceptance criteria are testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Execute Phase 1 Foundation tasks (T001-T022), starting with T001-T005 project setup in parallel, then validate checkpoint before proceeding to Phase 2
