# Personal AI Employee Constitution

## Core Principles

### I. Agent Autonomy & Tier Progression

**Autonomy must be earned through incremental capability:**

- **Bronze Tier (Monitoring)**: Agent monitors only, human reviews all changes manually
  - Zero autonomous actions
  - All changes require explicit human approval
  - 100% offline operation (no external API calls)
  - File watching and change detection only
  - Basic folder structure: /Inbox, /Needs_Action, /Done
  - Obsidian vault with Dashboard.md and Company_Handbook.md
  - One working Watcher script (Gmail OR file system monitoring)
  - All AI functionality implemented as Agent Skills

- **Silver Tier (Functional Assistant)**: Agent analyzes with AI and suggests priorities, human approves actions
  - **All Bronze features remain functional (backward compatible)**
  - Optional Claude API for task analysis (must work offline if API unavailable)
  - AI-powered priority ranking of inbox items (with graceful fallback to Bronze behavior)
  - Cost-aware API usage (<$0.10/day target)
  - Multiple Watcher scripts (Gmail + WhatsApp + LinkedIn)
  - Claude reasoning loop that creates Plan.md files
  - One working MCP server for external action (e.g., sending emails)
  - Human-in-the-loop approval workflow for sensitive actions
  - Basic scheduling via cron or Task Scheduler
  - Automatically post on LinkedIn about business to generate sales
  - Suggested actions presented to human for approval
  - No autonomous file modifications without approval

- **Gold Tier (Autonomous Employee)**: Agent proposes multi-step plans, executes with human approval gates
  - **All Bronze + Silver features remain functional (backward compatible)**
  - Full cross-domain integration (Personal + Business)
  - Odoo Community integration via MCP server (self-hosted, local)
  - Facebook, Instagram, Twitter (X) integration with post generation and summaries
  - Multiple MCP servers for different action types
  - Weekly Business and Accounting Audit with CEO Briefing generation
  - Error recovery and graceful degradation
  - Comprehensive audit logging
  - Ralph Wiggum loop for autonomous multi-step task completion
  - Multi-step workflow planning with human approval before execution
  - Optional external integrations (email, calendar) with graceful offline degradation
  - Plan execution with progress tracking
  - Task decomposition and delegation capabilities

- **Platinum Tier (Always-On Cloud + Local Executive)**: Fully autonomous with reflection loop, 24/7 cloud deployment
  - **All Bronze + Silver + Gold features remain functional (backward compatible)**
  - 24/7 cloud deployment (always-on watchers + orchestrator + health monitoring)
  - Work-Zone Specialization (domain ownership):
    - **Cloud owns**: Email triage + draft replies + social post drafts (draft-only, requires Local approval)
    - **Local owns**: Approvals, WhatsApp session, payments/banking, final "send/post" actions
  - Delegation via Synced Vault (file-based agent-to-agent communication):
    - Communication via /Needs_Action/<domain>/, /Plans/<domain>/, /Pending_Approval/<domain>/
    - Claim-by-move rule: First agent to move item from /Needs_Action to /In_Progress/<agent>/ owns it
    - Single-writer rule for Dashboard.md (Local only)
    - Cloud writes updates to /Updates/ or /Signals/, Local merges into Dashboard.md
  - Vault sync via Git or Syncthing (markdown/state only, secrets never sync)
  - Security rule: .env, tokens, WhatsApp sessions, banking credentials never sync to cloud
  - Odoo Community deployed on Cloud VM (24/7) with HTTPS, backups, health monitoring
  - Self-directed task execution with continuous reflection and error correction
  - Human oversight available but not required
  - Full audit trail of all autonomous decisions
  - Optional agent-to-agent (A2A) messaging (Phase 2 upgrade from file handoffs)

