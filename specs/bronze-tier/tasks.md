# Tasks: Bronze Tier - Foundation AI Employee

**Input**: Design documents from `/specs/bronze-tier/`
**Prerequisites**: plan.md ✅, spec.md ✅

**Organization**: Tasks are grouped by implementation phase (4 phases) aligned with user stories. Each phase builds on the previous, following the constitution's incremental development principle.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Path Conventions

Bronze tier uses **single project structure**:
- `agent_skills/`: Reusable Python modules
- `scripts/`: Entry point scripts
- `tests/`: Pytest test suite (unit/, integration/, fixtures/)
- `vault/`: Product deliverable (Obsidian vault)

---

## Phase 1: Foundation (Setup & Core Infrastructure)

**Purpose**: Initialize project structure and implement core Agent Skills API (vault_watcher.py). This is the foundation that all other phases depend on.

**⚠️ CRITICAL**: Phase 2, 3, and 4 depend on Phase 1 completion.

### T001-T005: Project Setup

- [ ] **T001** [P] [Setup] Create project structure (agent_skills/, scripts/, tests/, vault/)
  - **Files**: `agent_skills/__init__.py`, `scripts/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `vault/`
  - **Acceptance**: All directories exist, `agent_skills/__init__.py` is empty Python package
  - **Time**: 5 minutes

- [ ] **T002** [P] [Setup] Initialize Python project with pyproject.toml
  - **Files**: `pyproject.toml`
  - **Dependencies**: watchdog>=3.0.0, pyyaml>=6.0, pytest>=7.0, pytest-cov>=4.0, black>=23.0, mypy>=1.0
  - **Acceptance**: `pip install -e .[dev]` works without errors
  - **Reference**: Plan section "Dependencies" (watchdog, pyyaml, pytest)
  - **Time**: 10 minutes

- [ ] **T003** [P] [Setup] Configure mypy type checking
  - **Files**: `mypy.ini` or `pyproject.toml` [tool.mypy] section
  - **Config**: strict=true, python_version=3.11, check_untyped_defs=true
  - **Acceptance**: `mypy agent_skills/ scripts/` runs without errors on empty modules
  - **Time**: 5 minutes

- [ ] **T004** [P] [Setup] Configure black code formatter
  - **Files**: `pyproject.toml` [tool.black] section
  - **Config**: line-length=100, target-version=['py311']
  - **Acceptance**: `black --check agent_skills/ scripts/` passes on empty modules
  - **Time**: 5 minutes

- [ ] **T005** [P] [Setup] Configure pytest with coverage
  - **Files**: `pyproject.toml` [tool.pytest.ini_options] section
  - **Config**: testpaths=["tests"], python_files="test_*.py", addopts="--cov=agent_skills --cov-report=term-missing"
  - **Acceptance**: `pytest` runs (no tests yet, but command works)
  - **Time**: 5 minutes

### T006-T010: Vault Initialization Script (US1)

**User Story 1**: Vault Structure Initialization (P1)

- [ ] **T006** [US1] Implement create_folder_structure() in scripts/init_vault.py
  - **Files**: `scripts/init_vault.py`
  - **Function**: `def create_folder_structure(vault_path: Path) -> None`
  - **Logic**: Create 5 folders (Inbox/, Needs_Action/, Done/, Plans/, Logs/) using pathlib.Path.mkdir(parents=True, exist_ok=True)
  - **Acceptance**: Function creates all 5 folders, no error if folders already exist
  - **Reference**: Spec FR-B001, Plan section 3.4
  - **Time**: 15 minutes

- [ ] **T007** [US1] Implement create_dashboard() in scripts/init_vault.py
  - **Files**: `scripts/init_vault.py`
  - **Function**: `def create_dashboard(vault_path: Path) -> None`
  - **Logic**: Write Dashboard.md template (empty task table + statistics section)
  - **Template**: See Spec Appendix A for exact format
  - **Acceptance**: Dashboard.md created with valid markdown table, renders correctly in text editor
  - **Reference**: Spec FR-B002, Appendix A
  - **Time**: 20 minutes

- [ ] **T008** [US1] Implement create_handbook() in scripts/init_vault.py
  - **Files**: `scripts/init_vault.py`
  - **Function**: `def create_handbook(vault_path: Path) -> None`
  - **Logic**: Write Company_Handbook.md template with 5 required sections + YAML frontmatter
  - **Template**: See Spec Appendix B for exact format
  - **Acceptance**: Company_Handbook.md created with valid YAML + 5 sections
  - **Reference**: Spec FR-B003, Appendix B
  - **Time**: 25 minutes

- [ ] **T009** [US1] Implement main() entry point in scripts/init_vault.py
  - **Files**: `scripts/init_vault.py`
  - **Function**: `def main(vault_path: str, overwrite: bool = False) -> None`
  - **Logic**: Validate vault_path, call create_folder_structure, create_dashboard, create_handbook, handle FileExistsError
  - **CLI**: Add argparse for --overwrite flag
  - **Acceptance**: `python scripts/init_vault.py /path/to/vault` creates complete vault structure
  - **Reference**: Plan section 3.4
  - **Time**: 20 minutes

- [ ] **T010** [US1] Add signal handling and logging to scripts/init_vault.py
  - **Files**: `scripts/init_vault.py`
  - **Logic**: Add logging.info() for each step, print success message to stdout
  - **Error handling**: Catch PermissionError, log error, exit with code 3
  - **Acceptance**: Script logs "Vault initialized at {vault_path}" on success
  - **Reference**: Plan section 3.4 exit codes
  - **Time**: 10 minutes

### T011-T018: Agent Skills API - vault_watcher.py (US5)

**User Story 5**: Claude Code Vault Querying (P2)

- [ ] **T011** [P] [US5] Implement read_vault_file() in agent_skills/vault_watcher.py
  - **Files**: `agent_skills/vault_watcher.py`
  - **Function**: `def read_vault_file(vault_path: str, filepath: str) -> str`
  - **Logic**: Validate filepath (no `..`), construct full path, read UTF-8 file, return content
  - **Error handling**: Raise FileNotFoundError, PermissionError, UnicodeDecodeError, ValueError for directory traversal
  - **Acceptance**: Function reads markdown file, raises exceptions for invalid input
  - **Reference**: Spec FR-B013, Plan section 3.1
  - **Time**: 25 minutes

- [ ] **T012** [P] [US5] Implement list_vault_folder() in agent_skills/vault_watcher.py
  - **Files**: `agent_skills/vault_watcher.py`
  - **Function**: `def list_vault_folder(vault_path: str, folder_name: str) -> list[str]`
  - **Logic**: Validate folder_name (one of 5 allowed), list .md files (glob "*.md"), sort alphabetically, return filenames only
  - **Error handling**: Raise ValueError if folder_name invalid, FileNotFoundError if folder doesn't exist
  - **Acceptance**: Function returns sorted list of .md filenames, filters non-.md files
  - **Reference**: Spec FR-B014, Plan section 3.1
  - **Time**: 25 minutes

- [ ] **T013** [P] [US5] Implement get_dashboard_summary() in agent_skills/vault_watcher.py
  - **Files**: `agent_skills/vault_watcher.py`
  - **Function**: `def get_dashboard_summary(vault_path: str) -> dict[str, int]`
  - **Logic**: Read Dashboard.md, parse markdown table, count by Status column, return {"total": N, "inbox": N, "needs_action": N, "done": N}
  - **Parsing**: Find table start (| Filename | Date Added | Status | Priority |), extract rows, parse Status (3rd column)
  - **Error handling**: Return all zeros if Dashboard.md missing, raise ValueError if corrupted
  - **Acceptance**: Function returns correct task counts from Dashboard.md
  - **Reference**: Spec FR-B015, Plan section 3.1
  - **Time**: 35 minutes

- [ ] **T014** [P] [US5] Implement validate_handbook() in agent_skills/vault_watcher.py
  - **Files**: `agent_skills/vault_watcher.py`
  - **Function**: `def validate_handbook(vault_path: str) -> tuple[bool, list[str]]`
  - **Logic**: Read Company_Handbook.md, extract markdown headers (regex `^##+ (.+)$`), check for 5 required sections (case-insensitive substring match)
  - **YAML handling**: Parse frontmatter with pyyaml, log warning if malformed, continue validation
  - **Acceptance**: Function returns (True, []) if all sections present, (False, [missing]) otherwise
  - **Reference**: Spec FR-B016, Plan section 3.1
  - **Time**: 30 minutes

