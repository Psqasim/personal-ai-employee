# Feature Specification: Bronze Tier - Foundation AI Employee

**Feature Branch**: `bronze-tier`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "Create the Bronze Tier specification for Personal AI Employee system. Reference the Hackathon 0 requirements document already in this project. BRONZE TIER SCOPE: Build a local-first AI employee that monitors an Obsidian vault and provides basic task awareness. This is the foundation tier - 100% offline, manual human review required for all actions."

## Overview

Bronze Tier establishes the foundational layer of the Personal AI Employee system. This tier focuses on **monitoring and awareness** without autonomous actions. The agent operates 100% offline, monitoring an Obsidian vault for new tasks and maintaining an up-to-date dashboard. All actions require explicit human approval.

**Core Principle**: Vault Integrity First - Never corrupt user data. All operations are read-heavy with minimal, atomic writes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vault Structure Initialization (Priority: P1)

As a **user setting up the AI Employee for the first time**, I want a pre-configured Obsidian vault with organized folders so I can immediately start dropping tasks and notes into the system without manual setup.

**Why this priority**: This is the foundation. Without a properly structured vault, no other features can function. This delivers immediate value by providing a clear organizational system.

**Independent Test**: Can be fully tested by initializing the vault and opening it in Obsidian. Success means all folders exist, Dashboard.md is readable, and Company_Handbook.md contains valid configuration.

**Acceptance Scenarios**:

1. **Given** I have Python 3.11+ and Obsidian 1.5+ installed, **When** I run the vault initialization script, **Then** a vault directory is created with 5 folders (Inbox/, Needs_Action/, Done/, Plans/, Logs/)

2. **Given** the vault has been initialized, **When** I open the vault in Obsidian, **Then** Dashboard.md displays an empty task table with proper markdown formatting

3. **Given** the vault has been initialized, **When** I read Company_Handbook.md, **Then** it contains all 5 required sections (File Naming Convention, Folder Usage Guidelines, Forbidden Operations, Escalation Rules, Bronze Tier Limitations)

4. **Given** the vault structure exists, **When** I check folder permissions, **Then** all folders are readable and writable by the Python watcher process

5. **Given** the vault is open in Obsidian, **When** I create a test file in Inbox/, **Then** Obsidian does not lock the file from being read by Python scripts

---

### User Story 2 - Inbox File Detection (Priority: P1)

As a **user working with tasks**, I want a background watcher that automatically detects new markdown files in Inbox/ so I don't have to manually notify the system about new work.

**Why this priority**: Automatic detection is the core value proposition of Bronze tier. Without this, the system is just a static folder structure with no intelligence.

**Independent Test**: Start the watcher, drop a test file into Inbox/, and verify detection is logged within 30 seconds. This can be tested independently of dashboard updates.

**Acceptance Scenarios**:

1. **Given** the file watcher is running, **When** I create a new .md file in vault/Inbox/, **Then** the watcher logs the detection event to vault/Logs/watcher-YYYY-MM-DD.md within 30 seconds

2. **Given** the file watcher is running, **When** I add 5 files to Inbox/ simultaneously, **Then** all 5 files are detected and logged without race conditions or dropped events

3. **Given** the file watcher is running, **When** I create a non-.md file (e.g., image.png) in Inbox/, **Then** the watcher ignores it and does not log the event