**Universal Requirements Across All Tiers:**
- All agent actions MUST log reasoning to `vault/Logs/` before execution
- Log format: `YYYY-MM-DD_HH-MM-SS_action-name.md` with YAML frontmatter (timestamp, tier, action, reasoning, outcome)
- **Never skip tiers** (no "Gold features" in Bronze implementation)
- **Each tier builds on previous tier's capabilities** (Bronze → Silver → Gold → Platinum)
- **Lower tier functionality never breaks when upgrading** (backward compatibility guaranteed)
- **Human oversight decreases gradually**: Bronze (100% manual) → Silver (AI-assisted) → Gold (plan & approve) → Platinum (fully autonomous)
- **All tiers respect vault integrity** and local-first architecture
- **All AI functionality must be implemented as Agent Skills** for reusability and maintainability

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
  - Rate limiting: Max 10 API calls/minute
  - Cost monitoring: Log API usage, alert if exceeding $0.10/day
  - Never send sensitive data to API (only task title + first 200 chars)

- **Gold Tier (Optional External Integrations):**
  - Optional email, calendar, webhook integrations
  - Social media integrations (Facebook, Instagram, Twitter/X)
  - Odoo Community integration (self-hosted, local JSON-RPC APIs)
  - Core functions (file watching, dashboard updates) remain local
  - External integration failures never block core operations
  - Each integration has offline fallback mode
  - Human approval required for all external actions (email send, social post, accounting transactions)

- **Platinum Tier (Distributed Cloud + Local):**
  - Cloud VM deployment for 24/7 always-on watchers
  - Local machine retains final approval authority and sensitive operations
  - Vault sync via Git or Syncthing (markdown/state only)
  - Secrets partitioning: Cloud never accesses .env, WhatsApp sessions, banking credentials
  - Cloud can draft but cannot execute: Email drafts, social post drafts, accounting journal entries
  - Local executes after approval: Send emails, post to social, confirm payments
  - Network partition tolerance: Both Cloud and Local continue operating independently, sync when reconnected

- **Universal Local-First Rules:**
  - All critical data persists in `vault/` folder (no external databases)
  - Configuration stored in `Company_Handbook.md` (human-editable markdown)
  - No cloud storage dependencies (works with local Obsidian vault only)
  - Network failures never corrupt local state
  - Vault is the source of truth for all agent state and task tracking

### IV. Silver Tier Specific Principles

**AI-Powered Priority Analysis with Graceful Degradation:**

- **Claude API Integration (Optional Feature):**
  - Priority analysis for inbox items using Claude API
  - Sentiment analysis for WhatsApp/email messages
  - Suggested action generation based on Company_Handbook.md rules
  - Never required for core functionality (Bronze features work without API)

- **Cost Awareness:**
  - Track API usage in `vault/Logs/API_Usage/YYYY-MM.md`
  - Alert human if daily cost exceeds $0.10
  - Batch API requests when possible (analyze multiple tasks in single call)
  - Cache API responses for duplicate/similar queries (24-hour TTL)

- **AI Safety (Silver Tier):**
  - Never send full message content to API (only title + first 200 chars)
  - Sanitize inputs: Remove email addresses, phone numbers, account numbers before API call
  - Rate limiting: Max 10 API calls/minute, max 100 calls/day
  - Timeout: 5 seconds max per API call, fail fast with offline fallback
  - Error handling: Log errors, fall back to Bronze behavior (Medium priority), never crash

- **Backward Compatibility Guarantee:**
  - Users without API key get full Bronze experience
  - All Bronze features work exactly the same in Silver
  - Silver features degrade gracefully: If API unavailable, use rule-based priority (Bronze behavior)
  - Configuration flag: `ENABLE_AI_ANALYSIS=true` in `.env` (default: false for safety)

- **Multiple Watcher Integration:**
  - Gmail Watcher: Poll every 2 minutes for unread emails matching filters
  - WhatsApp Watcher: Playwright-based, poll every 30 seconds for keywords (urgent, invoice, payment)
  - LinkedIn Watcher: Monitor feed, auto-post business updates (draft-only, human approval required)
  - All watchers log to `vault/Logs/Watcher_Activity/YYYY-MM-DD.md`

- **Plan Generation:**
  - Claude creates Plan.md files in `/Plans/` folder for multi-step tasks
  - Plan format: YAML frontmatter (objective, steps, approval_required, estimated_time)
  - Human approval required before executing any plan step
  - Plans track progress: `[ ]` pending, `[x]` completed, `[!]` blocked