- [ ] **T015** [P] [US5] Add comprehensive docstrings to all vault_watcher.py functions
  - **Files**: `agent_skills/vault_watcher.py`
  - **Format**: Google style docstrings with Args, Returns, Raises, Example sections
  - **Acceptance**: All 4 functions have complete docstrings matching Spec Appendix C format
  - **Reference**: Spec FR-B017, Plan section 3.1
  - **Time**: 20 minutes

### T016-T022: Unit Tests for vault_watcher.py (US5)

**User Story 5**: Claude Code Vault Querying (P2)

- [ ] **T016** [P] [US5] Create test fixtures in tests/fixtures/sample_vault/
  - **Files**: `tests/fixtures/sample_vault/Inbox/test-task.md`, `tests/fixtures/sample_vault/Dashboard.md`, `tests/fixtures/sample_vault/Company_Handbook.md`
  - **Content**: Valid markdown files for testing (3-5 sample tasks, valid dashboard, valid handbook)
  - **Acceptance**: Fixture vault has all 5 folders, valid files for testing
  - **Time**: 15 minutes

- [ ] **T017** [P] [US5] Write unit tests for read_vault_file() in tests/unit/test_vault_watcher.py
  - **Files**: `tests/unit/test_vault_watcher.py`
  - **Tests**: test_read_valid_file, test_read_missing_file, test_read_locked_file, test_read_invalid_encoding, test_directory_traversal_attack
  - **Assertions**: Check return value is string, check exceptions raised for error cases
  - **Acceptance**: All 5 tests pass, achieve 90%+ coverage for read_vault_file()
  - **Reference**: Spec US-5 Acceptance Scenario 2
  - **Time**: 30 minutes

