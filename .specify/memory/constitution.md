# Personal AI Employee Constitution

## Core Principles

### I. Agent Autonomy & Tier Progression

**Autonomy must be earned through incremental capability:**

- **Bronze Tier (Monitoring)**: Agent monitors only, human reviews all changes manually
  - Zero autonomous actions
  - All changes require explicit human approval
  - 100% offline operation (no external API calls)
  - File watching and change detection only

- **Silver Tier (Analysis & Suggestion)**: Agent analyzes with AI and suggests priorities, human approves actions
  - Optional Claude API for task analysis (must work offline if API unavailable)
  - AI-powered priority ranking of inbox items
  - Suggested actions presented to human for approval
  - No autonomous file modifications

- **Gold Tier (Plan & Approve)**: Agent proposes multi-step plans, human approves before execution
  - Multi-step workflow planning capability
  - Optional external integrations (email, calendar) with graceful offline degradation
  - Human approval required before plan execution
  - Plan execution with progress tracking

- **Platinum Tier (Autonomous with Reflection)**: Fully autonomous with reflection loop, human oversight optional
  - Self-directed task execution with reasoning loop
  - Continuous reflection and error correction
  - Human oversight available but not required
  - Full audit trail of all autonomous decisions

**Universal Requirements Across All Tiers:**
- All agent actions MUST log reasoning to `vault/Logs/` before execution
- Log format: `YYYY-MM-DD_HH-MM-SS_action-name.md` with YAML frontmatter (timestamp, tier, action, reasoning, outcome)
- Never skip tiers (no "Gold features" in Bronze implementation)
- Each tier builds on previous tier's capabilities

### II. Vault Integrity & Obsidian Compatibility

**The vault is sacred - never corrupt user data:**

- **Never corrupt Obsidian markdown syntax:**
  - YAML frontmatter: Must use `---` delimiters with valid YAML
  - Wiki links: Use `[[Page Name]]` or `[[Page Name|Display Text]]` format
  - Tags: Use `#tag` or `#nested/tag` format (no spaces)
  - Dataview queries: Preserve backtick blocks and query syntax
  - Callouts: Preserve `> [!type]` syntax

- **Use atomic file operations:**
  - Read → Validate syntax → Modify → Validate syntax → Write
  - Never use partial writes or append operations on YAML frontmatter
  - Always read entire file before modifying
  - Validate markdown structure after every write

- **File watcher must handle race conditions:**
  - Use file locking or timestamp-based conflict detection
  - If file changed between read and write, re-read and retry operation
  - Maximum 3 retry attempts before logging error and notifying human
  - Never overwrite newer changes with stale data

- **Always backup critical files:**
  - `vault/Dashboard.md`: Create `.bak` file before every update
  - Keep last 5 backups with timestamps: `Dashboard.md.bak.YYYY-MM-DD_HH-MM-SS`
  - `Company_Handbook.md`: Backup before agent runtime modifications
  - Automatically prune backups older than 7 days

- **Graceful degradation on vault corruption:**
  - If Obsidian vault is locked: Log error, notify human, pause agent operations
  - If markdown syntax invalid: Log parse error, skip file, continue with others
  - If Dashboard.md corrupted: Restore from `.bak` file automatically
  - Never crash agent runtime on vault errors

### III. Local-First Architecture

**Default to offline operation - external APIs are optional enhancements:**

- **Bronze Tier (100% offline):**
  - Zero external API calls
  - All data persists in `vault/` folder
  - No network dependency checks
  - Pure filesystem-based operations

- **Silver Tier (Optional AI Analysis):**
  - Claude API for task analysis (optional)
  - Must work offline if API unavailable (fallback to rule-based analysis)
  - API key stored in `.env` file (never in code)
  - Timeout: 10 seconds for API calls, graceful fallback on timeout

- **Gold Tier (Optional External Integrations):**
  - Optional email, calendar, webhook integrations
  - Core functions (file watching, dashboard updates) remain local
  - External integration failures never block core operations
  - Each integration has offline fallback mode

- **Universal Local-First Rules:**
  - All critical data persists in `vault/` folder (no external databases)
  - Configuration stored in `Company_Handbook.md` (human-editable markdown)
  - No cloud storage dependencies (works with local Obsidian vault only)
  - Network failures never corrupt local state

### IV. Test-Driven Safety

**Every feature must prove safety before deployment:**

- **Unit Tests (Required for All Agent Skills):**
  - Every function in `agent_skills/` must have pytest unit tests in `tests/`
  - Test file naming: `test_<module_name>.py`
  - Minimum 80% code coverage for agent skills
  - Tests must pass before any PR merge