- **MCP Server Integration (Silver):**
  - One MCP server required (email recommended for practicality)
  - MCP server for email sending (Gmail API or SMTP)
  - All MCP actions logged to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`
  - MCP server configuration in `~/.config/claude-code/mcp.json`
  - Never execute MCP actions without human approval (file-based approval workflow)

### V. Gold Tier Specific Principles

**Multi-Step Plan Execution with External Integrations:**

- **Cross-Domain Integration:**
  - Personal domain: Email, WhatsApp, calendar, personal file management
  - Business domain: Social media, accounting (Odoo), invoicing, client communications
  - Integration point: Company_Handbook.md defines domain boundaries and routing rules

- **Odoo Community Integration:**
  - Self-hosted Odoo Community (local deployment, no cloud SaaS)
  - MCP server for Odoo JSON-RPC API integration (Odoo 19+)
  - Draft accounting entries only (human approval required for posting)
  - Capabilities: Create invoices, log expenses, update contacts, generate reports
  - Weekly audit: Compare bank transactions with Odoo accounting entries, flag discrepancies

- **Social Media Automation:**
  - Facebook/Instagram: Auto-generate post drafts based on business goals, human approval before posting
  - Twitter/X: Auto-generate tweet drafts, human approval before posting
  - LinkedIn: Business updates, thought leadership content (already in Silver)
  - Posting schedule: Max 1 post/day per platform, respect platform rate limits
  - Content generation: Use Claude API to draft posts aligned with Company_Handbook.md tone/voice

- **Multiple MCP Servers:**
  - Email MCP: Send emails, draft replies, search inbox
  - Browser MCP: Navigate payment portals, fill forms, screenshot confirmations
  - Calendar MCP: Create events, update meetings, check availability
  - Social Media MCP: Post to Facebook/Instagram/Twitter, fetch engagement metrics
  - Odoo MCP: Accounting operations, invoice generation, expense logging

- **Weekly Business Audit & CEO Briefing:**
  - Scheduled task: Every Sunday night at 11:00 PM
  - Audit scope: Review all completed tasks, bank transactions, Odoo entries, social media performance
  - Generate CEO Briefing: `/Briefings/YYYY-MM-DD_Monday_Briefing.md`
  - Briefing sections: Executive Summary, Revenue (This Week, MTD, Trend), Completed Tasks, Bottlenecks, Proactive Suggestions
  - Proactive suggestions: Flag unused subscriptions, late payment patterns, revenue opportunities

- **Error Recovery & Graceful Degradation:**
  - Transient errors: Retry with exponential backoff (max 3 attempts)
  - Authentication errors: Pause operations, alert human, never retry automatically
  - Logic errors: Queue for human review, log error context
  - Data corruption: Quarantine file, restore from backup, alert human
  - System errors: Watchdog auto-restart, health monitoring

- **Ralph Wiggum Loop (Autonomous Multi-Step):**
  - Stop hook pattern: Intercept Claude exit, check task completion, re-inject prompt if incomplete
  - Completion strategies: Promise-based (`<promise>TASK_COMPLETE</promise>`) or file-movement (task in /Done)
  - Max iterations: 10 (prevent infinite loops)
  - Loop state: Tracked in `/In_Progress/<task_id>/state.md`
  - Human escalation: If max iterations reached without completion, create approval request

- **Comprehensive Audit Logging (Gold):**
  - All actions logged to `vault/Logs/` with structured format (JSON or YAML)
  - Log retention: Minimum 90 days, recommend 1 year for compliance
  - Log categories: Watcher_Activity, MCP_Actions, API_Usage, Error_Recovery, Human_Approvals
  - Audit trail: Every action links to triggering event, approval file, and outcome

### VI. Platinum Tier Specific Principles

**Fully Autonomous 24/7 Cloud Deployment with Agent-to-Agent Coordination:**

- **Cloud VM Deployment:**
  - Always-on watchers running on cloud VM (Oracle Cloud Free Tier, AWS, etc.)
  - Health monitoring: Watchdog process checks watcher PIDs every 60 seconds, auto-restart on failure
  - Process management: PM2, supervisord, or systemd for watcher persistence
  - Boot persistence: Watchers auto-start on VM reboot
  - Cloud environment variables: Separate `.env` file on cloud (API keys only, no secrets)

- **Work-Zone Specialization (Cloud vs Local):**
  - **Cloud Zone (Draft & Monitor)**:
    - Email triage: Read inbox, categorize, draft replies (save to `/Pending_Approval/Email/`)
    - Social media: Draft posts, schedule content (save to `/Pending_Approval/Social/`)
    - Monitoring: Watch for new emails, WhatsApp messages, social mentions
    - Accounting drafts: Create Odoo invoice drafts, expense entries (save to `/Pending_Approval/Accounting/`)
  - **Local Zone (Execute & Approve)**:
    - Human approval: Review files in `/Pending_Approval/`, move to `/Approved/` or `/Rejected/`
    - Execute actions: Send approved emails, post approved social content, confirm approved payments
    - Sensitive operations: WhatsApp session access, banking portal access, payment execution
    - Final authority: Local always has veto power over cloud drafts

- **Delegation via Synced Vault:**
  - **Communication Folders**:
    - `/Needs_Action/<domain>/`: New tasks waiting for assignment
    - `/In_Progress/<agent>/`: Tasks claimed by specific agent (Cloud or Local)
    - `/Pending_Approval/<domain>/`: Drafts waiting for human/Local approval
    - `/Approved/`: Tasks approved for execution
    - `/Rejected/`: Tasks rejected by human
    - `/Done/`: Completed tasks with outcomes
  - **Claim-by-Move Rule**: First agent to move task from `/Needs_Action/` to `/In_Progress/<agent>/` owns it (prevents duplicate work)
  - **Single-Writer Rule**: Only Local writes to `Dashboard.md` (prevents merge conflicts)
  - **Cloud Updates**: Cloud writes updates to `/Updates/<timestamp>.md`, Local merges into Dashboard.md

- **Vault Sync Strategy:**
  - **Phase 1 (File-Based)**: Git or Syncthing for vault synchronization
  - Git workflow: Cloud commits drafts → pushes to remote → Local pulls → approves → pushes results
  - Syncthing: Bidirectional sync, conflict resolution via timestamps
  - Sync scope: Only markdown files and state files (never sync .env, WhatsApp sessions, banking credentials)
  - Conflict resolution: Local always wins (Cloud rewrites on next sync)

- **Security Partitioning:**
  - Cloud `.gitignore`: `.env`, `WhatsApp_Session/`, `Banking_Credentials/`, `*.key`, `*.pem`
  - Local-only secrets: WhatsApp web session files, banking portal credentials, payment tokens
  - Cloud API keys: Gmail API (read-only scope), Social media APIs (post-draft scope), Odoo API (read-only scope)
  - Principle: Cloud can READ and DRAFT, Local can WRITE and EXECUTE

- **Odoo Cloud Deployment:**
  - Odoo Community on cloud VM (24/7 availability)
  - HTTPS with Let's Encrypt SSL certificate
  - Automated backups: Daily database dumps to cloud storage (encrypted)
  - Health monitoring: Check Odoo service every 5 minutes, alert on downtime
  - Cloud agent integration: Draft invoices, draft expense entries (no posting without Local approval)

- **Reflection Loop & Self-Correction:**
  - After every action, agent reflects: "Did this achieve the intended outcome?"
  - Reflection criteria: Task completion status, errors encountered, unexpected results
  - Self-correction: If outcome doesn't match expectation, create new plan or escalate to human
  - Learning: Log reflection outcomes to `/Reflections/YYYY-MM-DD.md`, identify recurring patterns
  - Max reflection iterations: 5 before human escalation

- **Agent-to-Agent Communication:**
  - **Phase 1 (File-Based)**: Agents communicate by writing files to shared vault folders
  - **Phase 2 (Optional A2A Messaging)**: Direct agent-to-agent messages (future upgrade)
  - Message format: YAML frontmatter (from_agent, to_agent, message_type, timestamp) + markdown body
  - Message types: `task_handoff`, `approval_request`, `status_update`, `error_escalation`
  - Audit trail: All A2A messages logged to `/Logs/A2A_Messages/YYYY-MM-DD.md`

- **Platinum Demo Requirements (Minimum Passing Gate):**
  - Email arrives while Local is offline → Cloud drafts reply + writes approval file
  - When Local returns online, user reviews draft in `/Pending_Approval/Email/`
  - User approves by moving file to `/Approved/`
  - Local executes send via Email MCP
  - Action logged to `/Logs/MCP_Actions/`, task moved to `/Done/`
  - Demonstrates: Cloud autonomy, Local authority, HITL safety, audit trail

### VII. Universal Principles Across All Tiers

**Foundational Rules That Apply to Bronze, Silver, Gold, and Platinum:**

- **Tier Progression Mandate:**
  - Build sequentially: Complete Bronze → then Silver → then Gold → then Platinum
  - Never skip tiers or mix tier features (no "Gold shortcuts" in Bronze implementation)
  - Each tier inherits ALL features from previous tiers (cumulative capability)
  - Feature flag approach: `TIER=bronze|silver|gold|platinum` in `.env`

- **Backward Compatibility (Non-Negotiable):**
  - Upgrading from Bronze to Silver: All Bronze features work identically
  - Upgrading from Silver to Gold: All Bronze + Silver features work identically
  - Upgrading from Gold to Platinum: All Bronze + Silver + Gold features work identically
  - Downgrade safety: If `.env` sets `TIER=bronze`, higher-tier features disabled but don't break

- **Human Oversight Gradient:**
  - Bronze: 100% human review (agent monitors, human acts)
  - Silver: AI-assisted review (agent suggests, human approves and acts)
  - Gold: Plan-based approval (agent plans multi-step workflows, human approves plan, agent executes)
  - Platinum: Autonomous with reflection (agent acts independently, human can audit/override)

- **Vault Integrity (Sacred Principle):**
  - Never corrupt Obsidian markdown syntax (YAML frontmatter, wiki links, tags, dataview, callouts)
  - Atomic file operations: Read → Validate → Modify → Validate → Write
  - Race condition handling: File locking, timestamp-based conflict detection, max 3 retries
  - Backup before modify: Critical files get `.bak.YYYY-MM-DD_HH-MM-SS` backups (keep last 5, prune after 7 days)

- **Local-First Architecture (Default):**
  - All critical data persists in `vault/` folder (no external databases required)
  - Configuration in human-editable markdown (`Company_Handbook.md`)
  - Network failures never corrupt local state
  - External APIs are optional enhancements (graceful degradation if unavailable)

- **Agent Skills Mandate:**
  - All AI functionality implemented as reusable Agent Skills (not inline scripts)
  - Skills location: `.claude/skills/` or project skills directory
  - Skill documentation: `SKILL.md` with examples, parameters, expected outputs
  - Skills callable by: Claude Code CLI, background watchers, cron jobs

- **Audit Logging (All Tiers):**
  - Every agent action logged to `vault/Logs/` before execution
  - Log format: `YYYY-MM-DD_HH-MM-SS_action-name.md` with YAML frontmatter
  - Frontmatter fields: timestamp, tier, action, reasoning, outcome, human_approved (true/false)
  - Log retention: Minimum 90 days, recommend 1 year for compliance and learning

### VIII. Test-Driven Safety

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

1. **Vault Integrity** - Never corrupt user data (applies to all tiers)
2. **Local-First Architecture** - Default to offline operation (applies to all tiers)
3. **Backward Compatibility** - Lower tier features never break when upgrading (Universal Principle VII)
4. **Test-Driven Safety** - Prove safety before deployment (applies to all tiers)
5. **Agent Autonomy & Tier Progression** (Principle I) - Earn trust through incremental tiers
6. **Silver Tier Principles** (Principle IV) - AI-powered analysis with graceful fallback
7. **Gold Tier Principles** (Principle V) - Multi-step plans with external integrations
8. **Platinum Tier Principles** (Principle VI) - Autonomous 24/7 operation with reflection
9. **Incremental Development** - No skipping tiers, sequential implementation
10. **Code Organization** - Clean boundaries between components

**Tier Implementation Order (Non-Negotiable):**
1. Bronze (Foundation) → 2. Silver (AI-Assisted) → 3. Gold (Plan & Execute) → 4. Platinum (Autonomous)

**Version**: 2.0.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-11 | **Amendment**: Added Silver, Gold, and Platinum tier principles based on Personal AI Employee Hackathon requirements