- [ ] **T018** [P] [US5] Write unit tests for list_vault_folder() in tests/unit/test_vault_watcher.py
  - **Files**: `tests/unit/test_vault_watcher.py`
  - **Tests**: test_list_inbox_folder, test_list_empty_folder, test_list_invalid_folder_name, test_list_non_existent_folder, test_filters_non_md_files
  - **Assertions**: Check return is sorted list, check ValueError for invalid folder, check filtering works
  - **Acceptance**: All 5 tests pass, achieve 90%+ coverage for list_vault_folder()
  - **Reference**: Spec US-5 Acceptance Scenario 3
  - **Time**: 30 minutes

- [ ] **T019** [P] [US5] Write unit tests for get_dashboard_summary() in tests/unit/test_vault_watcher.py
  - **Files**: `tests/unit/test_vault_watcher.py`
  - **Tests**: test_summary_with_tasks, test_summary_empty_dashboard, test_summary_missing_dashboard, test_summary_corrupted_dashboard
  - **Assertions**: Check return dict has correct keys/values, check error handling
  - **Acceptance**: All 4 tests pass, achieve 90%+ coverage for get_dashboard_summary()
  - **Reference**: Spec US-5 Acceptance Scenario 1
  - **Time**: 25 minutes

- [ ] **T020** [P] [US5] Write unit tests for validate_handbook() in tests/unit/test_vault_watcher.py
  - **Files**: `tests/unit/test_vault_watcher.py`
  - **Tests**: test_validate_complete_handbook, test_validate_missing_sections, test_validate_malformed_yaml, test_validate_missing_handbook
  - **Assertions**: Check (bool, list) return type, check missing sections correctly identified
  - **Acceptance**: All 4 tests pass, achieve 90%+ coverage for validate_handbook()
  - **Reference**: Spec US-4 Acceptance Scenario 1, 2, 3
  - **Time**: 25 minutes

- [ ] **T021** [US5] Verify 80%+ test coverage for agent_skills/vault_watcher.py
  - **Command**: `pytest --cov=agent_skills.vault_watcher --cov-report=term-missing tests/unit/test_vault_watcher.py`
  - **Acceptance**: Coverage report shows ≥80% for vault_watcher.py
  - **Fix**: Add missing tests for uncovered branches if coverage <80%
  - **Reference**: Spec NFR-B-USE-001 (80% coverage target)
  - **Time**: 10 minutes

- [ ] **T022** [US5] Run mypy and black on agent_skills/vault_watcher.py
  - **Commands**: `mypy agent_skills/vault_watcher.py`, `black --check agent_skills/vault_watcher.py`
  - **Acceptance**: Mypy passes with zero errors, black passes with no formatting changes
  - **Fix**: Add type hints or reformat if checks fail
  - **Reference**: Plan Definition of Done (mypy + black checks)
  - **Time**: 10 minutes

**Checkpoint Phase 1**: At this point, vault initialization and Agent Skills API are complete and tested. User Story 1 (US1) and User Story 5 (US5) are fully functional.

---

## Phase 2: Monitoring (Dashboard Updates & File Watcher)

**Purpose**: Implement dashboard_updater.py (atomic writes with backups) and watch_inbox.py (polling loop). This phase enables automatic dashboard updates when files are detected.

**Dependencies**: Phase 1 must be complete (vault_watcher.py functions are used by dashboard_updater.py).

### T023-T029: Dashboard Updater Module (US3)

**User Story 3**: Automatic Dashboard Updates (P1)

- [ ] **T023** [US3] Implement parse_dashboard() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def parse_dashboard(dashboard_path: Path) -> list[dict]`
  - **Logic**: Read Dashboard.md, extract task table rows, parse each row into dict {"filename": str, "date_added": str, "status": str, "priority": str}
  - **Error handling**: Return empty list if Dashboard.md missing, raise ValueError if table malformed
  - **Acceptance**: Function parses Dashboard.md → list of task dicts
  - **Reference**: Plan section 3.2 atomic write algorithm
  - **Time**: 30 minutes

- [ ] **T024** [US3] Implement render_dashboard() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def render_dashboard(tasks: list[dict]) -> str`
  - **Logic**: Generate markdown table from task list, add Statistics section (count by status), add Last Updated timestamp
  - **Format**: Use Obsidian wiki link syntax [[filename]] for Filename column
  - **Acceptance**: Function renders valid markdown table matching Spec Appendix A format
  - **Reference**: Spec FR-B010, Plan section 3.2
  - **Time**: 35 minutes

- [ ] **T025** [US3] Implement create_backup() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def create_backup(dashboard_path: Path) -> Path`
  - **Logic**: Copy Dashboard.md → Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS (timestamp format)
  - **Error handling**: Raise IOError if backup creation fails
  - **Acceptance**: Backup file created with timestamp in filename
  - **Reference**: Spec FR-B008, Plan section 3.2
  - **Time**: 15 minutes

- [ ] **T026** [US3] Implement validate_dashboard() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def validate_dashboard(dashboard_path: Path) -> bool`
  - **Logic**: Check Dashboard.md has valid markdown table (4 columns, separator row), check all Status values are valid
  - **Acceptance**: Returns True for valid dashboard, False for corrupted dashboard
  - **Reference**: Plan section 8.2 output validation
  - **Time**: 20 minutes