- **Integration Tests (Required for File Watchers):**
  - Test with real `vault/` folder in isolated test environment
  - Simulate file additions, modifications, deletions, race conditions
  - Test Obsidian markdown syntax preservation (YAML, wiki links, tags)
  - Test backup/restore functionality for critical files

- **Mock External APIs:**
  - No real API calls during testing (use `pytest-mock` or `unittest.mock`)
  - Mock Claude API responses for Silver/Gold tier tests
  - Mock email/calendar APIs for Gold tier integration tests
  - Test offline fallback behavior explicitly

- **Idempotency Tests:**
  - `Dashboard.md` updates: Running twice must produce same result
  - Agent skill execution: Re-running same operation must be safe
  - File watcher recovery: Must handle duplicate events correctly

- **Configuration Validation Tests:**
  - Test `Company_Handbook.md` parsing with missing required sections
  - Test invalid YAML frontmatter handling
  - Test malformed configuration graceful degradation

- **Performance Tests:**
  - Test with vaults up to 10,000 markdown files
  - Test dashboard update completes within 2 seconds
  - Test agent skill response times (<5s read, <10s write)

### V. Incremental Development Discipline

**Build capabilities systematically - no skipping ahead:**

- **Feature Branch Strategy:**
  - Bronze tier development: `bronze-tier` branch
  - Silver tier development: `silver-tier` branch (merged from bronze-tier)
  - Gold tier development: `gold-tier` branch (merged from silver-tier)
  - Platinum tier development: `platinum-tier` branch (merged from gold-tier)
  - Never merge higher-tier features into lower-tier branches

- **Git Commit Discipline:**
  - Every commit must reference spec files (e.g., "Implements Bronze spec section 2.1")
  - Commit messages format: `[TIER] Brief description (spec: <file>#section)`
  - Example: `[Bronze] Add file watcher with 30s polling (spec: bronze-spec.md#2.1)`
  - No commits without corresponding spec/plan/task documentation

- **Tier Completion Criteria:**
  - Bronze: All Bronze spec tasks completed, tests pass, human validation approved
  - Silver: Includes all Bronze features + Silver features, integration tests pass
  - Gold: Includes all Bronze + Silver + Gold features, performance tests pass
  - Platinum: Full autonomous operation with reflection loop, safety audit passed

- **Clear Separation of Concerns:**
  - `.specify/`: Development workspace (specs, plans, tasks, PHRs, ADRs)
  - `vault/`: Product deliverable (only Obsidian-compatible markdown files)
  - `agent_skills/`: Reusable Python modules (callable by Claude Code and watchers)
  - `scripts/`: Background processes (file watchers, dashboard updaters)
  - `tests/`: Pytest test suites (unit tests for skills, integration tests for watchers)
  - Never mix development artifacts with product deliverables

### VI. Code Organization & Modularity

**Enforce clean boundaries between system components:**

- **Directory Structure (Non-Negotiable):**
  ```
  .specify/                  # Development workspace
    ├── memory/
    │   └── constitution.md  # This file
    ├── templates/           # Spec, plan, task, ADR templates
    └── scripts/             # Development automation scripts

  vault/                     # Product deliverable (Obsidian vault)
    ├── Dashboard.md         # Agent-maintained task dashboard
    ├── Company_Handbook.md  # Agent operational rules (config)
    ├── Logs/                # Agent reasoning logs
    └── [User markdown files]

  agent_skills/              # Reusable Python modules
    ├── __init__.py
    ├── file_watcher.py      # File monitoring utilities
    ├── dashboard_updater.py # Dashboard manipulation
    ├── vault_parser.py      # Obsidian markdown parsing
    └── ai_analyzer.py       # Claude API integration (Silver+)

  scripts/                   # Background processes
    ├── bronze_watcher.sh    # Bronze tier file watcher
    └── silver_watcher.py    # Silver tier AI-powered watcher

  tests/                     # Pytest test suites
    ├── unit/                # Unit tests for agent_skills/
    ├── integration/         # Integration tests for file watchers
    └── fixtures/            # Test data and mock vaults
  ```

- **Module Responsibilities (Single Responsibility Principle):**
  - `file_watcher.py`: Detect file changes in vault (no business logic)
  - `vault_parser.py`: Parse Obsidian markdown (no file I/O)
  - `dashboard_updater.py`: Update Dashboard.md (atomic operations only)
  - `ai_analyzer.py`: Claude API calls (with offline fallbacks)
  - Each module: One clear purpose, independently testable

- **Import Discipline:**
  - Agent skills must not import from `scripts/` (one-way dependency)
  - Test modules can import from `agent_skills/` (for testing)
  - Never circular dependencies between agent skills
  - External dependencies: Minimize and document in `pyproject.toml`

