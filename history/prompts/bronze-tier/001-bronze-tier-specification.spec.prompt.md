---
id: 001
title: Bronze Tier Specification
stage: spec
date: 2026-02-10
surface: agent
model: claude-sonnet-4-5
feature: bronze-tier
branch: main
user: ps_qasim
command: /sp.specify
labels: ["bronze-tier", "specification", "vault-monitoring", "obsidian", "local-first", "foundation"]
links:
  spec: specs/bronze-tier/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/bronze-tier/spec.md
tests:
  - (None - specification artifact, tests defined within spec)
---

## Prompt

/sp.specify

Create the Bronze Tier specification for Personal AI Employee system. Reference the Hackathon 0 requirements document already in this project.

BRONZE TIER SCOPE
Build a local-first AI employee that monitors an Obsidian vault and provides basic task awareness. This is the foundation tier - 100% offline, manual human review required for all actions.

USER STORIES

US-B1: Vault Structure Setup
As a user, I want a pre-configured Obsidian vault with organized folders so I can immediately start dropping tasks and notes into the system.

Acceptance Criteria:
- Vault contains 5 folders: Inbox/, Needs_Action/, Done/, Plans/, Logs/
- Dashboard.md exists at vault root with empty task table
- Company_Handbook.md exists with placeholder rules
- All folders are empty initially (ready for user content)
- Vault opens successfully in Obsidian 1.5+

US-B2: Inbox Monitoring
As a user, I want a background watcher that detects new files in Inbox/ so I don't have to manually update the dashboard.

Acceptance Criteria:
- Python script runs continuously (polling every 30 seconds)
- Detects .md files added to vault/Inbox/
- Logs detection events to vault/Logs/watcher-YYYY-MM-DD.md
- Triggers Dashboard.md update when new file detected
- Handles race conditions (multiple files added simultaneously)
- Gracefully handles Obsidian vault being locked

US-B3: Automatic Dashboard Updates
As a user, I want Dashboard.md to show all pending tasks from Inbox/ so I have a quick overview without opening multiple files.