- [ ] **T027** [US3] Implement update_dashboard() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def update_dashboard(vault_path: str, new_files: list[tuple[str, str]]) -> bool`
  - **Logic**: Atomic write algorithm (backup → parse → merge → render → write temp → validate → rename)
  - **Error handling**: Return False on any error, Dashboard.md unchanged (backup preserved)
  - **Acceptance**: Dashboard.md updated atomically, .bak file created, temp file cleaned up
  - **Reference**: Spec FR-B007, FR-B008, FR-B009, Plan section 3.2
  - **Time**: 45 minutes

- [ ] **T028** [US3] Implement restore_from_backup() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def restore_from_backup(vault_path: str, backup_filename: str = None) -> bool`
  - **Logic**: List .bak files, sort by timestamp (newest first), copy to Dashboard.md.tmp, validate, atomic rename
  - **Acceptance**: Dashboard.md restored from most recent backup (or specified backup)
  - **Reference**: Spec FR-B020, Plan section 3.2
  - **Time**: 25 minutes

- [ ] **T029** [US3] Implement prune_old_backups() in agent_skills/dashboard_updater.py
  - **Files**: `agent_skills/dashboard_updater.py`
  - **Function**: `def prune_old_backups(vault_path: str, keep_days: int = 7) -> int`
  - **Logic**: List .bak files, delete files older than keep_days, return count deleted
  - **Acceptance**: Old backups deleted, recent backups preserved
  - **Reference**: Spec FR-B025, Plan section 5.3
  - **Time**: 20 minutes

### T030-T034: Unit Tests for dashboard_updater.py (US3)

**User Story 3**: Automatic Dashboard Updates (P1)

- [ ] **T030** [P] [US3] Create corrupted dashboard fixture in tests/fixtures/
  - **Files**: `tests/fixtures/corrupted_dashboard.md`
  - **Content**: Invalid markdown table (missing pipes, misaligned columns, incomplete write)
  - **Acceptance**: Fixture file exists, can be used to test corruption detection
  - **Time**: 10 minutes

- [ ] **T031** [P] [US3] Write unit tests for parse/render functions in tests/unit/test_dashboard_updater.py
  - **Files**: `tests/unit/test_dashboard_updater.py`
  - **Tests**: test_parse_valid_dashboard, test_parse_empty_dashboard, test_render_task_list, test_render_empty_list
  - **Acceptance**: All 4 tests pass, verify parse/render roundtrip works
  - **Time**: 30 minutes

- [ ] **T032** [P] [US3] Write unit tests for backup functions in tests/unit/test_dashboard_updater.py
  - **Files**: `tests/unit/test_dashboard_updater.py`
  - **Tests**: test_create_backup, test_restore_from_backup, test_restore_specific_backup, test_prune_old_backups
  - **Acceptance**: All 4 tests pass, verify backup/restore works correctly
  - **Reference**: Spec US-3 Acceptance Scenario 3, 5
  - **Time**: 35 minutes

- [ ] **T033** [P] [US3] Write unit tests for update_dashboard() in tests/unit/test_dashboard_updater.py
  - **Files**: `tests/unit/test_dashboard_updater.py`
  - **Tests**: test_update_new_tasks, test_update_preserves_existing, test_update_creates_backup, test_update_corruption_recovery, test_update_idempotency
  - **Assertions**: Verify atomic write, backup created, corruption recovery, same output on re-run
  - **Acceptance**: All 5 tests pass, verify update_dashboard() is atomic and idempotent
  - **Reference**: Spec US-3 Acceptance Scenario 1, 2, 4, 5
  - **Time**: 45 minutes

- [ ] **T034** [US3] Verify 80%+ test coverage for agent_skills/dashboard_updater.py
  - **Command**: `pytest --cov=agent_skills.dashboard_updater --cov-report=term-missing tests/unit/test_dashboard_updater.py`
  - **Acceptance**: Coverage report shows ≥80%
  - **Reference**: Spec NFR-B-USE-001 (80% coverage target)
  - **Time**: 10 minutes

### T035-T041: File Watcher Script (US2)

**User Story 2**: Inbox File Detection (P1)

- [ ] **T035** [US2] Implement detect_new_files() in scripts/watch_inbox.py
  - **Files**: `scripts/watch_inbox.py`
  - **Function**: `def detect_new_files(vault_path: Path, processed_files: set[str]) -> list[tuple[str, str]]`
  - **Logic**: List Inbox/ .md files, filter out processed_files, return [(filename, "Inbox"), ...] for new files
  - **Error handling**: Catch PermissionError (file locked), log warning, skip file
  - **Acceptance**: Function returns new files not in processed_files set
  - **Reference**: Spec FR-B004, FR-B005, FR-B019
  - **Time**: 30 minutes

- [ ] **T036** [US2] Implement log_event() in scripts/watch_inbox.py
  - **Files**: `scripts/watch_inbox.py`
  - **Function**: `def log_event(vault_path: Path, event_type: str, details: dict) -> None`
  - **Logic**: Append event to vault/Logs/watcher-YYYY-MM-DD.md (human-readable markdown format)
  - **Format**: See Plan section 3.5 for log format (timestamp, event type, file list)
  - **Acceptance**: Events logged to daily log file with timestamp
  - **Reference**: Spec FR-B006, Plan section 3.5
  - **Time**: 25 minutes