## Testing & Safety Standards

### Test Coverage Requirements

- **Unit Tests**: 80% minimum coverage for `agent_skills/`
- **Integration Tests**: All file watcher workflows tested with real vault
- **Regression Tests**: Every bug fix must include regression test
- **Performance Tests**: Vault size (10,000 files), dashboard update (<2s), skill response (<5s read, <10s write)

### Safety Checklist (Pre-Deployment)

- [ ] All tests passing (pytest)
- [ ] No unhandled exceptions in agent skills
- [ ] Vault corruption recovery tested
- [ ] Offline fallback tested (Silver/Gold tiers)
- [ ] Race condition handling verified (integration tests)
- [ ] Backup/restore functionality validated
- [ ] Performance requirements met (see Performance Requirements)
- [ ] Human approval workflow tested (Bronze/Silver/Gold tiers)

## Documentation Standards

### Required Documentation Files

- **`Company_Handbook.md`** (Agent operational rules):
  - Required sections: Agent Role, Inbox Rules, Priority Scoring, Task Lifecycle, Integration Settings
  - Read at runtime by agent before every operation
  - Human-editable markdown (no code syntax)
  - Must pass validation before agent starts (see `agent_skills/handbook_validator.py`)

- **`constitution.md`** (This file - development principles):
  - Read by human developers and Claude Code
  - Not read by runtime agent (development-time only)
  - Updated only through `/sp.constitution` command

- **Agent Skill Docstrings** (Required format):
  ```python
  def update_dashboard(vault_path: str, new_files: list[str]) -> bool:
      """Update Dashboard.md with new inbox files.

      Args:
          vault_path: Absolute path to Obsidian vault directory
          new_files: List of relative file paths added to inbox

      Returns:
          True if dashboard updated successfully, False otherwise

      Raises:
          VaultCorruptionError: If Dashboard.md has invalid markdown syntax
          BackupError: If backup creation fails

      Example:
          >>> update_dashboard("/path/to/vault", ["inbox/new-task.md"])
          True
      """
  ```

- **`README.md`** (Setup instructions for Bronze tier):
  - Prerequisites: Obsidian 1.5+, Python 3.11+, pip
  - Installation steps (numbered, copy-pasteable commands)
  - Configuration: `Company_Handbook.md` setup, `.env` file (Silver+ only)
  - Running: How to start Bronze tier file watcher
  - Troubleshooting: Common issues and solutions
  - Assume user has Obsidian + Python (no Docker/Kubernetes required for Bronze)

- **`Dashboard.md`** (Agent-maintained task dashboard):
  - Format: Markdown table with columns `[File, Added, Status, Priority]`
  - Example:
    ```markdown
    | File | Added | Status | Priority |
    |------|-------|--------|----------|
    | [[inbox/client-request.md]] | 2026-02-10 | New | High |
    | [[inbox/bug-report.md]] | 2026-02-09 | In Progress | Medium |
    ```
  - Must use Obsidian wiki link syntax for files
  - Status values: `New`, `In Progress`, `Completed`, `Archived`
  - Priority values: `High`, `Medium`, `Low` (AI-scored in Silver+ tiers)

## Performance Requirements

### Bronze Tier (Monitoring)

- **File Watcher Polling**: 30-second interval (lower CPU usage)
- **Dashboard Update**: Complete within 2 seconds (blocking operation acceptable)
- **Agent Skill Response**: <5 seconds for read operations, <10 seconds for write operations
- **Vault Size Support**: Up to 10,000 markdown files (performance test required)

### Silver Tier (AI Analysis)

- **File Watcher Polling**: 10-second interval (faster response to inbox changes)
- **AI Analysis Request**: 10-second timeout, offline fallback on failure
- **Priority Scoring**: <5 seconds for batch of 20 inbox items
- **Dashboard Update**: <2 seconds (same as Bronze)

### Gold Tier (Multi-Step Plans)

- **Plan Generation**: <15 seconds for 5-step plan
- **External API Calls**: 10-second timeout per integration (email, calendar)
- **Plan Execution Progress**: Update every 2 seconds during execution
- **Dashboard Update**: <2 seconds (same as Bronze/Silver)

### Platinum Tier (Autonomous)

- **Reflection Loop**: Max 5 iterations before human escalation
- **Error Recovery**: <10 seconds to detect and retry failed operation
- **Autonomous Decision**: <30 seconds per decision cycle (perceive, decide, act, reflect)
- **Dashboard Update**: <2 seconds (same as all tiers)

### Performance Testing

