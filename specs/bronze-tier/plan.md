# Implementation Plan: Bronze Tier - Foundation AI Employee

**Branch**: `bronze-tier` | **Date**: 2026-02-10 | **Spec**: [specs/bronze-tier/spec.md](./spec.md)
**Input**: Feature specification from `/specs/bronze-tier/spec.md`

## Summary

Bronze Tier establishes the foundational layer of the Personal AI Employee system. This tier implements a **local-first vault monitoring system** that detects new markdown files in an Obsidian vault and maintains an up-to-date dashboard. The system operates 100% offline with zero autonomous actions - all operations are read-heavy with minimal, atomic writes to Dashboard.md.

**Primary Requirement**: Monitor vault/Inbox/ for new .md files and update Dashboard.md within 2 seconds while preserving vault integrity.

**Technical Approach**: Event-driven polling architecture using Python watchdog library with atomic file writes, backup strategy, and corruption recovery mechanisms. All functionality exposed via Agent Skills API for Claude Code integration.

## Technical Context

**Language/Version**: Python 3.11+ (use pathlib, type hints, dataclasses)
**Primary Dependencies**:
- `watchdog>=3.0.0` (file system monitoring)
- `pyyaml>=6.0` (YAML parsing for handbook validation)
**Storage**: Local filesystem only (vault/ directory with Obsidian markdown files)
**Testing**: pytest 7.0+, pytest-cov 4.0+ (target: 80% coverage)
**Target Platform**: WSL Ubuntu 22.04+ (primary), macOS 13+, Windows 11 (secondary)
**Project Type**: Single project (agent_skills/ modules + scripts/ entry points)
**Performance Goals**:
- Dashboard update: <2 seconds from file detection to completion
- File read operations: <500ms for files up to 100KB
- Polling cycle: 30 seconds (configurable)
- Vault support: Up to 1000 markdown files
**Constraints**:
- 100% offline operation (zero network requests)
- Atomic file writes only (no partial updates)
- Read-only access except Dashboard.md and Logs/
- No code execution from vault contents
- Obsidian markdown syntax preservation (YAML frontmatter, wiki links, tags)
**Scale/Scope**:
- 5 vault folders (Inbox/, Needs_Action/, Done/, Plans/, Logs/)
- 4 Python modules (init_vault, watch_inbox, dashboard_updater, vault_watcher)
- 4 Agent Skills API functions (read, list, summary, validate)
- 25 functional requirements, 18 non-functional requirements

## Constitution Check

*GATE: Must pass before implementation. Aligned with constitution principles.*

✅ **Vault Integrity First (Principle II)**:
- Atomic file operations: read → validate → modify → validate → write
- Dashboard.md backups before every update (Dashboard.md.bak.TIMESTAMP)
- Corruption detection and automatic recovery from .bak files
- File lock handling with retry logic (no forced overwrites)

✅ **Local-First Architecture (Principle III)**:
- Bronze tier: 100% offline, zero external API calls
- All data persists in vault/ folder (no external databases)
- Configuration in Company_Handbook.md (human-editable markdown)

✅ **Test-Driven Safety (Principle IV)**:
- Pytest unit tests for every agent skill function (80% coverage target)
- Integration test: Drop file → Detect → Update → Query
- Idempotency tests (running watcher multiple times = same output)

✅ **Incremental Development (Principle V)**:
- Bronze tier is foundation (monitoring only)
- No Silver tier features (AI analysis, autonomous actions)
- Clear separation: .specify/ (dev), vault/ (product), agent_skills/ (reusable), scripts/ (entry points)

✅ **Code Organization (Principle VI)**:
- agent_skills/: Reusable Python modules (vault_watcher.py, dashboard_updater.py)
- scripts/: Entry points (init_vault.py, watch_inbox.py)
- tests/: Pytest suite (unit/, integration/)
- vault/: Product deliverable (Obsidian-compatible markdown only)

✅ **Performance Requirements**:
- Bronze watcher: 30-second polling interval (per constitution)
- Dashboard updates: <2 seconds (measurable target)
- Vault support: 1000 files (Bronze tier limit per constitution)

**Constitution Alignment**: PASS - All principles satisfied, no exceptions required.

## Project Structure

### Documentation (this feature)

```text
specs/bronze-tier/
├── spec.md              # Feature specification (already created)
├── plan.md              # This file (implementation architecture)
└── tasks.md             # Implementation tasks (created via /sp.tasks)

.specify/memory/
└── constitution.md      # Development principles (already exists)

history/prompts/bronze-tier/
├── 001-bronze-tier-specification.spec.prompt.md
└── 002-bronze-tier-implementation-plan.plan.prompt.md
```

### Source Code (repository root)

```text
agent_skills/                        # Reusable Python modules
├── __init__.py                      # Package initialization
├── vault_watcher.py                 # Agent Skills API (4 functions)
│   ├── read_vault_file()            # Read markdown file
│   ├── list_vault_folder()          # List .md files in folder
│   ├── get_dashboard_summary()      # Parse Dashboard.md → dict
│   └── validate_handbook()          # Check handbook sections
└── dashboard_updater.py             # Dashboard.md manipulation
    ├── update_dashboard()           # Atomic update with backup
    ├── create_backup()              # Timestamp-based backups
    ├── restore_from_backup()        # Corruption recovery
    └── parse_dashboard()            # Extract current state

scripts/                             # Entry points (not importable)
├── init_vault.py                    # One-time vault setup
│   ├── create_folder_structure()    # 5 folders
│   ├── create_dashboard()           # Dashboard.md template
│   └── create_handbook()            # Company_Handbook.md template
└── watch_inbox.py                   # Continuous monitoring
    ├── main()                       # Entry point with signal handling
    ├── poll_inbox()                 # 30-second polling loop
    ├── detect_new_files()           # Filter .md files, ignore locks
    └── log_event()                  # Write to vault/Logs/watcher-DATE.md

tests/                               # Pytest test suite
├── unit/                            # Unit tests (agent_skills/)
│   ├── test_vault_watcher.py        # Test 4 API functions
│   └── test_dashboard_updater.py    # Test atomic writes, backups
├── integration/                     # Integration tests
│   └── test_end_to_end.py           # Drop file → Detect → Update → Query
└── fixtures/                        # Test data
    ├── sample_vault/                # Mock vault for testing
    └── corrupted_dashboard.md       # Test recovery logic

vault/                               # Product deliverable (Obsidian vault)
├── Inbox/                           # User drops tasks here (monitored)
├── Needs_Action/                    # Manual move (Bronze tier)
├── Done/                            # Manual move (Bronze tier)
├── Plans/                           # Reserved for Silver+ tiers
├── Logs/                            # System-generated logs
│   └── watcher-YYYY-MM-DD.md        # Daily log file
├── Dashboard.md                     # Auto-maintained task table
└── Company_Handbook.md              # Human-editable configuration
```

**Structure Decision**: Single project structure chosen because Bronze tier is a self-contained monitoring system with no web/mobile components. The `agent_skills/` modules are reusable libraries, while `scripts/` provides entry points for vault initialization and monitoring. This aligns with constitution principle VI (Code Organization & Modularity).

## Complexity Tracking

> **No complexity violations detected**. Bronze tier follows all constitution principles without exceptions.

## 1. Scope and Dependencies

### In Scope

**Core Functionality**:
- Vault initialization with 5 folders and 2 template files (Dashboard.md, Company_Handbook.md)
- File watcher polling vault/Inbox/ every 30 seconds for new .md files
- Dashboard.md updates within 2 seconds of file detection (atomic writes with backups)
- Agent Skills API with 4 functions for Claude Code integration
- Company_Handbook.md validation on watcher startup (5 required sections)
- Logging all events to vault/Logs/watcher-YYYY-MM-DD.md
- Error handling: file locks (retry), Dashboard corruption (restore from .bak), invalid encoding (skip file)

**Boundaries**:
- Monitoring only (no autonomous actions)
- 100% offline (no network requests)
- Read-only access except Dashboard.md and Logs/
- Support up to 1000 markdown files (Bronze tier limit)

### Out of Scope