- [ ] **T037** [US2] Implement poll_inbox() in scripts/watch_inbox.py
  - **Files**: `scripts/watch_inbox.py`
  - **Function**: `def poll_inbox(vault_path: Path, config: dict) -> None`
  - **Logic**: Infinite loop (while True), detect_new_files(), update_dashboard(), log_event(), time.sleep(POLLING_INTERVAL)
  - **Error handling**: Catch all exceptions, log error, continue (graceful degradation)
  - **Acceptance**: Polling loop runs continuously, errors don't crash watcher
  - **Reference**: Spec FR-B004, Plan section 3.3 polling loop algorithm
  - **Time**: 35 minutes

- [ ] **T038** [US2] Implement signal handlers in scripts/watch_inbox.py
  - **Files**: `scripts/watch_inbox.py`
  - **Logic**: Register handlers for SIGINT (graceful shutdown), SIGTERM (graceful shutdown), SIGHUP (re-validate handbook)
  - **Acceptance**: Watcher logs "Watcher stopped" on SIGINT, exits gracefully
  - **Reference**: Plan section 3.3 signal handling
  - **Time**: 20 minutes

- [ ] **T039** [US2] Implement main() entry point in scripts/watch_inbox.py
  - **Files**: `scripts/watch_inbox.py`
  - **Function**: `def main(vault_path: str, config: dict = None) -> None`
  - **Logic**: Validate vault structure, validate handbook, init logging, call poll_inbox()
  - **Error handling**: Exit code 1 (invalid vault), 2 (handbook validation failed), 3 (permission error)
  - **CLI**: Add argparse for vault_path, optional config overrides
  - **Acceptance**: `python scripts/watch_inbox.py /path/to/vault` starts watcher
  - **Reference**: Spec FR-B004, FR-B012, Plan section 3.3
  - **Time**: 30 minutes

- [ ] **T040** [US2] Add configuration loading from Company_Handbook.md
  - **Files**: `scripts/watch_inbox.py`
  - **Logic**: Parse Company_Handbook.md YAML frontmatter, extract polling_interval (default 30s)
  - **Acceptance**: Watcher uses polling_interval from handbook (fallback to 30s if not specified)
  - **Reference**: Spec FR-B004 (configurable via handbook)
  - **Time**: 15 minutes

- [ ] **T041** [US2] Add heartbeat logging to poll_inbox()
  - **Files**: `scripts/watch_inbox.py`
  - **Logic**: Log "heartbeat" event every polling cycle (for watchdog health monitoring)
  - **Acceptance**: vault/Logs/watcher-DATE.md shows heartbeat events every 30 seconds
  - **Reference**: Plan section 4.2 reliability monitoring
  - **Time**: 10 minutes

### T042-T044: Integration Test (US2 + US3)

**User Story 2 + User Story 3**: End-to-End Flow

- [ ] **T042** [US2+US3] Write end-to-end integration test in tests/integration/test_end_to_end.py
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_drop_file_detect_update_query
  - **Logic**: Init vault → Start watcher (background thread) → Drop test file in Inbox/ → Wait 35s → Assert Dashboard.md updated → Assert vault_watcher.get_dashboard_summary() returns correct counts → Assert watcher log exists
  - **Acceptance**: Integration test passes, verifies full workflow
  - **Reference**: Spec SC-B001 through SC-B006, Plan section 8.3
  - **Time**: 45 minutes

- [ ] **T043** [US2+US3] Test race condition handling (10 files simultaneously)
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_simultaneous_file_detection
  - **Logic**: Start watcher → Drop 10 files at once → Wait 35s → Assert all 10 files in Dashboard.md → Assert no dropped events
  - **Acceptance**: All 10 files detected, no race conditions
  - **Reference**: Spec US-2 Acceptance Scenario 2, Spec SC-B004
  - **Time**: 30 minutes