Acceptance Criteria:
- Dashboard.md contains markdown table with columns: [Filename, Date Added, Status, Priority]
- Status values: "Inbox", "Needs Action", "Done"
- Priority defaults to "Medium" for Bronze tier (no AI analysis yet)
- Table updates within 2 seconds of file detection
- Preserves existing Dashboard.md content (adds tasks, doesn't overwrite)
- Creates .bak backup before each update

US-B4: Company Handbook Configuration
As a user, I want Company_Handbook.md to define basic operational rules so the agent knows how to categorize and process tasks.

Acceptance Criteria:
- Defines file naming convention (e.g., YYYY-MM-DD-task-name.md)
- Specifies which files should go in Inbox vs Needs_Action
- Lists forbidden file operations (no auto-delete, no auto-move in Bronze)
- Defines escalation rules (when to notify human)
- Includes Bronze tier limitations section (no AI analysis, no autonomous actions)

US-B5: Claude Code Vault Access
As a developer, I want Agent Skills that allow Claude Code to read vault contents so I can query the system via chat.

Acceptance Criteria:
- agent_skills/vault_watcher.py module with functions:
  - read_vault_file(filepath) → Returns markdown content
  - list_vault_folder(folder_name) → Returns list of files
  - get_dashboard_summary() → Returns task counts by status
  - validate_handbook() → Checks Company_Handbook.md has required sections
- All functions have pytest unit tests
- Functions are importable by Claude Code
- No external API calls (100% local filesystem operations)

[Additional functional requirements, non-functional requirements, dependencies, and success criteria provided in detail...]

## Response snapshot

Created comprehensive Bronze Tier specification following Spec-Driven Development template:

**Specification Structure:**

1. **5 Prioritized User Stories** (P1, P2) with Given-When-Then acceptance scenarios:
   - US-1 (P1): Vault Structure Initialization - 5 acceptance tests
   - US-2 (P1): Inbox File Detection - 5 acceptance tests
   - US-3 (P1): Automatic Dashboard Updates - 6 acceptance tests
   - US-4 (P2): Company Handbook Validation - 4 acceptance tests
   - US-5 (P2): Claude Code Vault Querying - 5 acceptance tests

2. **25 Functional Requirements** (FR-B001 through FR-B025):
   - Vault initialization and folder structure
   - File watcher polling and detection logic
   - Dashboard.md update mechanics with atomic writes
   - Backup strategy (Dashboard.md.bak with timestamp)
   - Agent Skills API with type-hinted functions
   - Error handling (file locks, corruption, race conditions)
   - 100% offline operation (no network requests)

3. **18 Non-Functional Requirements** across 5 categories:
   - Performance: <2s dashboard updates, <500ms file reads, 1000-file support
   - Reliability: 99% uptime, idempotent operations, automatic corruption recovery
   - Compatibility: Obsidian 1.5+, Python 3.11+, WSL Ubuntu/macOS/Windows
   - Security: 100% offline, read-only except Dashboard.md, no code execution
   - Usability: Single-command setup, human-readable logs, actionable error messages

4. **5 Key Entities**:
   - VaultFile (filename, date_added, status, priority)
   - VaultFolder (name, file_count)
   - Dashboard (task_table, statistics, last_updated)
   - Handbook (configuration sections)
   - WatcherLog (timestamp, event_type, message)

5. **12 Success Criteria** (measurable outcomes):
   - SC-B001: Vault initialization in <30 seconds
   - SC-B002: File detection within 30 seconds
   - SC-B003: Dashboard update within 2 seconds
   - SC-B004: Process 10 simultaneous files without errors
   - SC-B005: 24-hour continuous operation at 99% uptime
   - SC-B006: Claude Code can query vault via Agent Skills
   - SC-B007: Handbook validation detects missing sections
   - SC-B008: Automatic recovery from Dashboard corruption
   - SC-B009: Zero network traffic (verified with monitoring)
   - SC-B010: 80%+ test coverage for Agent Skills
   - SC-B011: 1000-file vault performance target met
   - SC-B012: Obsidian renders Dashboard.md without errors

6. **8 Edge Cases** handled:
   - Obsidian file locks → Retry on next cycle
   - Dashboard.md deleted → Recreate from current state
   - Duplicate filenames in different folders → Show full paths
   - 10,000+ files → Performance warning, continue operation
   - Invalid UTF-8 encoding → Log error, continue with other files
   - System clock changes → Timestamps with timezone info
   - Manual Dashboard.md edits → .bak preserves user version
   - Power loss mid-update → Restore from .bak on next startup

7. **Dependencies Specified**:
   - Python packages: watchdog>=3.0.0, pyyaml>=6.0
   - Dev tools: pytest>=7.0, black, mypy
   - External: Obsidian 1.5+, Python 3.11+
   - System: 8GB RAM, 1GB disk, 4-core CPU

8. **Out of Scope** (deferred to Silver/Gold/Platinum):
   - AI-powered priority analysis (Silver)
   - Automatic file movement (Silver)
   - Plan.md generation (Silver)
   - Multi-step execution (Gold)
   - External API integrations (Gold)
   - Reflection loops (Platinum)
   - Cloud deployment (Platinum)

9. **Reference Formats** (Appendices):
   - Dashboard.md markdown table format
   - Company_Handbook.md structure with 5 required sections
   - Agent Skills API usage examples

10. **Definition of Done**:
    - All 5 user stories passing acceptance tests
    - All 25 FRs and 18 NFRs implemented and verified
    - All 12 success criteria met
    - 80%+ test coverage
    - Integration test passes end-to-end
    - Mypy and black checks pass
    - User can run system without developer assistance

**Alignment with Constitution:**
- Vault Integrity First: Atomic writes, backups, corruption recovery
- Local-First Architecture: 100% offline operation
- Test-Driven Safety: 80% coverage requirement, measurable success criteria
- Incremental Development: Bronze is foundation, Silver/Gold/Platinum deferred
- Code Organization: agent_skills/, scripts/, vault/ separation enforced
- Performance Requirements: Measurable targets (<2s updates, 99% uptime)

## Outcome

- ✅ Impact: Comprehensive Bronze Tier specification created with 5 prioritized user stories, 25 functional requirements, 18 non-functional requirements, 12 measurable success criteria, and clear scope boundaries (no AI analysis, no autonomous actions, 100% offline)
- 🧪 Tests: Specification defines testing strategy (80% coverage for Agent Skills, integration test for end-to-end flow, idempotency tests, edge case handling)
- 📁 Files: Created `specs/bronze-tier/spec.md` (comprehensive specification with appendices for reference formats)
- 🔁 Next prompts:
  - `/sp.plan bronze-tier` - Design implementation architecture (file watcher design, dashboard update algorithm, Agent Skills module structure)
  - `/sp.clarify bronze-tier` - Identify underspecified areas (if any questions arise during plan phase)
  - Review Hackathon document for Bronze tier implementation examples
- 🧠 Reflection: Specification successfully balances detail (measurable requirements) with clarity (Given-When-Then scenarios). Edge cases are explicitly handled to prevent "unknown unknowns" during implementation. Out-of-scope items clearly documented to prevent feature creep. Ready for planning phase.

## Evaluation notes (flywheel)

- Failure modes observed: None (specification creation successful)
- Graders run and results (PASS/FAIL): All validation checklist items passed (user stories prioritized, requirements measurable, API signatures with type hints, success criteria testable)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to `/sp.plan bronze-tier` to design file watcher architecture, dashboard update algorithm, and Agent Skills module structure following constitution's incremental development principle