**Deferred to Silver Tier**:
- AI-powered priority analysis (Claude API)
- Automatic file movement between folders
- Plan.md generation (Claude reasoning loop)
- Email/WhatsApp watcher integration

**Deferred to Gold+ Tiers**:
- Multi-step plan execution
- External API integrations (email, calendar, social media)
- Business audit and CEO briefing generation
- Reflection loops and autonomous error correction

**Never in Bronze (Safety Boundaries)**:
- Autonomous file deletion
- Code execution from vault files
- Network requests of any kind

### External Dependencies

**Python Packages** (managed via pyproject.toml):
- `watchdog>=3.0.0`: File system event monitoring (uses Observer pattern)
- `pyyaml>=6.0`: YAML parsing for Company_Handbook.md validation

**Development Dependencies**:
- `pytest>=7.0`: Unit testing framework
- `pytest-cov>=4.0`: Code coverage reporting
- `black>=23.0`: Code formatting (enforce PEP 8)
- `mypy>=1.0`: Static type checking

**External Tools** (user-installed):
- Obsidian Desktop App v1.5+ (specifically tested with v1.11.7)
- Python 3.11+ (pathlib, type hints, dataclasses)
- Git (optional but recommended for version control)

**System Dependencies**:
- Filesystem access to vault/ directory (read/write permissions)
- At least 8GB RAM (watcher process uses <100MB)
- At least 1GB disk space (vault with 1000 markdown files)

### Dependency Ownership

| Dependency | Owner | Risk Level | Mitigation |
|------------|-------|------------|------------|
| watchdog | External (PyPI) | Low | Stable library (10+ years), pinned version >=3.0.0 |
| pyyaml | External (PyPI) | Low | Standard library, widely used, pinned version >=6.0 |
| Obsidian | External (user) | Medium | No proprietary plugins required, use standard markdown only |
| Python 3.11+ | External (user) | Low | LTS version, widely available on all platforms |

## 2. Key Decisions and Rationale

### Decision 1: Polling vs. Real-Time Event Monitoring

**Options Considered**:
1. **Polling** (watchdog in polling mode): Check vault/Inbox/ every 30 seconds
2. **Real-time events** (watchdog in event mode): Trigger immediately on file system changes
3. **Hybrid**: Event-driven with debouncing (collect events for 5 seconds, then batch process)

**Trade-offs**:
- **Polling**: Simpler implementation, lower CPU usage, predictable behavior, 30-second delay
- **Real-time**: Instant detection, higher CPU usage, complex event handling (rapid-fire events, lock conflicts)
- **Hybrid**: Best of both worlds, but increased complexity for Bronze tier

**Decision**: **Polling with 30-second interval** (Option 1)

**Rationale**:
- Constitution principle: Bronze tier watcher uses 30-second polling for lower CPU usage
- Simplicity: Bronze is foundation tier, prefer simple over complex
- Predictable: Users understand "checks every 30 seconds" better than event-driven behavior
- Sufficient: 30-second delay is acceptable for task management workflows
- Measurable: Easy to verify in tests (drop file, wait 30s, check log)

**Reversible**: Silver tier can upgrade to event-driven if needed (watchdog supports both modes)

---

### Decision 2: Dashboard Update Strategy - Atomic Writes with Backups

**Options Considered**:
1. **Direct write**: Open Dashboard.md, modify, save (no backup)
2. **Append-only log**: Never modify Dashboard.md, only append new entries (chronological)
3. **Atomic write with backup**: Write to temp file → backup original → rename temp to Dashboard.md

**Trade-offs**:
- **Direct write**: Simplest, but risk of corruption on power loss or Obsidian lock
- **Append-only**: No corruption risk, but Dashboard.md grows unbounded, hard to parse
- **Atomic with backup**: More complex, but guarantees data integrity and recovery

**Decision**: **Atomic write with backup** (Option 3)

**Rationale**:
- Constitution principle II: Vault Integrity First - never corrupt user data
- Atomic rename is OS-level operation (POSIX guarantees atomicity)
- Backup with timestamp (Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS) enables recovery
- Spec requirement FR-B008: MUST create backup before every update
- Spec requirement FR-B020: MUST detect corruption and restore from .bak
- Testable: Integration tests can simulate power loss (partial write) and verify recovery

**Reversible**: No, this is a safety requirement (non-negotiable per constitution)

---

### Decision 3: Agent Skills API Design - Pure Functions vs. Stateful Class

**Options Considered**:
1. **Pure functions**: Module-level functions (no class), pass vault_path as parameter
2. **Stateful class**: VaultWatcher class with vault_path in __init__, methods operate on self
3. **Singleton pattern**: Global VaultWatcher instance, initialize once, import everywhere