- [ ] **T044** [US2+US3] Test file lock handling
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_file_lock_graceful_degradation
  - **Logic**: Start watcher → Lock test file (simulate Obsidian lock) → Drop locked file → Verify watcher logs warning → Verify watcher continues (doesn't crash)
  - **Acceptance**: Watcher logs "file locked" warning, continues monitoring
  - **Reference**: Spec US-2 Acceptance Scenario 4, Spec Edge Case "Obsidian locks file"
  - **Time**: 35 minutes

**Checkpoint Phase 2**: At this point, file watching, dashboard updates, and integration tests are complete. User Story 2 (US2) and User Story 3 (US3) are fully functional.

---

## Phase 3: Validation (Handbook Validation & Error Handling)

**Purpose**: Implement Company_Handbook.md validation at watcher startup, add robust error handling for all edge cases.

**Dependencies**: Phase 2 must be complete (watcher script exists, handbook validation will be added to startup).

### T045-T048: Handbook Validation (US4)

**User Story 4**: Company Handbook Validation (P2)

- [ ] **T045** [US4] Integrate validate_handbook() into watch_inbox.py startup
  - **Files**: `scripts/watch_inbox.py` (modify main() function)
  - **Logic**: Call validate_handbook() before starting poll_inbox(), exit with code 2 if validation fails
  - **Acceptance**: Watcher exits with error message if handbook missing required sections
  - **Reference**: Spec US-4 Acceptance Scenario 1, 2
  - **Time**: 15 minutes

- [ ] **T046** [US4] Add handbook re-validation on SIGHUP
  - **Files**: `scripts/watch_inbox.py` (modify signal handler)
  - **Logic**: On SIGHUP, re-run validate_handbook(), log result, continue monitoring (don't exit)
  - **Acceptance**: Watcher re-validates handbook without restarting process
  - **Reference**: Spec US-4 Acceptance Scenario 4
  - **Time**: 15 minutes

- [ ] **T047** [P] [US4] Write unit tests for handbook validation in tests/unit/test_vault_watcher.py
  - **Files**: `tests/unit/test_vault_watcher.py` (add more tests if needed)
  - **Tests**: test_validate_missing_multiple_sections, test_validate_fuzzy_matching (e.g., "## 4. Escalation Rules" matches "Escalation Rules")
  - **Acceptance**: Tests cover edge cases, verify fuzzy matching works
  - **Reference**: Plan section 3.1 validation algorithm
  - **Time**: 20 minutes

- [ ] **T048** [US4] Test watcher startup with invalid handbook (integration test)
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_watcher_exits_on_invalid_handbook
  - **Logic**: Create vault with missing handbook sections → Start watcher → Assert exit code 2 → Assert error message logged
  - **Acceptance**: Watcher exits gracefully with helpful error message
  - **Reference**: Spec US-4 Acceptance Scenario 1
  - **Time**: 25 minutes

### T049-T052: Edge Case Handling

- [ ] **T049** [P] Test Dashboard.md corruption recovery (integration test)
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_dashboard_corruption_recovery
  - **Logic**: Start watcher → Corrupt Dashboard.md (overwrite with invalid markdown) → Trigger update → Verify watcher detects corruption → Verify automatic restore from .bak → Assert Dashboard.md valid again
  - **Acceptance**: Watcher auto-restores corrupted dashboard from backup
  - **Reference**: Spec US-3 Acceptance Scenario 5, Spec Edge Case "Dashboard.md corrupted"
  - **Time**: 40 minutes

- [ ] **T050** [P] Test Dashboard.md deleted (watcher recreates)
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_dashboard_deleted_recreated
  - **Logic**: Start watcher → Delete Dashboard.md → Drop new file → Verify watcher recreates Dashboard.md from scratch with current vault state
  - **Acceptance**: Dashboard.md recreated, logs warning "Dashboard.md was missing, recreated"
  - **Reference**: Spec Edge Case "Dashboard.md deleted"
  - **Time**: 30 minutes

- [ ] **T051** [P] Test invalid UTF-8 encoding in vault file
  - **Files**: `tests/integration/test_end_to_end.py`
  - **Test**: test_invalid_encoding_handled
  - **Logic**: Start watcher → Drop file with invalid UTF-8 → Verify watcher logs encoding error → Verify watcher continues (doesn't crash) → Dashboard entry shows "Error: Invalid Encoding"
  - **Acceptance**: Watcher handles encoding errors gracefully
  - **Reference**: Spec Edge Case "File with invalid UTF-8 encoding"
  - **Time**: 30 minutes

- [ ] **T052** Test 1000-file vault performance
  - **Files**: `tests/integration/test_performance.py` (new file)
  - **Test**: test_vault_with_1000_files
  - **Logic**: Create fixture vault with 1000 markdown files → Start watcher → Drop new file → Measure time to detect and update dashboard → Assert <30s polling cycle, <2s dashboard update
  - **Acceptance**: Performance targets met with 1000-file vault
  - **Reference**: Spec SC-B011, Spec NFR-B-PERF-004
  - **Time**: 45 minutes

**Checkpoint Phase 3**: At this point, handbook validation and all edge case handling is complete. User Story 4 (US4) is fully functional.

---

## Phase 4: Polish & Documentation

**Purpose**: Create runbooks, README.md, verify all acceptance criteria met, run full test suite, ensure production-ready quality.

**Dependencies**: Phase 3 must be complete (all features implemented).

### T053-T056: Runbooks

- [ ] **T053** [P] Write Runbook 1: Watcher Won't Start
  - **Files**: `docs/runbooks/watcher-wont-start.md`
  - **Content**: Symptoms (exit code 1/2/3), diagnosis steps (check vault path, handbook validation, permissions), resolution (run init_vault, fix handbook, chmod)
  - **Acceptance**: Runbook provides clear step-by-step troubleshooting
  - **Reference**: Plan section 6.3 Runbook 1
  - **Time**: 30 minutes

- [ ] **T054** [P] Write Runbook 2: Dashboard Not Updating
  - **Files**: `docs/runbooks/dashboard-not-updating.md`
  - **Content**: Symptoms (files added but dashboard unchanged), diagnosis (check watcher running, check logs, check file locks), resolution (start watcher, close Obsidian, check logs for errors)
  - **Acceptance**: Runbook covers common dashboard update issues
  - **Reference**: Plan section 6.3 Runbook 2
  - **Time**: 30 minutes

- [ ] **T055** [P] Write Runbook 3: Dashboard Corrupted
  - **Files**: `docs/runbooks/dashboard-corrupted.md`
  - **Content**: Symptoms (invalid markdown), diagnosis (open in text editor, check for malformed table), resolution (automatic recovery by watcher, manual restore from .bak)
  - **Acceptance**: Runbook explains recovery process
  - **Reference**: Plan section 6.3 Runbook 3
  - **Time**: 25 minutes

- [ ] **T056** [P] Write Runbook 4: Watcher Keeps Restarting
  - **Files**: `docs/runbooks/watcher-keeps-restarting.md`
  - **Content**: Symptoms (multiple watcher_started events), diagnosis (check logs for ERROR, check vault filesystem, check disk space), resolution (fix encoding errors, free disk space, check vault size)
  - **Acceptance**: Runbook helps diagnose crash-loop issues
  - **Reference**: Plan section 6.3 Runbook 4
  - **Time**: 30 minutes

### T057-T060: Documentation

- [ ] **T057** Create README.md with Bronze tier setup instructions
  - **Files**: `README.md`
  - **Sections**: Prerequisites (Python 3.11+, Obsidian 1.5+), Installation (`pip install -e .[dev]`), Vault Setup (`python scripts/init_vault.py ~/vault`), Start Watcher (`python scripts/watch_inbox.py ~/vault`), Testing (`pytest`), Troubleshooting (link to runbooks)
  - **Acceptance**: User can follow README to set up Bronze tier without developer assistance
  - **Reference**: Spec Definition of Done item 7, Plan section 6.4
  - **Time**: 45 minutes

- [ ] **T058** [P] Document Agent Skills API usage in README.md
  - **Files**: `README.md` (add section: "Using Agent Skills with Claude Code")
  - **Content**: Import examples, function signatures, usage examples from Spec Appendix C
  - **Acceptance**: Developers know how to use vault_watcher functions from Claude Code
  - **Reference**: Spec Appendix C
  - **Time**: 25 minutes

- [ ] **T059** [P] Add CONTRIBUTING.md with development guidelines
  - **Files**: `CONTRIBUTING.md`
  - **Content**: Git workflow (feature branches per tier), commit message format (references spec sections), code quality gates (mypy, black, pytest, 80% coverage), constitution principles
  - **Acceptance**: Contributors understand project workflow and standards
  - **Reference**: Constitution Principle V (git commit discipline)
  - **Time**: 30 minutes

- [ ] **T060** [P] Generate API documentation with pdoc
  - **Command**: `pdoc --html --output-dir docs/api agent_skills/`
  - **Acceptance**: HTML docs generated for vault_watcher.py and dashboard_updater.py
  - **Time**: 15 minutes

### T061-T064: Final Validation

- [ ] **T061** Run full test suite and verify 80%+ coverage
  - **Command**: `pytest --cov=agent_skills --cov-report=html`
  - **Acceptance**: All tests pass (unit + integration), coverage ≥80%, HTML report generated in htmlcov/
  - **Fix**: Add missing tests if coverage <80%
  - **Reference**: Spec Definition of Done item 4
  - **Time**: 15 minutes

- [ ] **T062** Run mypy type checking on all modules
  - **Command**: `mypy agent_skills/ scripts/`
  - **Acceptance**: Zero mypy errors
  - **Fix**: Add missing type hints if mypy fails
  - **Reference**: Spec Definition of Done item 8
  - **Time**: 15 minutes

- [ ] **T063** Run black formatting check
  - **Command**: `black --check agent_skills/ scripts/ tests/`
  - **Acceptance**: Zero formatting changes needed
  - **Fix**: Run `black agent_skills/ scripts/ tests/` to reformat if needed
  - **Reference**: Spec Definition of Done item 9
  - **Time**: 10 minutes

- [ ] **T064** Manual end-to-end test (user validation)
  - **Steps**: 1) Init vault (`python scripts/init_vault.py /tmp/test-vault`), 2) Start watcher (`python scripts/watch_inbox.py /tmp/test-vault`), 3) Drop test file in Inbox/, 4) Wait 30s, 5) Open vault in Obsidian, 6) Verify Dashboard.md updated and renders correctly
  - **Acceptance**: All steps work without errors, Dashboard.md displays as table in Obsidian
  - **Reference**: Spec Definition of Done item 10 (user validation)
  - **Time**: 30 minutes