- **Load Test**: Create test vault with 10,000 markdown files, measure:
  - File watcher scan time (<5 seconds for full scan)
  - Dashboard update time (<2 seconds)
  - Memory usage (<500MB Python process)
- **Stress Test**: Simulate 50 file additions in 10 seconds, measure:
  - No race conditions (all files processed exactly once)
  - No dashboard corruption
  - No dropped events

## Compatibility Requirements

### Obsidian Compatibility

- **Obsidian Version**: 1.5+ (test with latest stable release)
- **Markdown Syntax**: CommonMark + Obsidian extensions
  - YAML frontmatter with `---` delimiters
  - Wiki links: `[[file]]`, `[[file|alias]]`, `[[file#heading]]`
  - Tags: `#tag`, `#nested/tag` (no spaces in tags)
  - Dataview queries: Preserve backtick blocks
  - Callouts: `> [!type] Title` format
- **Plugin Independence**: No dependency on proprietary Obsidian plugins
  - Use standard markdown only (parseable without Obsidian)
  - Dataview syntax supported but not required for core functionality

### Python Compatibility

- **Python Version**: 3.11+ (use type hints and dataclasses)
- **Type Hints**: Use `typing` module for all function signatures
- **Dataclasses**: Prefer `dataclasses` for data structures over dicts
- **Async/Await**: Use `asyncio` for file watchers (Silver+ tiers)
- **Dependencies**: Minimal external dependencies (list in `pyproject.toml`)
  - Bronze: `watchdog` (file monitoring), `pytest` (testing)
  - Silver: Add `anthropic` (Claude API), `pytest-asyncio`
  - Gold: Add `aiohttp` (async HTTP), integration libraries (email, calendar)

### Operating System Compatibility

- **Primary**: Linux (WSL Ubuntu) - development and testing environment
- **Secondary**: macOS, Windows 11 - best-effort compatibility
- **File Paths**: Use `pathlib.Path` for cross-platform path handling
- **Line Endings**: Handle both `\n` (Linux/macOS) and `\r\n` (Windows)
- **File Locking**: Use cross-platform file locking (e.g., `filelock` library)

### Claude Code Compatibility

- **MCP Servers**: Compatible with filesystem, github, context7 MCP servers
- **Agent Skills**: Callable via Claude Code's Python execution environment
- **Skill Naming**: Follow `/sp.<skill-name>` convention for custom skills
- **Async Execution**: Skills can run in background (e.g., file watchers)

### Integration Compatibility (Gold+ Tiers)

- **Email**: IMAP/SMTP standard protocols (no vendor lock-in)
- **Calendar**: CalDAV standard protocol (Google Calendar, iCloud, etc.)
- **Webhooks**: Standard HTTP POST with JSON payloads
- **Authentication**: Support `.env` file for API keys (never hardcoded)

## Governance

### Constitution Authority

- This constitution **supersedes all other development practices**
- All PRs, code reviews, and agent implementations must verify compliance with these principles
- Complexity beyond these principles must be explicitly justified in an ADR (Architecture Decision Record)

### Amendment Process

- Constitution changes require:
  1. Proposal via `/sp.constitution` command with rationale
  2. Review by project lead (human approval)
  3. Update of dependent templates (spec, plan, task templates)
  4. Migration plan if existing code affected
  5. Git commit with tag: `constitution-v<version>`

### Compliance Verification

- **Pre-Commit Checks**:
  - All tests passing (pytest)
  - Code coverage >= 80% for agent skills
  - No unhandled exceptions in main workflows

- **PR Review Checklist**:
  - [ ] Follows tier progression (no skipped tiers)
  - [ ] Agent skills have docstrings with Args, Returns, Raises, Example
  - [ ] Unit tests added for new agent skills (80% coverage)
  - [ ] Integration tests added for file watcher changes
  - [ ] Obsidian markdown syntax preservation verified
  - [ ] Performance requirements met (see Performance Requirements)
  - [ ] Offline fallback tested (Silver/Gold tiers)
  - [ ] Git commit references spec file section

- **Runtime Validation**:
  - Agent validates `Company_Handbook.md` before operations
  - Agent logs reasoning to `vault/Logs/` before every action
  - Dashboard backups created before every update
  - Graceful degradation on vault corruption

### Constitutional Principles Hierarchy

1. **Vault Integrity** (Principle II) - Never corrupt user data
2. **Local-First Architecture** (Principle III) - Default to offline operation
3. **Test-Driven Safety** (Principle IV) - Prove safety before deployment
4. **Agent Autonomy** (Principle I) - Earn trust through tiers
5. **Incremental Development** (Principle V) - No skipping ahead
6. **Code Organization** (Principle VI) - Clean boundaries

**Version**: 1.0.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-10