**Trade-offs**:
- **Pure functions**: Simple, testable, explicit dependencies (vault_path always passed)
- **Stateful class**: Encapsulation, but harder to test (need to mock __init__)
- **Singleton**: Hidden global state, hard to test (can't test with multiple vaults)

**Decision**: **Pure functions with vault_path parameter** (Option 1)

**Rationale**:
- Testability: Unit tests can call functions with test fixture paths (no mocking needed)
- Simplicity: Functions are easier to understand than classes for Bronze tier
- Claude Code integration: Functions are more natural to call from agent context
- Spec requirement FR-B013 to FR-B016: Functions specified, not class methods
- Example from spec Appendix C shows function imports (not class instantiation)

**Reversible**: Yes, Silver tier can introduce VaultContext class if stateful operations needed

---

### Decision 4: Error Handling - Graceful Degradation vs. Fail-Fast

**Options Considered**:
1. **Fail-fast**: Watcher exits on any error (file lock, corruption, encoding error)
2. **Graceful degradation**: Log error, skip problematic file, continue monitoring
3. **Retry with exponential backoff**: Retry failed operations up to 3 times, then skip

**Trade-offs**:
- **Fail-fast**: Simplest, but requires manual restart (poor user experience)
- **Graceful degradation**: Keeps watcher running, but may silently skip important files
- **Retry with backoff**: Best reliability, but complexity for Bronze tier

**Decision**: **Graceful degradation with immediate retry on next cycle** (Option 2)

**Rationale**:
- NFR-B-REL-001: Watcher uptime MUST be 99% over 24 hours
- Spec edge case: "Obsidian file locks → Retry on next polling cycle, don't crash"
- Bronze tier simplicity: Immediate retry (next 30s cycle) is sufficient
- User awareness: All errors logged to vault/Logs/watcher-DATE.md (human can investigate)
- Measurable: Integration tests verify watcher continues after file lock error

**Silver Tier Upgrade**: Can add exponential backoff for persistent failures if needed

---

### Decision 5: Company_Handbook.md Validation - Startup Only vs. Continuous

**Options Considered**:
1. **Startup only**: Validate on watcher start, never re-validate during runtime
2. **Continuous**: Re-validate every time handbook is modified (watchdog event)
3. **Periodic**: Re-validate every 5 minutes (in case user edits while watcher running)

**Trade-offs**:
- **Startup only**: Simplest, but stale validation if user edits handbook
- **Continuous**: Most accurate, but adds complexity (watch additional file)
- **Periodic**: Balanced, but arbitrary interval (why 5 minutes?)

**Decision**: **Startup only for Bronze, with manual re-validation command** (Option 1)

**Rationale**:
- Bronze tier simplicity: Minimize moving parts (only watch Inbox/, not handbook)
- User workflow: Handbook edits are rare (initial setup, then stable)
- Manual override: User can restart watcher to re-validate if handbook changed
- Spec US-4: Validation on watcher startup (no requirement for continuous validation)
- Silver tier upgrade path: Can add continuous validation when adding more watchers

**Reversible**: Yes, Silver tier can add handbook file watcher if needed

---

### Principles Applied Across All Decisions

1. **Measurable**: All decisions have testable outcomes (polling interval, atomic writes, error recovery)
2. **Reversible**: Most decisions can be upgraded in Silver tier (polling → events, pure functions → classes)
3. **Smallest viable change**: Choose simplest option that meets spec requirements
4. **Constitution-aligned**: All decisions prioritize vault integrity, local-first operation, test-driven safety

## 3. Interfaces and API Contracts

### 3.1 Agent Skills API (vault_watcher.py)

**Purpose**: Expose vault data to Claude Code for interactive queries.

**Contract Guarantees**:
- Pure functions (no side effects)
- Synchronous execution (no async/await in Bronze)
- Raise exceptions for invalid input (no silent failures)
- Return types match docstrings (enforced by mypy)

#### Function: read_vault_file

```python
def read_vault_file(vault_path: str, filepath: str) -> str:
    """Read markdown file from vault.

    Args:
        vault_path: Absolute path to vault root directory
        filepath: Relative path from vault root (e.g., "Inbox/task.md")

    Returns:
        File content as UTF-8 string

    Raises:
        FileNotFoundError: If file doesn't exist at vault_path/filepath
        PermissionError: If file is locked by Obsidian (unreadable)
        UnicodeDecodeError: If file is not valid UTF-8 encoding
        ValueError: If filepath attempts directory traversal (e.g., "../etc/passwd")

    Example:
        >>> content = read_vault_file("/path/to/vault", "Inbox/task.md")
        >>> print(content[:50])
        # Task: Review Proposal

        Due: 2026-02-15

    Performance:
        - <500ms for files up to 100KB (NFR-B-PERF-002)
        - Fail fast if file > 10MB (log warning, raise ValueError)
    """
```

**Error Taxonomy**:
- `FileNotFoundError` (404): File doesn't exist → User should check filepath
- `PermissionError` (403): File locked by Obsidian → Retry after closing Obsidian
- `UnicodeDecodeError` (422): Invalid encoding → User should save file as UTF-8
- `ValueError` (400): Invalid input (directory traversal, absolute path) → Fix caller

**Idempotency**: Yes (pure read operation, no side effects)

**Versioning**: Bronze tier is v0.1.0. If signature changes (e.g., add `encoding` parameter in Silver), bump to v0.2.0.

---

#### Function: list_vault_folder

```python
def list_vault_folder(vault_path: str, folder_name: str) -> list[str]:
    """List all .md files in a vault folder (non-recursive).

    Args:
        vault_path: Absolute path to vault root directory
        folder_name: One of ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]

    Returns:
        List of filenames (not full paths), sorted alphabetically.
        Example: ["2026-02-10-task1.md", "2026-02-11-task2.md"]

    Raises:
        FileNotFoundError: If folder doesn't exist at vault_path/folder_name
        ValueError: If folder_name is not one of the 5 allowed folders
        PermissionError: If folder is not readable

    Example:
        >>> files = list_vault_folder("/path/to/vault", "Inbox")
        >>> print(files)
        ["2026-02-10-review-proposal.md", "2026-02-11-fix-bug.md"]

    Performance:
        - <100ms for folders with up to 1000 files (Bronze limit)
        - Fail fast if folder contains >1000 files (log warning, raise ValueError)

    Notes:
        - Filters: Only .md files (ignore .txt, .png, .obsidian/, .git/)
        - Non-recursive: Does not scan subfolders
        - Sorted: Alphabetical order (consistent output for testing)
    """
```

**Validation Rules**:
- `folder_name` must be one of: `["Inbox", "Needs_Action", "Done", "Plans", "Logs"]`
- `vault_path` must be absolute path (no relative paths like `../vault`)
- Folder must exist and be readable

---

#### Function: get_dashboard_summary

```python
def get_dashboard_summary(vault_path: str) -> dict[str, int]:
    """Parse Dashboard.md and return task counts by status.

    Args:
        vault_path: Absolute path to vault root directory

    Returns:
        Dictionary with task counts:
        {
            "total": 5,
            "inbox": 2,
            "needs_action": 2,
            "done": 1
        }

    Raises:
        FileNotFoundError: If Dashboard.md doesn't exist at vault_path
        ValueError: If Dashboard.md is corrupted (invalid markdown table)

    Example:
        >>> summary = get_dashboard_summary("/path/to/vault")
        >>> print(f"You have {summary['inbox']} tasks in Inbox")
        You have 2 tasks in Inbox

    Performance:
        - <200ms for dashboards with up to 1000 tasks (Bronze limit)

    Notes:
        - Parses markdown table (columns: Filename, Date Added, Status, Priority)
        - Case-insensitive status matching ("Inbox" == "inbox" == "INBOX")
        - Ignores invalid rows (logs warning, continues parsing)
        - If Dashboard.md is empty, returns {"total": 0, "inbox": 0, ...}
    """
```

**Parsing Strategy**:
1. Read Dashboard.md content
2. Find markdown table (starts with `| Filename | Date Added | Status | Priority |`)
3. Extract rows (skip header and separator `|---|---|---|---|`)
4. Parse Status column (3rd column), count by status
5. Return counts dictionary

**Error Recovery**:
- If table not found → Return all zeros ({"total": 0, "inbox": 0, "needs_action": 0, "done": 0})
- If row is malformed (missing columns) → Skip row, log warning, continue
- If Dashboard.md is corrupted → Raise ValueError with helpful message ("Dashboard.md is corrupted, run restore_from_backup()")

---

#### Function: validate_handbook

```python
def validate_handbook(vault_path: str) -> tuple[bool, list[str]]:
    """Check if Company_Handbook.md has all required sections.

    Args:
        vault_path: Absolute path to vault root directory

    Returns:
        Tuple of (is_valid, missing_sections):
        - is_valid: True if all 5 required sections present, False otherwise
        - missing_sections: List of missing section names (empty if is_valid=True)

    Raises:
        FileNotFoundError: If Company_Handbook.md doesn't exist at vault_path

    Example:
        >>> is_valid, missing = validate_handbook("/path/to/vault")
        >>> if not is_valid:
        ...     print(f"Handbook missing sections: {', '.join(missing)}")
        Handbook missing sections: Escalation Rules, Bronze Tier Limitations

    Required Sections (case-insensitive):
        1. "File Naming Convention"
        2. "Folder Usage Guidelines"
        3. "Forbidden Operations (Bronze Tier)" or "Forbidden Operations"
        4. "Escalation Rules"
        5. "Bronze Tier Limitations"

    Notes:
        - Uses markdown header detection (lines starting with ## or ###)
        - Fuzzy matching: "Escalation Rules" matches "## 4. Escalation Rules"
        - YAML frontmatter: Parsed with pyyaml, but not validated (Bronze tier)
        - Malformed YAML: Logs warning, continues with section validation
    """
```

**Validation Algorithm**:
1. Read Company_Handbook.md content
2. Extract all markdown headers (lines matching `^##+ (.+)$`)
3. For each required section, check if any header contains the section name (case-insensitive substring match)
4. Return (True, []) if all found, else (False, [list of missing sections])

**YAML Frontmatter Handling**:
- If YAML frontmatter exists (`---\n...\n---`), parse with pyyaml
- If parsing fails (malformed YAML), log warning and continue (graceful degradation)
- Bronze tier does not validate YAML content (just check it parses)

---

### 3.2 Dashboard Updater API (dashboard_updater.py)

**Purpose**: Atomic Dashboard.md updates with backup and recovery.

#### Function: update_dashboard

```python
def update_dashboard(
    vault_path: str,
    new_files: list[tuple[str, str]],  # [(filename, status), ...]
) -> bool:
    """Update Dashboard.md with new tasks (atomic write with backup).

    Args:
        vault_path: Absolute path to vault root directory
        new_files: List of (filename, status) tuples to add to dashboard
            - filename: Relative path from vault root (e.g., "Inbox/task.md")
            - status: One of ["Inbox", "Needs Action", "Done"]

    Returns:
        True if update successful, False if failed (check logs for details)

    Raises:
        ValueError: If any status is invalid (not in allowed list)
        PermissionError: If vault_path is not writable

    Example:
        >>> success = update_dashboard(
        ...     "/path/to/vault",
        ...     [("Inbox/task1.md", "Inbox"), ("Inbox/task2.md", "Inbox")]
        ... )
        >>> print("Updated" if success else "Failed")
        Updated

    Performance:
        - <2 seconds from function call to completion (NFR-B-PERF-001)

    Algorithm:
        1. Create backup: Dashboard.md → Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS
        2. Parse current Dashboard.md (extract existing tasks)
        3. Append new tasks to table (with Date Added = current timestamp)
        4. Recalculate statistics (Total, Inbox, Needs Action, Done counts)
        5. Write to temp file: Dashboard.md.tmp
        6. Validate temp file (check markdown table is valid)
        7. Atomic rename: Dashboard.md.tmp → Dashboard.md
        8. Return True (or False if any step fails)

    Notes:
        - Priority defaults to "Medium" for Bronze tier (no AI analysis)
        - Preserves existing Dashboard.md content (header, custom sections)
        - If Dashboard.md doesn't exist, creates from template
        - If update fails at any step, Dashboard.md remains unchanged (backup preserved)
    """
```

**Atomic Write Algorithm**:
```python
# Pseudocode for atomic update
def update_dashboard(vault_path, new_files):
    dashboard_path = Path(vault_path) / "Dashboard.md"
    temp_path = Path(vault_path) / "Dashboard.md.tmp"

    # Step 1: Backup
    backup_path = create_backup(dashboard_path)

    try:
        # Step 2: Parse existing
        existing_tasks = parse_dashboard(dashboard_path)

        # Step 3: Merge new tasks
        all_tasks = existing_tasks + [
            {"filename": f, "status": s, "date_added": now(), "priority": "Medium"}
            for f, s in new_files
        ]

        # Step 4: Render markdown table
        markdown_content = render_dashboard(all_tasks)

        # Step 5: Write to temp
        temp_path.write_text(markdown_content, encoding="utf-8")

        # Step 6: Validate temp file
        validate_dashboard(temp_path)

        # Step 7: Atomic rename (POSIX guarantees atomicity)
        temp_path.replace(dashboard_path)

        return True
    except Exception as e:
        logger.error(f"Dashboard update failed: {e}")
        # Dashboard.md remains unchanged, backup preserved
        return False
```

**Error Handling**:
- If backup creation fails → Log error, abort update, return False
- If parse fails (Dashboard.md corrupted) → Restore from backup, log recovery, retry update
- If validation fails (temp file invalid) → Delete temp file, Dashboard.md unchanged, return False
- If atomic rename fails (permissions) → Log error, Dashboard.md unchanged, return False

---

#### Function: restore_from_backup

```python
def restore_from_backup(vault_path: str, backup_filename: str = None) -> bool:
    """Restore Dashboard.md from most recent .bak file.

    Args:
        vault_path: Absolute path to vault root directory
        backup_filename: Optional specific backup to restore (default: most recent)

    Returns:
        True if restore successful, False if no backups found or restore failed

    Example:
        >>> # Restore from most recent backup
        >>> restore_from_backup("/path/to/vault")
        True
        >>> # Restore from specific backup
        >>> restore_from_backup("/path/to/vault", "Dashboard.md.bak.2026-02-10_15-30-00")
        True

    Algorithm:
        1. List all .bak files: Dashboard.md.bak.*
        2. Sort by timestamp (newest first)
        3. Copy backup_filename (or most recent) → Dashboard.md.tmp
        4. Validate Dashboard.md.tmp (check markdown table)
        5. Atomic rename: Dashboard.md.tmp → Dashboard.md
        6. Log restoration event to vault/Logs/watcher-DATE.md
    """
```

---

### 3.3 Watcher Entry Point (scripts/watch_inbox.py)

**Purpose**: Continuous monitoring of vault/Inbox/ with 30-second polling.

#### Function: main

```python
def main(vault_path: str, config: dict = None) -> None:
    """Entry point for inbox file watcher.

    Args:
        vault_path: Absolute path to vault root directory
        config: Optional configuration overrides (polling_interval, log_level)

    Raises:
        FileNotFoundError: If vault_path doesn't exist or is not a valid vault
        ValueError: If Company_Handbook.md validation fails (missing required sections)

    Lifecycle:
        1. Validate vault structure (5 folders exist)
        2. Validate Company_Handbook.md (5 required sections)
        3. Initialize logging (vault/Logs/watcher-YYYY-MM-DD.md)
        4. Start polling loop (every 30 seconds)
        5. On SIGINT/SIGTERM → Graceful shutdown (log "Watcher stopped")

    Signal Handling:
        - SIGINT (Ctrl+C): Graceful shutdown, log final state, exit 0
        - SIGTERM: Graceful shutdown, log final state, exit 0
        - SIGHUP: Re-validate handbook, log reload, continue monitoring
    """
```

**Polling Loop Algorithm**:
```python
def poll_inbox(vault_path):
    while True:
        try:
            # Detect new files
            new_files = detect_new_files(vault_path)

            if new_files:
                # Log detection
                log_event("file_detected", new_files)

                # Update dashboard
                success = update_dashboard(vault_path, new_files)

                if success:
                    log_event("dashboard_updated", new_files)
                else:
                    log_event("dashboard_update_failed", new_files)

        except Exception as e:
            # Graceful degradation: log error, continue monitoring
            log_event("error", str(e))

        # Sleep until next cycle
        time.sleep(POLLING_INTERVAL)
```

---

### 3.4 Vault Initialization (scripts/init_vault.py)

**Purpose**: One-time vault setup (5 folders + 2 template files).

#### Function: main

```python
def main(vault_path: str, overwrite: bool = False) -> None:
    """Initialize Bronze tier vault structure.

    Args:
        vault_path: Absolute path for new vault directory
        overwrite: If True, recreate folders/files even if they exist

    Raises:
        FileExistsError: If vault_path already exists and overwrite=False
        PermissionError: If vault_path parent directory is not writable

    Algorithm:
        1. Create vault_path directory (mkdir -p)
        2. Create 5 subfolders: Inbox/, Needs_Action/, Done/, Plans/, Logs/
        3. Create Dashboard.md from template (empty task table)
        4. Create Company_Handbook.md from template (5 required sections)
        5. Log initialization to stdout (no vault/Logs yet)

    Example:
        >>> init_vault("/home/user/my-vault")
        Vault initialized at /home/user/my-vault
        Ready to use with Obsidian
    """
```

---

### 3.5 Logging Format (vault/Logs/watcher-YYYY-MM-DD.md)

**Purpose**: Human-readable event log for watcher operations.

**Format**:
```markdown
---
date: 2026-02-10
watcher_version: 0.1.0
---

# Watcher Log - 2026-02-10

## 15:30:00 - Watcher Started
- Vault path: /home/user/vault
- Polling interval: 30 seconds
- Handbook validation: PASS

## 15:30:45 - File Detected
- File: Inbox/2026-02-10-review-proposal.md
- Size: 1.2 KB
- Encoding: UTF-8

## 15:30:47 - Dashboard Updated
- New tasks: 1
- Total tasks: 5
- Update time: 1.8 seconds

## 15:31:15 - File Detected
- File: Inbox/2026-02-10-fix-bug.md
- Size: 850 bytes
- Encoding: UTF-8

## 15:31:17 - Dashboard Updated
- New tasks: 1
- Total tasks: 6
- Update time: 1.5 seconds

## 16:00:00 - Error
- Event: File lock detected
- File: Inbox/2026-02-10-locked-file.md
- Action: Skipped (will retry next cycle)

## 18:00:00 - Watcher Stopped
- Reason: SIGINT received
- Uptime: 2 hours 30 minutes
- Total files processed: 12
```

**Log Rotation**: New file created daily (watcher-YYYY-MM-DD.md). Old logs retained for 7 days (pruned on watcher startup).

---

### 3.6 Error Codes and Status Codes

**Exit Codes (scripts/watch_inbox.py)**:
- `0`: Graceful shutdown (SIGINT, SIGTERM)
- `1`: Invalid vault path (doesn't exist or not a valid vault)
- `2`: Handbook validation failed (missing required sections)
- `3`: Filesystem permission error (vault not writable)

**API Return Codes (boolean functions)**:
- `True`: Operation successful
- `False`: Operation failed (check logs for details)

**Exception Types**:
- `FileNotFoundError`: File or directory doesn't exist
- `PermissionError`: Filesystem permission denied
- `ValueError`: Invalid input (e.g., invalid folder name, corrupted data)
- `UnicodeDecodeError`: File encoding error (not UTF-8)

## 4. Non-Functional Requirements (NFRs) and Budgets

### 4.1 Performance Budgets

| Metric | Target | Measurement Method | Acceptance Test |
|--------|--------|-------------------|-----------------|
| Dashboard update time | <2 seconds | Time from `update_dashboard()` call to completion | Drop file, measure time until Dashboard.md written |
| File read operation | <500ms | Time to execute `read_vault_file()` for 100KB file | Unit test with 100KB fixture file |
| Polling cycle | 30 seconds | Time between `poll_inbox()` iterations | Integration test with time.sleep() mock |
| Vault scan time | <5 seconds | Time to list 1000 files in vault | Integration test with 1000-file fixture |
| Memory usage | <100MB | Python process RSS (Resident Set Size) | Monitor with `ps aux` during 24-hour run |
| CPU usage | <5% average | Python process CPU percentage | Monitor with `top` during 24-hour run |

**Performance Test Plan**:
1. **Load test**: Create vault with 1000 markdown files, measure polling cycle time
2. **Stress test**: Add 50 files to Inbox/ simultaneously, measure dashboard update time
3. **Endurance test**: Run watcher for 24 hours, measure memory/CPU usage every hour

**Performance Regression Detection**:
- Run performance tests before every PR merge
- Fail build if any metric exceeds target by >10%
- Track metrics over time (performance dashboard in CI)

---

### 4.2 Reliability Budgets

| Metric | Target | Measurement Method | Recovery Strategy |
|--------|--------|-------------------|-------------------|
| Watcher uptime | 99% over 24 hours | Monitor process with watchdog script | Auto-restart on crash (systemd or PM2) |
| Dashboard integrity | 100% (zero corruption) | Validate Dashboard.md after every update | Restore from .bak on corruption detection |
| Idempotency | 100% (same output on re-run) | Compare Dashboard.md before/after re-run | Fix update algorithm if non-deterministic |
| Error recovery time | <30 seconds | Time from error detection to recovery | Retry on next polling cycle |

**Error Budget**: Allow 15 minutes of downtime per 24 hours (99% uptime = 14.4 minutes downtime)

**Monitoring Strategy**:
- Health check: Watcher writes "heartbeat" to vault/Logs every 30 seconds
- Watchdog script: Check heartbeat timestamp, restart if >60 seconds old
- User notification: Log warning to vault/Logs if watcher auto-restarted

---

### 4.3 Security Budgets

| Requirement | Enforcement | Test Method |
|-------------|-------------|-------------|
| Zero network requests | Code review + network monitoring | Run watcher with `tcpdump`, verify zero packets |
| Filesystem access limited to vault/ | Path validation in all functions | Unit test with `../etc/passwd`, expect ValueError |
| No code execution from vault | Static analysis (no `eval()`, `exec()`) | Grep codebase for dangerous functions |
| Read-only except Dashboard.md and Logs/ | Permission checks before write | Unit test: attempt write to Inbox/, expect PermissionError |

**Security Test Plan**:
- **Penetration test**: Attempt directory traversal (`read_vault_file("../../etc/passwd")`) → Expect ValueError
- **Fuzz test**: Pass random strings to all API functions → Expect no crashes, only documented exceptions
- **Network isolation test**: Run watcher in container with no network access → Verify full functionality

---

### 4.4 Cost Budgets

**Bronze Tier is 100% free (no API costs)**:
- No Claude API calls (AI analysis deferred to Silver tier)
- No cloud services (local-first architecture)
- No third-party SaaS (Obsidian is free desktop app)

**Development Costs**:
- Developer time: 8-12 hours (per spec estimate)
- Testing time: 2-4 hours (unit tests, integration tests, manual verification)
- Code review time: 1-2 hours

**Operational Costs**:
- Compute: <0.1 CPU cores, <100MB RAM (negligible on modern hardware)
- Storage: <1GB for vault with 1000 files
- Bandwidth: Zero (no network requests)

**Total Cost of Ownership (TCO)**: $0 for Bronze tier (excluding developer time)

## 5. Data Management and Migration

### 5.1 Data Schema

**Dashboard.md Structure**:
```markdown
# Personal AI Employee Dashboard

## Task Overview
| Filename | Date Added | Status | Priority |
|----------|-----------|--------|----------|
| [[Inbox/task.md]] | 2026-02-10 15:30 | Inbox | Medium |

## Statistics
- **Total Tasks**: 1
- **Inbox**: 1
- **Needs Action**: 0
- **Done**: 0

---
*Last Updated: 2026-02-10 15:30:45*
```

**Field Definitions**:
- `Filename`: Obsidian wiki link format `[[relative/path.md]]` (clickable in Obsidian)
- `Date Added`: ISO 8601 datetime without timezone (YYYY-MM-DD HH:MM)
- `Status`: One of ["Inbox", "Needs Action", "Done"] (case-sensitive)
- `Priority`: Default "Medium" for Bronze tier (AI-scored in Silver+)
- `Statistics`: Computed from table rows (updated on every dashboard refresh)
- `Last Updated`: ISO 8601 datetime when dashboard was last modified

**Company_Handbook.md Structure**:
```markdown
---
version: 1.0.0
tier: bronze
last_updated: 2026-02-10
---

# Company Handbook - Bronze Tier

## 1. File Naming Convention
[User-defined rules]

## 2. Folder Usage Guidelines
[User-defined rules]

## 3. Forbidden Operations (Bronze Tier)
[System-defined rules, read-only for user]

## 4. Escalation Rules
[User-defined rules]

## 5. Bronze Tier Limitations
[System-defined rules, read-only for user]
```

**YAML Frontmatter Schema**:
```yaml
version: string         # Handbook version (semver format)
tier: string            # Current tier ("bronze", "silver", "gold", "platinum")
last_updated: string    # ISO 8601 date (YYYY-MM-DD)
```

---

### 5.2 Data Migration Strategy

**Bronze Tier v0.1.0 → v0.2.0** (hypothetical):
- No migration needed for Bronze tier (stable data format)
- If Dashboard.md format changes, migration script: `scripts/migrate_dashboard.py`

**Migration Script Template**:
```python
def migrate_dashboard_v1_to_v2(vault_path: str):
    """Migrate Dashboard.md from v0.1.0 to v0.2.0 format.

    Changes:
        - Add "Tags" column to task table
        - Preserve all existing data
        - Create backup before migration
    """
    # 1. Backup current dashboard
    backup_path = create_backup(Path(vault_path) / "Dashboard.md")

    # 2. Parse v0.1.0 format
    old_tasks = parse_dashboard_v1(vault_path)

    # 3. Transform to v0.2.0 format (add default tags)
    new_tasks = [
        {**task, "tags": ""}  # Add empty tags column
        for task in old_tasks
    ]

    # 4. Write v0.2.0 format
    render_dashboard_v2(vault_path, new_tasks)

    # 5. Validate migration
    validate_dashboard(Path(vault_path) / "Dashboard.md")
```

**Migration Testing**:
- Unit test: Create v0.1.0 dashboard, run migration, verify v0.2.0 format
- Rollback test: Restore from backup, verify v0.1.0 format preserved

---

### 5.3 Data Retention and Cleanup

**Backup Retention Policy**:
- Dashboard.md.bak.* files: Keep last 5 backups per day (delete older)
- Watcher logs (vault/Logs/watcher-*.md): Keep 7 days (delete older)
- Cleanup runs on watcher startup (prune_old_backups(), prune_old_logs())

**User Data Retention**:
- Inbox/, Needs_Action/, Done/, Plans/: User-managed (watcher never deletes)
- Dashboard.md: Auto-maintained (user can manually edit, but edits may be overwritten)
- Company_Handbook.md: User-managed (watcher only reads)

---

### 5.4 Source of Truth

**Dashboard.md**:
- Source of truth: **Vault filesystem** (Inbox/, Needs_Action/, Done/ folders)
- Dashboard.md is a **derived view** (rebuilt from filesystem on every update)
- If Dashboard.md is deleted, watcher recreates from current vault state (no data loss)

**Company_Handbook.md**:
- Source of truth: **Company_Handbook.md file** (user-editable)
- Watcher reads configuration from handbook on startup
- If handbook is modified, user must restart watcher to reload (Bronze tier)

**Watcher Logs**:
- Source of truth: **vault/Logs/watcher-*.md files** (append-only)
- Logs are immutable (watcher never modifies past log entries)
- Logs are informational (not used for state reconstruction)

## 6. Operational Readiness

### 6.1 Observability

**Logging Strategy**:
- **Level**: INFO (default), DEBUG (development), ERROR (production)
- **Format**: Human-readable markdown (vault/Logs/watcher-YYYY-MM-DD.md)
- **Structured**: Each event has timestamp, event type, file list, outcome
- **Rotation**: Daily log files (watcher-YYYY-MM-DD.md), pruned after 7 days

**Log Event Types**:
- `watcher_started`: Watcher process started (log vault path, polling interval, handbook validation)
- `file_detected`: New .md file detected in Inbox/ (log filename, size, encoding)
- `dashboard_updated`: Dashboard.md successfully updated (log new tasks count, update time)
- `dashboard_update_failed`: Dashboard.md update failed (log error, backtrace)
- `error`: Unexpected error (log exception type, message, backtrace)
- `watcher_stopped`: Watcher process stopped (log reason, uptime, total files processed)

**Metrics** (logged to watcher-YYYY-MM-DD.md):
- Files processed per hour
- Average dashboard update time
- Error count per hour
- Watcher uptime (start/stop timestamps)

**Tracing**:
- Bronze tier: No distributed tracing (single-process application)
- Silver tier: Add request IDs if multi-process (e.g., separate email/WhatsApp watchers)

---

### 6.2 Alerting

**Bronze Tier Alerts** (logged to vault/Logs/watcher-YYYY-MM-DD.md):
- **WARNING**: Dashboard update time >2 seconds (performance degradation)
- **WARNING**: File lock detected (Obsidian conflict, user should close Obsidian)
- **WARNING**: Handbook validation failed (missing required sections)
- **ERROR**: Dashboard.md corrupted (automatic restoration from .bak)
- **ERROR**: Watcher crash (exit code 1, 2, or 3)

**User Notification Strategy**:
- Bronze tier: Passive (user must read vault/Logs/watcher-YYYY-MM-DD.md)
- Silver tier: Active (desktop notification for ERROR-level events)

**Alert Thresholds**:
- Dashboard update time: >2 seconds (NFR-B-PERF-001 violation)
- Error rate: >5 errors per hour (reliability concern)
- Watcher restart: >3 restarts per hour (investigate root cause)

---

### 6.3 Runbooks

#### Runbook 1: Watcher Won't Start

**Symptoms**: `scripts/watch_inbox.py` exits immediately with error code 1 or 2

**Diagnosis**:
1. Check exit code: `echo $?` (after running watcher)
   - Exit code 1: Vault path invalid
   - Exit code 2: Handbook validation failed
   - Exit code 3: Filesystem permission error

2. Check vault structure:
   ```bash
   ls vault/
   # Should see: Inbox/ Needs_Action/ Done/ Plans/ Logs/ Dashboard.md Company_Handbook.md
   ```

3. Check handbook validation:
   ```bash
   python -c "from agent_skills.vault_watcher import validate_handbook; print(validate_handbook('vault/'))"
   # Should print: (True, [])
   ```

**Resolution**:
- **Exit code 1**: Run `python scripts/init_vault.py vault/` to initialize vault
- **Exit code 2**: Edit `vault/Company_Handbook.md`, add missing sections (see Appendix B in spec)
- **Exit code 3**: Fix permissions: `chmod -R u+rw vault/`

---

#### Runbook 2: Dashboard.md Not Updating

**Symptoms**: Files added to Inbox/, but Dashboard.md doesn't change

**Diagnosis**:
1. Check watcher is running: `ps aux | grep watch_inbox.py`
2. Check watcher logs: `tail -f vault/Logs/watcher-$(date +%Y-%m-%d).md`
3. Check for file lock errors in logs (Obsidian conflict)
4. Check Dashboard.md.bak timestamps: `ls -lt vault/Dashboard.md.bak.*`

**Resolution**:
- **Watcher not running**: Start watcher: `python scripts/watch_inbox.py vault/`
- **File lock errors**: Close Obsidian, watcher will retry on next cycle
- **No .bak files**: Dashboard update is failing silently, check watcher logs for errors

---

#### Runbook 3: Dashboard.md Corrupted

**Symptoms**: Dashboard.md contains invalid markdown (table not rendering in Obsidian)

**Diagnosis**:
1. Open `vault/Dashboard.md` in text editor
2. Check for malformed markdown table (missing pipes `|`, misaligned columns)
3. Check for incomplete write (file ends abruptly)

**Resolution**:
- **Automatic recovery**: Watcher should detect corruption on next update and restore from .bak
- **Manual recovery**:
  ```bash
  # Find most recent backup
  ls -lt vault/Dashboard.md.bak.*
  # Restore manually
  cp vault/Dashboard.md.bak.2026-02-10_15-30-00 vault/Dashboard.md
  ```

---

#### Runbook 4: Watcher Keeps Restarting

**Symptoms**: Watcher crashes repeatedly, logs show multiple `watcher_started` events

**Diagnosis**:
1. Check watcher logs for ERROR events before each restart
2. Check vault filesystem for corrupted files (encoding errors, invalid symlinks)
3. Check system resources (disk space, memory)

**Resolution**:
- **Encoding errors**: Find problematic file in logs, convert to UTF-8 or remove
- **Disk full**: Free up space: `df -h`, remove old backups/logs
- **Memory exhausted**: Check vault size: `du -sh vault/`, if >1000 files, upgrade to Silver tier

---

### 6.4 Deployment Strategy

**Bronze Tier Deployment** (local-only):
1. **Install dependencies**: `pip install -e .` (installs watchdog, pyyaml)
2. **Initialize vault**: `python scripts/init_vault.py ~/my-vault`
3. **Configure handbook**: Edit `~/my-vault/Company_Handbook.md` with user preferences
4. **Start watcher**: `python scripts/watch_inbox.py ~/my-vault`
5. **Test**: Drop test file in `~/my-vault/Inbox/`, verify Dashboard.md updates

**Process Management** (for 24/7 operation):
- **Option 1 - PM2** (Node.js process manager):
  ```bash
  pm2 start "python scripts/watch_inbox.py ~/my-vault" --name bronze-watcher
  pm2 save
  pm2 startup  # Auto-start on reboot
  ```

- **Option 2 - systemd** (Linux service):
  ```ini
  # /etc/systemd/system/bronze-watcher.service
  [Unit]
  Description=Bronze Tier AI Employee Watcher
  After=network.target

  [Service]
  Type=simple
  User=myuser
  WorkingDirectory=/home/myuser/personal-ai-employee
  ExecStart=/usr/bin/python3 scripts/watch_inbox.py /home/myuser/my-vault
  Restart=on-failure
  RestartSec=30

  [Install]
  WantedBy=multi-user.target
  ```

**Rollback Strategy**:
- Bronze tier has no database migrations, so rollback = revert to previous code version
- Dashboard.md.bak files allow recovery from bad updates

---

### 6.5 Feature Flags (Bronze Tier)

**No feature flags in Bronze tier** (all functionality always enabled).

**Silver Tier Preview**: Feature flags for optional AI analysis:
```yaml
# Company_Handbook.md frontmatter
features:
  ai_priority_scoring: false  # Bronze default
  auto_file_movement: false   # Bronze default
```

## 7. Risk Analysis and Mitigation

### 7.1 Top 3 Risks

#### Risk 1: Dashboard.md Corruption on Power Loss

**Likelihood**: Medium (power outages, system crashes, kernel panics)
**Impact**: High (users lose trust in system if dashboard frequently corrupted)
**Blast Radius**: Single user's vault (no multi-user impact in Bronze tier)

**Mitigation Strategies**:
1. **Atomic writes**: Use POSIX atomic rename (write to temp file, then rename)
   - Rationale: OS guarantees atomicity of rename operation (either old file or new file, never half-written)
   - Test: Simulate power loss with `kill -9` during dashboard update, verify Dashboard.md intact

2. **Backups before every update**: Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS
   - Rationale: Even if atomic rename fails (unlikely), backup enables recovery
   - Test: Corrupt Dashboard.md manually, verify watcher restores from .bak on next update

3. **Corruption detection**: Validate Dashboard.md after every update (check markdown table syntax)
   - Rationale: Detect corruption immediately, not hours later when user opens dashboard
   - Test: Unit test with malformed Dashboard.md, verify validation fails and restoration triggers

**Kill Switch**: If Dashboard.md corruption rate >1% (unacceptable), add fsync() before rename (slower, but guarantees durability).

**Monitoring**: Log Dashboard.md validation result after every update, alert if validation fails.

---

#### Risk 2: File Lock Conflicts with Obsidian

**Likelihood**: High (Obsidian often locks files while user is editing)
**Impact**: Medium (watcher can't read locked files, logs warning, retries next cycle)
**Blast Radius**: Single file (other files processed normally)

**Mitigation Strategies**:
1. **Graceful degradation**: Log warning, skip locked file, continue monitoring
   - Rationale: Bronze tier can tolerate 30-second delay (retry on next polling cycle)
   - Test: Open file in Obsidian, drop in Inbox/, verify watcher logs "file locked" warning

2. **File lock detection**: Use `fcntl.flock()` (POSIX) or `msvcrt.locking()` (Windows) to check if file is locked before read
   - Rationale: Distinguish between "file locked" (retry) and "file doesn't exist" (error)
   - Test: Unit test with locked file fixture, verify PermissionError raised (not FileNotFoundError)

3. **User guidance**: Runbook instructs user to close Obsidian temporarily if persistent lock errors
   - Rationale: Most users won't edit Inbox/ files (drop-and-forget workflow), so conflicts are rare

**Kill Switch**: If file lock rate >50% (half of files locked), suggest user closes Obsidian or changes workflow.

**Monitoring**: Log file lock count per hour, alert if >10 locks (user may be editing Inbox/ files frequently).

---

#### Risk 3: Vault Size Exceeds 1000 Files (Performance Degradation)

**Likelihood**: Low (Bronze tier is for individual use, 1000 files = ~2 years of daily tasks)
**Impact**: Medium (dashboard update time exceeds 2-second target, but no data loss)
**Blast Radius**: Single user's vault (no multi-user impact in Bronze tier)

**Mitigation Strategies**:
1. **Performance warning**: Log warning if vault exceeds 1000 files (upgrade to Silver tier)
   - Rationale: Bronze tier is foundation (not designed for power users)
   - Test: Integration test with 1000-file fixture, verify dashboard update <2 seconds

2. **Graceful degradation**: Dashboard update may take 3-5 seconds (not 2 seconds), but still functional
   - Rationale: 3-5 seconds is acceptable for occasional edge case (most users have <100 files)
   - Test: Integration test with 1500-file fixture, verify watcher doesn't crash (just slower)

3. **Cleanup strategy**: Encourage users to move completed tasks to Done/ folder, then archive (manual process in Bronze)
   - Rationale: Dashboard only tracks active tasks (Inbox + Needs_Action), not Done/ folder
   - User guidance: Runbook explains how to archive Done/ tasks to external folder

**Kill Switch**: If vault exceeds 10,000 files, watcher refuses to start (log error, exit code 4).

**Monitoring**: Log vault size (file count) on watcher startup, alert if >1000 files.

---

### 7.2 Secondary Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Obsidian version incompatibility | Low | Medium | Test with Obsidian 1.5+ and 1.11.7 specifically, document minimum version |
| Python version incompatibility | Low | Low | Require Python 3.11+, use type hints (mypy checks compatibility) |
| Watchdog library bug | Low | High | Pin watchdog>=3.0.0 (stable version), fallback to manual polling if watchdog fails |
| Invalid UTF-8 encoding in vault files | Medium | Low | Skip files with encoding errors (log warning), continue monitoring |
| User manually edits Dashboard.md | Medium | Low | Next update may overwrite manual edits (user should edit tasks in Inbox/ files, not dashboard) |
| Runaway backup creation (disk full) | Low | Medium | Prune backups older than 7 days on watcher startup |

## 8. Evaluation and Validation

### 8.1 Definition of Done

Bronze Tier is considered **Done** when all of the following criteria are met:

**Functional Completeness**:
- [ ] All 5 user stories have passing acceptance tests (25 acceptance scenarios total)
- [ ] All 25 functional requirements (FR-B001 through FR-B025) are implemented and verified
- [ ] All 18 non-functional requirements (NFR-B-*) are verified with measurable tests

**Testing**:
- [ ] Pytest unit tests achieve 80%+ coverage for agent_skills/ module
- [ ] Integration test passes: Drop test file → Watcher detects → Dashboard updates → Claude Code queries
- [ ] All 8 edge cases handled gracefully (no crashes on locked files, corrupted data, race conditions)
- [ ] Performance tests pass: Dashboard update <2s, file read <500ms, 1000-file vault support
- [ ] Idempotency tests pass: Running watcher multiple times produces same Dashboard.md

**Code Quality**:
- [ ] Code passes mypy type checking with zero errors (100% type coverage)
- [ ] Code passes black formatting check (no manual formatting fixes)
- [ ] All functions have docstrings with Args, Returns, Raises, Example sections
- [ ] No pylint warnings (or warnings are explicitly justified and documented)

**Documentation**:
- [ ] README.md includes Bronze tier setup instructions (user can run system without developer assistance)
- [ ] Runbooks created for 4 common failure modes (watcher won't start, dashboard not updating, corruption, restarts)
- [ ] API documentation generated (pdoc or sphinx) for agent_skills/ module
- [ ] Company_Handbook.md template includes all 5 required sections with examples

**Operational Readiness**:
- [ ] Watcher runs continuously for 24 hours with 99% uptime (allowed 15 minutes downtime for restarts)
- [ ] Dashboard.md corruption rate <1% (automatic recovery from .bak files works)
- [ ] Zero network traffic detected during watcher runtime (verified with tcpdump or Wireshark)
- [ ] Process management setup documented (PM2 or systemd service file provided)

**User Validation**:
- [ ] User can initialize vault with `python scripts/init_vault.py vault/` in <30 seconds
- [ ] User can start watcher with `python scripts/watch_inbox.py vault/` (no errors)
- [ ] User drops test file in vault/Inbox/, Dashboard.md updates within 30 seconds
- [ ] User opens vault in Obsidian 1.11.7, Dashboard.md renders correctly (markdown table displays as table)

---

### 8.2 Output Validation

**Dashboard.md Validation**:
```python
def validate_dashboard(dashboard_path: Path) -> bool:
    """Validate Dashboard.md markdown structure.

    Checks:
        - File exists and is readable
        - Contains markdown table with 4 columns (Filename, Date Added, Status, Priority)
        - Table separator row is valid (|---|---|---|---|)
        - All Filename cells use Obsidian wiki link format [[file.md]]
        - All Status values are one of ["Inbox", "Needs Action", "Done"]
        - Statistics section exists with counts (Total, Inbox, Needs Action, Done)
        - Last Updated timestamp is recent (within 1 hour)

    Returns:
        True if valid, False otherwise (logs specific validation errors)
    """
```

**Company_Handbook.md Validation**:
```python
def validate_handbook(vault_path: str) -> tuple[bool, list[str]]:
    """Validate Company_Handbook.md structure.

    Checks:
        - File exists and is readable
        - YAML frontmatter is valid (parses with pyyaml)
        - All 5 required sections present (see spec FR-B003)
        - No dangerous shell commands in configuration (no `rm -rf`, `eval()`)

    Returns:
        (is_valid, missing_sections)
    """
```

---

### 8.3 Acceptance Tests

**Integration Test: End-to-End Flow**:
```python
def test_end_to_end_flow(tmp_vault):
    """Drop file → Detect → Update → Query flow."""
    # Setup: Initialize vault
    init_vault(tmp_vault)

    # Start watcher in background thread
    watcher_thread = threading.Thread(
        target=watch_inbox,
        args=(tmp_vault,),
        daemon=True
    )
    watcher_thread.start()

    # Act: Drop test file in Inbox/
    test_file = tmp_vault / "Inbox" / "2026-02-10-test-task.md"
    test_file.write_text("# Test Task\n\nThis is a test.")

    # Wait for detection (30s polling + 2s update = 32s max)
    time.sleep(35)

    # Assert: Dashboard.md updated
    dashboard = (tmp_vault / "Dashboard.md").read_text()
    assert "2026-02-10-test-task.md" in dashboard
    assert "Inbox" in dashboard
    assert "Medium" in dashboard

    # Assert: Claude Code can query
    summary = get_dashboard_summary(str(tmp_vault))
    assert summary["inbox"] == 1
    assert summary["total"] == 1

    # Assert: Watcher log exists
    log_file = tmp_vault / "Logs" / f"watcher-{datetime.now().strftime('%Y-%m-%d')}.md"
    assert log_file.exists()
    log_content = log_file.read_text()
    assert "File Detected" in log_content
    assert "Dashboard Updated" in log_content
```

---

### 8.4 Safety Audit

**Security Checks** (run before marking Bronze tier as Done):
- [ ] No `eval()` or `exec()` calls in codebase (grep search)
- [ ] No shell commands with user input (no `os.system()`, `subprocess.call()` with vault data)
- [ ] All file paths validated (no directory traversal attacks: `read_vault_file("../../etc/passwd")` raises ValueError)
- [ ] No network requests (verified with `tcpdump` during 24-hour watcher run)
- [ ] No credentials in code or logs (grep search for "password", "token", "api_key")

**Data Integrity Checks**:
- [ ] Atomic writes verified (rename is atomic on all target platforms: Linux, macOS, Windows)
- [ ] Backups created before every Dashboard.md update (check .bak files exist)
- [ ] Corruption recovery tested (manually corrupt Dashboard.md, verify automatic restoration)
- [ ] Race condition handling tested (add 10 files simultaneously, verify all detected)

**Obsidian Compatibility Checks**:
- [ ] Dashboard.md renders correctly in Obsidian 1.5+
- [ ] Wiki links [[file.md]] are clickable in Obsidian
- [ ] YAML frontmatter in Company_Handbook.md is recognized by Obsidian
- [ ] No proprietary Obsidian plugins required (standard markdown only)

## 9. Architecture Decision Records (ADRs)

**Significant decisions detected during planning phase**. Each should be documented with `/sp.adr <decision-title>` if approved.

---

### 📋 Architectural Decision Detected: Polling vs. Real-Time Event Monitoring

**Decision**: Use polling with 30-second interval instead of real-time file system events

**Context**: File watcher can use either watchdog polling mode (check every 30s) or event mode (trigger on FS change)

**Consequences**:
- ✅ Simpler implementation (Bronze tier foundation)
- ✅ Lower CPU usage (no rapid-fire event handling)
- ✅ Predictable behavior (users understand "checks every 30 seconds")
- ❌ 30-second delay for file detection (acceptable for Bronze tier task management)

**Tradeoffs**: Real-time events would give instant detection but increase complexity and CPU usage. Bronze tier prioritizes simplicity and reliability over low latency.

**Reversibility**: Silver tier can upgrade to event-driven if needed (watchdog supports both modes).

**Document reasoning and tradeoffs? Run `/sp.adr polling-vs-realtime-monitoring`**

---

### 📋 Architectural Decision Detected: Atomic Writes with Backups for Dashboard Updates

**Decision**: Use atomic write pattern (temp file → rename) with timestamped backups before every Dashboard.md update

**Context**: Dashboard.md updates risk corruption on power loss or Obsidian file lock conflicts

**Consequences**:
- ✅ Data integrity guaranteed (POSIX atomic rename)
- ✅ Automatic recovery from corruption (restore from .bak)
- ✅ User can manually recover from backups (timestamped .bak files)
- ❌ Extra disk I/O (create temp file + backup file for every update)
- ❌ Backup pruning required (delete old .bak files after 7 days)

**Tradeoffs**: Direct writes would be faster but risk corruption. Constitution Principle II prioritizes vault integrity over performance.

**Reversibility**: No, this is a safety requirement (non-negotiable per constitution).

**Document reasoning and tradeoffs? Run `/sp.adr atomic-dashboard-updates`**

---

### 📋 Architectural Decision Detected: Pure Functions for Agent Skills API

**Decision**: Implement Agent Skills as module-level pure functions (not stateful classes)

**Context**: Agent Skills can be exposed as functions or class methods

**Consequences**:
- ✅ Simpler testing (no mock __init__, just call functions with test fixtures)
- ✅ More natural for Claude Code integration (function imports vs. class instantiation)
- ✅ Explicit dependencies (vault_path always passed as parameter)
- ❌ No encapsulation (but Bronze tier doesn't need stateful operations)

**Tradeoffs**: Classes would provide encapsulation but add complexity for Bronze tier. Pure functions align with functional programming principles and simplify testing.

**Reversibility**: Yes, Silver tier can introduce VaultContext class if stateful operations needed (e.g., connection pooling for external APIs).

**Document reasoning and tradeoffs? Run `/sp.adr agent-skills-api-design`**

---

## Next Steps

### Immediate Actions (After Plan Approval)

1. **Review Plan**: Stakeholders review this plan for accuracy and completeness
2. **Create Tasks**: Run `/sp.tasks bronze-tier` to generate dependency-ordered implementation tasks
3. **Setup Development Environment**:
   ```bash
   # Create Python virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -e .[dev]
   ```
4. **Initialize Project Structure**:
   ```bash
   mkdir -p agent_skills scripts tests/{unit,integration,fixtures} vault
   touch agent_skills/__init__.py
   ```

### Implementation Sequence (Recommended)

**Phase 1: Foundation (P1 User Stories)**
1. Implement `scripts/init_vault.py` (vault initialization)
2. Implement `agent_skills/vault_watcher.py` (4 API functions)
3. Write unit tests for vault_watcher.py (target: 80% coverage)
4. Implement `agent_skills/dashboard_updater.py` (atomic updates, backups)
5. Write unit tests for dashboard_updater.py

**Phase 2: File Monitoring (P1 User Stories)**
6. Implement `scripts/watch_inbox.py` (polling loop, signal handling)
7. Write integration test: Drop file → Detect → Update → Query
8. Test with 1000-file vault (performance verification)

**Phase 3: Handbook Validation (P2 User Stories)**
9. Implement handbook validation in `scripts/watch_inbox.py` (startup check)
10. Write unit tests for validation edge cases (missing sections, malformed YAML)

**Phase 4: Polish & Documentation**
11. Write runbooks (4 common failure modes)
12. Create README.md with setup instructions
13. Run full test suite (unit + integration + performance)
14. Set up process management (PM2 or systemd)

### Quality Gates (Must Pass Before PR Merge)

- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] Integration test passes (`pytest tests/integration/`)
- [ ] Code coverage ≥80% (`pytest --cov=agent_skills --cov-report=term`)
- [ ] Mypy type checking passes (`mypy agent_skills/ scripts/`)
- [ ] Black formatting passes (`black --check agent_skills/ scripts/`)
- [ ] Performance tests pass (dashboard update <2s, file read <500ms)

### ADR Creation (Optional but Recommended)

If any of the 3 detected architectural decisions need formal documentation:
- `/sp.adr polling-vs-realtime-monitoring` - Document polling decision
- `/sp.adr atomic-dashboard-updates` - Document atomic write strategy
- `/sp.adr agent-skills-api-design` - Document pure functions vs. classes

---

**Version**: 1.0.0 | **Status**: Draft | **Next Review**: After stakeholder approval