### T065-T067: Process Management Setup

- [ ] **T065** [P] Create PM2 ecosystem file for Bronze tier
  - **Files**: `ecosystem.config.js`
  - **Content**: PM2 configuration for watch_inbox.py (name: "bronze-watcher", script: "python scripts/watch_inbox.py ~/vault", restart: "on-failure", max_restarts: 3)
  - **Acceptance**: `pm2 start ecosystem.config.js` starts watcher, `pm2 logs bronze-watcher` shows logs
  - **Reference**: Plan section 6.4 deployment (PM2 option)
  - **Time**: 20 minutes

- [ ] **T066** [P] Create systemd service file for Bronze tier
  - **Files**: `deploy/bronze-watcher.service`
  - **Content**: Systemd unit file (ExecStart, Restart=on-failure, User, WorkingDirectory)
  - **Instructions**: Document installation steps (`sudo cp deploy/bronze-watcher.service /etc/systemd/system/`, `sudo systemctl enable bronze-watcher`)
  - **Acceptance**: Systemd service file follows best practices, documented in README.md
  - **Reference**: Plan section 6.4 deployment (systemd option)
  - **Time**: 25 minutes

- [ ] **T067** Test 24-hour continuous operation
  - **Manual Test**: Start watcher, let run for 24 hours (or simulate with time.sleep mock), monitor memory/CPU usage, count restarts
  - **Acceptance**: Watcher uptime ≥99% (allow 15 minutes downtime), memory <100MB, CPU <5%
  - **Reference**: Spec SC-B005, Spec NFR-B-REL-001
  - **Time**: 10 minutes setup + 24 hours wait (async)