4. **Given** the file watcher is running and Obsidian has a file locked, **When** the watcher attempts to read the locked file, **Then** it logs a warning and continues monitoring (doesn't crash)

5. **Given** the file watcher encounters a network timeout (simulated), **When** the error occurs, **Then** the watcher logs the error and retries on the next polling cycle (doesn't exit)

---

### User Story 3 - Automatic Dashboard Updates (Priority: P1)

As a **user managing multiple tasks**, I want Dashboard.md to automatically show all pending tasks from Inbox/ in a structured table so I have a quick overview without opening individual files.

**Why this priority**: The dashboard is the user's primary interface to understand system state. Without automatic updates, users lose trust in the system's accuracy.

**Independent Test**: With the watcher running, add a file to Inbox/ and verify Dashboard.md updates with the new task entry within 2 seconds. Check that the markdown table is valid and renders correctly in Obsidian.

**Acceptance Scenarios**:

1. **Given** a new file is detected in Inbox/, **When** the dashboard update process runs, **Then** Dashboard.md contains a new table row with [Filename, Date Added, Status="Inbox", Priority="Medium"]

2. **Given** Dashboard.md has existing content, **When** a new task is added, **Then** the existing content is preserved and the new task is appended to the table (not overwritten)

3. **Given** a dashboard update is about to occur, **When** the update process starts, **Then** a backup file Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS is created before modification

4. **Given** 10 files are added to Inbox/ simultaneously, **When** the dashboard update runs, **Then** all 10 tasks appear in the table and the "Total Tasks" statistic increments correctly

5. **Given** Dashboard.md is corrupted (invalid markdown), **When** the update process detects corruption, **Then** it restores from the most recent .bak file and logs the recovery event

6. **Given** the dashboard update process completes, **When** I check the "Last Updated" timestamp, **Then** it reflects the current date/time within 2 seconds of the actual update

---

### User Story 4 - Company Handbook Validation (Priority: P2)

As a **system administrator**, I want the agent to validate Company_Handbook.md at startup to ensure all required configuration sections exist so the system operates according to my defined rules.

**Why this priority**: Configuration validation prevents runtime errors and ensures the agent has clear operational guidelines. This is P2 because the system can function with a basic handbook, but validation improves reliability.

**Independent Test**: Modify Company_Handbook.md to remove a required section, start the watcher, and verify it logs a validation warning. This can be tested independently of file monitoring.

**Acceptance Scenarios**:

1. **Given** Company_Handbook.md is missing the "File Naming Convention" section, **When** the watcher starts, **Then** it logs a validation warning listing the missing section

2. **Given** Company_Handbook.md contains all 5 required sections, **When** the watcher starts, **Then** it logs "Handbook validation passed" and proceeds with monitoring

3. **Given** Company_Handbook.md has a malformed YAML frontmatter, **When** validation runs, **Then** it logs a parsing error with the specific line number and continues with default rules (graceful degradation)

4. **Given** the user updates Company_Handbook.md while the watcher is running, **When** the watcher detects the change, **Then** it re-validates and logs the result without requiring a restart

---

### User Story 5 - Claude Code Vault Querying (Priority: P2)

As a **developer using Claude Code**, I want Agent Skills that expose vault data via Python functions so I can query task status, file counts, and dashboard summaries interactively via chat.

**Why this priority**: This enables human-AI collaboration by giving Claude Code read access to vault state. It's P2 because the watcher provides core functionality, but querying enhances usability.

**Independent Test**: Import the agent_skills.vault_watcher module in a Python REPL, call `get_dashboard_summary()`, and verify it returns a dict with task counts. This can be tested independently of the watcher.

**Acceptance Scenarios**:

1. **Given** the vault contains 3 files in Inbox/ and 2 in Done/, **When** I call `get_dashboard_summary()`, **Then** it returns `{"total": 5, "inbox": 3, "needs_action": 0, "done": 2}`

2. **Given** a file exists at vault/Inbox/task.md, **When** I call `read_vault_file("Inbox/task.md")`, **Then** it returns the file content as a string

3. **Given** vault/Needs_Action/ contains 10 .md files, **When** I call `list_vault_folder("Needs_Action")`, **Then** it returns a list of 10 filenames (not full paths)

4. **Given** Company_Handbook.md is missing the "Escalation Rules" section, **When** I call `validate_handbook()`, **Then** it returns `(False, ["Escalation Rules"])`

5. **Given** Claude Code imports agent_skills.vault_watcher, **When** any function is called with invalid input (e.g., non-existent folder), **Then** it raises a descriptive exception (FileNotFoundError, ValueError) with a helpful error message

---

### Edge Cases

- **What happens when Obsidian locks a file during watcher read?**
  → Watcher logs a warning "File locked by Obsidian: {filename}" and retries on the next polling cycle. Does not crash or corrupt data.

- **What happens when Dashboard.md is deleted by the user?**
  → On next update, the watcher recreates Dashboard.md from scratch with the current task list. Logs a warning "Dashboard.md was missing, recreated."

- **What happens when two files have the same name in different folders?**
  → Dashboard displays both with full relative paths (e.g., "Inbox/task.md" and "Done/task.md"). No collision or data loss.

- **What happens when the vault directory contains 10,000+ files?**
  → Bronze tier spec limits support to 1000 files. Watcher logs a performance warning if count exceeds 1000 but continues to function (may exceed 2-second dashboard update target).

- **What happens when a file is added to Inbox/ with invalid UTF-8 encoding?**
  → Watcher logs an encoding error for that specific file and continues monitoring other files. Dashboard entry shows filename with status "Error: Invalid Encoding."

- **What happens when the system clock changes (DST, timezone adjustment)?**
  → "Date Added" timestamps in Dashboard.md may appear inconsistent, but this is expected behavior. All timestamps use ISO 8601 format with timezone info to minimize confusion.

- **What happens when a user manually edits Dashboard.md while the watcher is running?**
  → Next automatic update may overwrite manual edits if they conflict with the task table format. The .bak file preserves the user's version. Logs a warning "Manual edit detected in Dashboard.md."

- **What happens when Python crashes mid-update (power loss, kill signal)?**
  → Dashboard.md may be partially written (corrupted). On next startup, watcher detects corruption, restores from .bak file, and logs recovery event. This is why atomic writes with backups are critical.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-B001**: System MUST initialize an Obsidian vault directory with 5 folders (Inbox/, Needs_Action/, Done/, Plans/, Logs/) when setup script is executed

- **FR-B002**: System MUST create a Dashboard.md file at vault root containing an empty markdown table with columns [Filename, Date Added, Status, Priority] and a Statistics section

- **FR-B003**: System MUST create a Company_Handbook.md file with 5 required sections: File Naming Convention, Folder Usage Guidelines, Forbidden Operations (Bronze Tier), Escalation Rules, Bronze Tier Limitations

- **FR-B004**: File watcher MUST poll vault/Inbox/ every 30 seconds (configurable via Company_Handbook.md) for new .md files

- **FR-B005**: File watcher MUST ignore non-.md files and hidden folders (.obsidian/, .git/, .DS_Store)

- **FR-B006**: File watcher MUST log all detection events to vault/Logs/watcher-YYYY-MM-DD.md with timestamp, event type, and filename

- **FR-B007**: System MUST update Dashboard.md within 2 seconds of detecting a new file in Inbox/

- **FR-B008**: System MUST create a backup file Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS before every Dashboard.md update

- **FR-B009**: System MUST preserve existing Dashboard.md content when adding new tasks (append to table, don't overwrite)

- **FR-B010**: Dashboard.md MUST use Obsidian wiki link syntax `[[filename]]` for all file references in the Filename column

- **FR-B011**: Dashboard.md MUST include a Statistics section with counts: Total Tasks, Inbox, Needs Action, Done

- **FR-B012**: System MUST validate Company_Handbook.md on watcher startup and log validation results (pass/fail with missing sections)

- **FR-B013**: Agent Skills module (agent_skills/vault_watcher.py) MUST provide function `read_vault_file(filepath: str) -> str` that returns markdown file content

- **FR-B014**: Agent Skills module MUST provide function `list_vault_folder(folder_name: str) -> list[str]` that returns list of .md filenames in specified folder

- **FR-B015**: Agent Skills module MUST provide function `get_dashboard_summary() -> dict` that parses Dashboard.md and returns task counts by status

- **FR-B016**: Agent Skills module MUST provide function `validate_handbook() -> tuple[bool, list[str]]` that checks Company_Handbook.md for required sections

- **FR-B017**: All Agent Skills functions MUST include type hints and docstrings with Args, Returns, Raises, Example sections

- **FR-B018**: System MUST handle race conditions when multiple files are added to Inbox/ simultaneously (all files detected, no dropped events)

- **FR-B019**: System MUST gracefully handle Obsidian file locks by logging a warning and retrying on next polling cycle (no crash)

- **FR-B020**: System MUST detect corrupted Dashboard.md (invalid markdown) and restore from most recent .bak file automatically

- **FR-B021**: System MUST operate 100% offline (no network requests, no external API calls)

- **FR-B022**: System MUST limit file operations to vault/ directory only (no access to parent directories or system files)

- **FR-B023**: System MUST use atomic file write operations: write to temp file → validate → rename to target file

- **FR-B024**: System MUST support vault sizes up to 1000 markdown files (Bronze tier performance limit)

- **FR-B025**: System MUST prune old backup files older than 7 days automatically on watcher startup

### Non-Functional Requirements

#### Performance (NFR-B-PERF)

- **NFR-B-PERF-001**: Dashboard.md update MUST complete within 2 seconds from file detection event to final write
- **NFR-B-PERF-002**: Vault read operations (read_vault_file) MUST complete within 500ms for files up to 100KB
- **NFR-B-PERF-003**: File watcher polling cycle MUST not exceed 30 seconds under normal load (≤1000 files)
- **NFR-B-PERF-004**: System MUST support up to 1000 markdown files in vault without performance degradation

#### Reliability (NFR-B-REL)

- **NFR-B-REL-001**: File watcher uptime MUST be 99% over a 24-hour period (allow graceful restarts after errors)
- **NFR-B-REL-002**: Data integrity: Dashboard.md MUST never be corrupted (atomic writes + backups ensure recoverability)
- **NFR-B-REL-003**: Idempotency: Running file watcher multiple times MUST produce identical Dashboard.md content (deterministic output)
- **NFR-B-REL-004**: System MUST recover from Dashboard.md corruption automatically within one polling cycle (30 seconds)

#### Compatibility (NFR-B-COMPAT)

- **NFR-B-COMPAT-001**: Obsidian compatibility: System MUST work with Obsidian 1.5+ (tested specifically with 1.11.7)
- **NFR-B-COMPAT-002**: Python version: Code MUST run on Python 3.11+ (use pathlib, not os.path; use type hints)
- **NFR-B-COMPAT-003**: Operating System: Primary target is WSL Ubuntu 22.04+; secondary targets are macOS 13+ and Windows 11
- **NFR-B-COMPAT-004**: Markdown syntax: System MUST preserve Obsidian markdown extensions (YAML frontmatter, wiki links `[[]]`, tags `#`)
- **NFR-B-COMPAT-005**: No Obsidian plugins required: System MUST work with standard Obsidian installation (no proprietary plugins)

#### Security (NFR-B-SEC)

- **NFR-B-SEC-001**: System MUST operate 100% offline (zero network requests in Bronze tier)
- **NFR-B-SEC-002**: File operations: System MUST never delete files (read and append only in Bronze tier)
- **NFR-B-SEC-003**: Code execution: System MUST NOT execute vault contents (no eval() on markdown, no shell commands from vault files)
- **NFR-B-SEC-004**: Filesystem access: System MUST be restricted to vault/ directory only (no access to parent directories, /home, /etc)
- **NFR-B-SEC-005**: Credential storage: Bronze tier has no credentials, but system MUST NOT log sensitive data (file contents) to watcher logs

#### Usability (NFR-B-USE)

- **NFR-B-USE-001**: Setup: User MUST be able to initialize vault with a single command (`python scripts/setup_vault.py`)
- **NFR-B-USE-002**: Error messages: All exceptions MUST include actionable error messages (e.g., "File locked by Obsidian: task.md. Will retry in 30 seconds.")
- **NFR-B-USE-003**: Logging: Watcher logs MUST be human-readable markdown files (not JSON or binary formats)
- **NFR-B-USE-004**: Documentation: Company_Handbook.md MUST include inline comments explaining each configuration option

### Key Entities

- **VaultFile**: Represents a markdown file in the vault
  - Attributes: filename (relative path), date_added (ISO 8601 timestamp), status ("Inbox" | "Needs Action" | "Done"), priority ("Medium" default for Bronze)
  - Relationships: Belongs to one VaultFolder

- **VaultFolder**: Represents a top-level folder in the vault
  - Attributes: name (one of ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]), file_count (number of .md files)
  - Relationships: Contains many VaultFiles

- **Dashboard**: Represents the Dashboard.md state
  - Attributes: task_table (list of VaultFiles), statistics (task counts by status), last_updated (timestamp)
  - Relationships: Aggregates VaultFiles from all folders

- **Handbook**: Represents the Company_Handbook.md configuration
  - Attributes: file_naming_convention (string), folder_usage_guidelines (string), forbidden_operations (list), escalation_rules (string), limitations (string)
  - Relationships: Defines rules that govern VaultFile processing

- **WatcherLog**: Represents an event logged to vault/Logs/watcher-YYYY-MM-DD.md
  - Attributes: timestamp (ISO 8601), event_type ("file_detected" | "dashboard_updated" | "error"), filename (if applicable), message (string)
  - Relationships: Many WatcherLogs per day (grouped in single daily log file)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-B001**: User can initialize a Bronze tier vault in under 30 seconds using the setup script (`python scripts/setup_vault.py`)

- **SC-B002**: Within 30 seconds of dropping a test file into vault/Inbox/, the file watcher detects it and logs the event

- **SC-B003**: Dashboard.md updates within 2 seconds of file detection, including the new task in the markdown table

- **SC-B004**: System processes 10 files added simultaneously to Inbox/ without dropping events or corrupting Dashboard.md

- **SC-B005**: File watcher runs continuously for 24 hours with 99% uptime (restarts allowed after errors)

- **SC-B006**: Claude Code can execute `python -c "from agent_skills.vault_watcher import get_dashboard_summary; print(get_dashboard_summary())"` and receive accurate task counts

- **SC-B007**: Company_Handbook.md validation detects missing required sections on watcher startup with 100% accuracy

- **SC-B008**: Dashboard.md is never corrupted: automatic recovery from .bak file works 100% of the time when corruption is detected

- **SC-B009**: System operates 100% offline: no network traffic detected during watcher runtime (verified with network monitoring tool)

- **SC-B010**: All Agent Skills functions have 80%+ code coverage in pytest unit tests

- **SC-B011**: Vault with 1000 markdown files processes new file detection within 30-second polling interval (performance target met)

- **SC-B012**: Obsidian can open the vault and render Dashboard.md correctly without syntax errors (markdown table displays as table)

### Definition of Done

Bronze Tier is considered **Done** when:

1. ✅ All 5 user stories have passing acceptance tests
2. ✅ All 25 functional requirements (FR-B001 through FR-B025) are implemented
3. ✅ All 18 non-functional requirements (NFR-B-*) are verified
4. ✅ All 12 success criteria (SC-B001 through SC-B012) are met
5. ✅ Pytest unit tests achieve 80%+ coverage for agent_skills/ module
6. ✅ Integration test passes: Drop test file → Watcher detects → Dashboard updates → Claude Code queries
7. ✅ User can run system end-to-end without developer assistance (documented in README.md)
8. ✅ Code passes mypy type checking with zero errors
9. ✅ Code passes black formatting check
10. ✅ All edge cases are handled gracefully (no crashes on locked files, corrupted data, or race conditions)

## Dependencies

### Python Packages (pyproject.toml)

```toml
[project]
name = "personal-ai-employee-bronze"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "watchdog>=3.0.0",      # File system monitoring
    "pyyaml>=6.0",          # YAML parsing for handbook validation
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",          # Unit testing
    "pytest-cov>=4.0",      # Code coverage
    "black>=23.0",          # Code formatting
    "mypy>=1.0",            # Type checking
]
```

### External Tools (User-Installed)

- **Obsidian Desktop App**: v1.5+ (user installs from https://obsidian.md/download)
- **Python**: 3.11+ (user installs from https://www.python.org/downloads/)
- **Git**: For version control (optional but recommended)

### System Requirements

- **RAM**: 8GB minimum (watcher process uses <100MB)
- **Disk Space**: 1GB for vault with 1000 markdown files
- **CPU**: 4-core minimum (watcher polling is lightweight)
- **OS**: WSL Ubuntu 22.04+ (primary), macOS 13+, Windows 11 (secondary)

## Out of Scope (Deferred to Future Tiers)

The following features are **explicitly excluded** from Bronze Tier and deferred to Silver, Gold, or Platinum tiers:

### Deferred to Silver Tier
- ❌ AI-powered priority analysis (Claude API for task classification)
- ❌ Automatic file movement between folders (human approval required in Bronze)
- ❌ Plan.md generation (Claude reasoning loop)
- ❌ Human-in-the-loop approval workflow (Bronze has no autonomous actions to approve)
- ❌ Email/WhatsApp watcher integration (Bronze is vault-only)

### Deferred to Gold Tier
- ❌ Multi-step plan execution (autonomous workflows)
- ❌ External API integrations (email, calendar, social media)
- ❌ Task decomposition (breaking large tasks into subtasks)
- ❌ Cross-domain integration (Personal + Business workflows)
- ❌ Business audit and CEO briefing generation

### Deferred to Platinum Tier
- ❌ Reflection loops (autonomous error correction)
- ❌ Cloud deployment (24/7 always-on operation)
- ❌ Agent-to-agent communication (Local + Cloud coordination)
- ❌ Odoo accounting integration
- ❌ Social media posting automation

### Never in Bronze (Safety Boundaries)
- ❌ Autonomous file deletion
- ❌ Autonomous email sending
- ❌ Autonomous payment processing
- ❌ Execution of code from vault files
- ❌ Network requests of any kind

## Validation Checklist

Before marking Bronze Tier spec as **Approved**, verify:

- [x] All 5 user stories have clear acceptance scenarios in Given-When-Then format
- [x] All user stories are prioritized (P1, P2) and can be tested independently
- [x] Functional requirements reference specific file paths and data formats
- [x] Non-functional requirements have measurable targets (e.g., "2 seconds", "99% uptime", "1000 files")
- [x] API signatures include type hints (e.g., `-> dict`, `-> tuple[bool, list[str]]`)
- [x] API functions include docstrings with Args, Returns, Raises, Example sections
- [x] Success criteria are measurable without human judgment (automated tests)
- [x] Out of scope items are clearly documented to prevent feature creep
- [x] Dependencies specify minimum versions (e.g., `watchdog>=3.0.0`)
- [x] Compatibility matrix matches constitution requirements (Obsidian 1.5+, Python 3.11+, WSL Ubuntu)
- [x] Edge cases include failure modes (file locks, corruption, race conditions)
- [x] Definition of Done includes code quality gates (coverage, type checking, formatting)
- [x] Security requirements enforce offline operation and filesystem restrictions

## Appendix A: Dashboard.md Reference Format

```markdown
# Personal AI Employee Dashboard

## Task Overview
| Filename | Date Added | Status | Priority |
|----------|-----------|--------|----------|
| [[Inbox/2026-02-10-review-proposal.md]] | 2026-02-10 15:30 | Inbox | Medium |
| [[Needs_Action/2026-02-09-fix-bug.md]] | 2026-02-09 14:20 | Needs Action | Medium |
| [[Done/2026-02-08-client-email.md]] | 2026-02-08 10:15 | Done | Medium |

## Statistics
- **Total Tasks**: 3
- **Inbox**: 1
- **Needs Action**: 1
- **Done**: 1

---
*Last Updated: 2026-02-10 15:30:45*
```

## Appendix B: Company_Handbook.md Reference Format

```markdown
---
version: 1.0.0
tier: bronze
last_updated: 2026-02-10
---

# Company Handbook - Bronze Tier

## 1. File Naming Convention

All task files in Inbox/ should follow this format:
- Format: `YYYY-MM-DD-brief-description.md`
- Example: `2026-02-10-review-client-proposal.md`
- Hyphens for word separation (no spaces)
- Dates in ISO 8601 format (YYYY-MM-DD)

## 2. Folder Usage Guidelines

- **Inbox/**: Drop all new tasks here. Watcher monitors this folder.
- **Needs_Action/**: (Manual move in Bronze) Tasks requiring immediate attention.
- **Done/**: (Manual move in Bronze) Completed tasks for archival.
- **Plans/**: Reserved for future use (Silver tier and above).
- **Logs/**: System-generated logs. Do not manually edit.

## 3. Forbidden Operations (Bronze Tier)

The Bronze tier AI Employee is **monitoring only**. It will:
- ✅ Detect new files in Inbox/
- ✅ Update Dashboard.md automatically
- ✅ Log events to vault/Logs/

It will **NOT**:
- ❌ Delete any files
- ❌ Move files between folders
- ❌ Modify file contents
- ❌ Execute code from vault files
- ❌ Make network requests

## 4. Escalation Rules

The watcher logs warnings for:
- Obsidian file locks (will retry automatically)
- Dashboard.md corruption (will restore from backup)
- Vault exceeding 1000 files (performance warning)
- Invalid file encoding (UTF-8 required)

**Human intervention required for**:
- Watcher process crashes (check vault/Logs/ for errors)
- Persistent file lock conflicts (close Obsidian temporarily)
- Backup restoration failures (manual recovery from .bak files)

## 5. Bronze Tier Limitations

This is a **foundation tier**. The AI Employee:
- Operates 100% offline (no AI analysis, no external APIs)
- Requires manual file movement (no autonomous actions)
- Defaults all tasks to "Medium" priority (no smart prioritization)
- Polls every 30 seconds (not real-time monitoring)
- Supports up to 1000 files (performance limit)

**Upgrade to Silver Tier for**:
- AI-powered priority analysis
- Automatic file movement with approval workflow
- Integration with email/WhatsApp
```

## Appendix C: Agent Skills API Examples

```python
# Example 1: Query dashboard from Claude Code
from agent_skills.vault_watcher import get_dashboard_summary

summary = get_dashboard_summary()
print(f"You have {summary['inbox']} tasks in Inbox")
print(f"Total tasks: {summary['total']}")

# Example 2: Read a specific task file
from agent_skills.vault_watcher import read_vault_file

content = read_vault_file("Inbox/2026-02-10-client-proposal.md")
print(content)

# Example 3: List all files in a folder
from agent_skills.vault_watcher import list_vault_folder

files = list_vault_folder("Done")
print(f"Completed tasks: {', '.join(files)}")

# Example 4: Validate handbook configuration
from agent_skills.vault_watcher import validate_handbook

is_valid, missing = validate_handbook()
if not is_valid:
    print(f"Handbook validation failed. Missing sections: {missing}")
else:
    print("Handbook is properly configured")
```

---

**Next Step**: Proceed to `/sp.plan bronze-tier` to design the implementation architecture for this specification.