### T068-T069: Security Audit

- [ ] **T068** [P] Run security checks (no eval/exec, no network requests)
  - **Commands**: `grep -r "eval\|exec\|os.system" agent_skills/ scripts/`, `grep -r "requests\|urllib\|socket" agent_skills/ scripts/`
  - **Acceptance**: Zero matches for dangerous functions, zero matches for network libraries
  - **Reference**: Plan section 8.4 security checks
  - **Time**: 10 minutes

- [ ] **T069** [P] Test directory traversal protection
  - **Test**: Call `read_vault_file("vault", "../../etc/passwd")` → Expect ValueError
  - **Acceptance**: All path validation works, no directory traversal possible
  - **Reference**: Plan section 8.4 security checks
  - **Time**: 15 minutes

**Checkpoint Phase 4**: All tasks complete. Bronze Tier is production-ready.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundation)**: No dependencies - start immediately
  - Deliverables: Project setup, init_vault.py, vault_watcher.py, unit tests
  - Duration: ~10-12 hours
  - **BLOCKS Phase 2, 3, 4**

- **Phase 2 (Monitoring)**: Depends on Phase 1 completion
  - Deliverables: dashboard_updater.py, watch_inbox.py, integration tests
  - Duration: ~8-10 hours
  - **BLOCKS Phase 3, 4**

- **Phase 3 (Validation)**: Depends on Phase 2 completion
  - Deliverables: Handbook validation, edge case handling
  - Duration: ~4-6 hours
  - **BLOCKS Phase 4**

- **Phase 4 (Polish)**: Depends on Phase 3 completion
  - Deliverables: Runbooks, README, final validation, process management
  - Duration: ~6-8 hours

### Total Estimated Time: 28-36 hours (conservative estimate with buffer)

### Parallel Opportunities

**Phase 1 Parallel Tasks**:
- T001-T005: All setup tasks can run in parallel (5 tasks)
- T011-T014: All vault_watcher.py functions can be implemented in parallel (4 tasks)
- T016-T020: All vault_watcher unit tests can be written in parallel (5 tasks)

**Phase 2 Parallel Tasks**:
- T030-T032: All dashboard_updater unit tests can be written in parallel (3 tasks)

**Phase 4 Parallel Tasks**:
- T053-T056: All runbooks can be written in parallel (4 tasks)
- T058-T060: Documentation tasks can run in parallel (3 tasks)
- T065-T066: Process management files can be created in parallel (2 tasks)
- T068-T069: Security checks can run in parallel (2 tasks)

### Recommended Execution Strategy

**Single Developer (Sequential)**:
1. Complete Phase 1 tasks T001-T022 (foundation)
2. Complete Phase 2 tasks T023-T044 (monitoring)
3. Complete Phase 3 tasks T045-T052 (validation)
4. Complete Phase 4 tasks T053-T069 (polish)

**Two Developers (Parallel)**:
- Dev A: Phase 1 foundation (T001-T022)
- Dev B: Wait for Phase 1 → Phase 2 monitoring (T023-T044)
- Both: Phase 3 validation (split tasks)
- Both: Phase 4 polish (split documentation tasks)

---

## Task Summary

**Total Tasks**: 69 tasks
- Phase 1 (Foundation): 22 tasks (T001-T022)
- Phase 2 (Monitoring): 22 tasks (T023-T044)
- Phase 3 (Validation): 8 tasks (T045-T052)
- Phase 4 (Polish): 17 tasks (T053-T069)

**User Story Mapping**:
- US1 (Vault Initialization): T006-T010 (5 tasks)
- US2 (Inbox Detection): T035-T041, T042-T044 (10 tasks)
- US3 (Dashboard Updates): T023-T034, T042-T044 (15 tasks)
- US4 (Handbook Validation): T045-T048 (4 tasks)
- US5 (Agent Skills API): T011-T022 (12 tasks)
- Setup & Polish: T001-T005, T049-T069 (23 tasks)

**Parallel Tasks**: 35 tasks marked [P] can run in parallel (50% of tasks)

**Test Tasks**: 28 tasks are test-related (unit tests, integration tests, coverage verification)

---

## Notes

- All tasks reference specific files, functions, and acceptance criteria
- Tasks are ordered by dependency (foundation → monitoring → validation → polish)
- Constitution compliance: Git commit messages must reference spec sections (e.g., "Implements US-1: Vault initialization (spec: bronze-tier/spec.md#US-1)")
- Stop at any phase checkpoint to validate independently
- 80% test coverage is non-negotiable (constitution requirement)
- Mypy and black checks are quality gates (must pass before PR merge)

---

**Next Step**: Start Phase 1 (Foundation) with T001-T005 (project setup). Once setup complete, implement vault_watcher.py functions T011-T014 in parallel.
