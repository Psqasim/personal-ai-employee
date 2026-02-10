---
id: 001
title: Personal AI Employee Development Principles
stage: constitution
date: 2026-02-10
surface: agent
model: claude-sonnet-4-5
feature: none
branch: main
user: ps_qasim
command: /sp.constitution
labels: ["constitution", "agent-autonomy", "vault-integrity", "local-first", "test-driven", "obsidian"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - (None - constitution creation doesn't require tests)
---

## Prompt

/sp.constitution

Create development principles for building a Personal AI Employee agent system following Hackathon 0 requirements. Focus on these key areas:

AGENT AUTONOMY PRINCIPLES
- Bronze tier: Agent monitors only, human reviews all changes manually
- Silver tier: Agent analyzes with AI and suggests priorities, human approves actions
- Gold tier: Agent proposes multi-step plans, human approves before execution
- Platinum tier: Fully autonomous with reflection loop, human oversight optional
- All agent actions must log reasoning to vault/Logs/ before execution

VAULT INTEGRITY STANDARDS
- Never corrupt Obsidian markdown syntax (YAML frontmatter, wiki links [[]], tags #)
- Use atomic file operations: read → validate → modify → validate → write
- File watcher must handle race conditions (multiple simultaneous file changes)
- Always backup vault/Dashboard.md before updates (keep .bak file)
- If Obsidian vault is locked or corrupted, gracefully degrade (log error, notify human)

LOCAL-FIRST ARCHITECTURE
- Bronze tier: 100% offline, zero external API calls
- Silver tier: Optional Claude API for task analysis (must work offline if API unavailable)
- Gold tier: Optional external integrations (email, calendar) but core functions local
- All critical data persists in vault/ folder (no external databases)
- Configuration stored in Company_Handbook.md (human-editable markdown)

INCREMENTAL CAPABILITY DEVELOPMENT
- Each tier builds on previous (Bronze → Silver → Gold → Platinum)
- Never skip tiers (no "Gold features" in Bronze implementation)
- Clear separation: .specify/ for dev artifacts, vault/ for product deliverables
- Use feature branches: bronze-tier, silver-tier, gold-tier, platinum-tier
- Git commits must reference spec files (e.g., "Implements Bronze spec section 2.1")

TESTING & SAFETY REQUIREMENTS
- Every agent skill must have pytest unit tests in tests/ directory
- File watchers must include integration tests (test with real vault/ folder)
- Mock external APIs in tests (no real API calls during testing)
- Dashboard.md updates must be idempotent (running twice = same result)
- Company_Handbook.md validation: check for required sections before agent starts

CODE ORGANIZATION STANDARDS
- .specify/: Development workspace (specs, plans, tasks, PHRs, ADRs)
- vault/: Product deliverable (only Obsidian-compatible markdown files)
- agent_skills/: Reusable Python modules (callable by Claude Code and watchers)
- scripts/: Background processes (file watchers, dashboard updaters)
- tests/: Pytest test suites (unit tests for skills, integration tests for watchers)

DOCUMENTATION REQUIREMENTS
- Company_Handbook.md: Agent operational rules (read at runtime by agent)
- constitution.md: Development principles (read by human developers)
- Every agent skill: Docstring with Args, Returns, Raises, Example usage
- README.md: Setup instructions for Bronze tier (assume user has Obsidian + Python)
- Dashboard.md format: Markdown table with columns [File, Added, Status, Priority]

PERFORMANCE REQUIREMENTS
- Bronze tier watcher: 30-second polling interval (lower CPU usage)
- Silver tier watcher: 10-second polling interval (faster response)
- Dashboard.md updates: Complete within 2 seconds (no blocking operations)
- Agent skill responses: <5 seconds for read ops, <10 seconds for write ops
- Vault size limit: Support up to 10,000 markdown files (performance test required)

COMPATIBILITY REQUIREMENTS
- Obsidian version: 1.5+ (test with latest stable release)
- Python version: 3.11+ (use type hints and dataclasses)
- Operating systems: Linux (WSL Ubuntu), macOS, Windows 11
- Claude Code: Compatible with MCP servers (filesystem, github, context7)
- No dependency on proprietary Obsidian plugins (use standard markdown only)

## Response snapshot

Created comprehensive constitution with six core principles and detailed standards:

**Core Principles:**
1. **Agent Autonomy & Tier Progression**: Four-tier system (Bronze/Silver/Gold/Platinum) with clear capability boundaries and universal logging requirements
2. **Vault Integrity & Obsidian Compatibility**: Atomic file operations, race condition handling, backup strategies, graceful degradation
3. **Local-First Architecture**: Offline-first design with optional API enhancements per tier
4. **Test-Driven Safety**: 80% coverage requirement, integration tests, idempotency tests, performance tests
5. **Incremental Development Discipline**: Feature branch strategy, git commit discipline, tier completion criteria
6. **Code Organization & Modularity**: Enforced directory structure with single responsibility principle

**Additional Sections:**
- Testing & Safety Standards (80% coverage, pre-deployment checklist)
- Documentation Standards (Company_Handbook.md, README.md, docstring format, Dashboard.md table format)
- Performance Requirements (polling intervals, response times, vault size support per tier)
- Compatibility Requirements (Obsidian 1.5+, Python 3.11+, cross-platform, MCP server integration)

**Governance:**
- Constitution supersedes all other practices
- Amendment process requires human approval and migration plan
- Compliance verification at pre-commit, PR review, and runtime
- Constitutional principles hierarchy prioritizes vault integrity first

**File Created:** `.specify/memory/constitution.md` (Version 1.0.0, Ratified 2026-02-10)

## Outcome

- ✅ Impact: Established comprehensive development principles for Personal AI Employee agent system with clear tier progression, safety standards, and compliance requirements
- 🧪 Tests: No tests required for constitution creation (development principles document)
- 📁 Files: Created `.specify/memory/constitution.md` with 6 core principles, testing standards, documentation requirements, performance benchmarks, and compatibility matrix
- 🔁 Next prompts:
  - `/sp.specify <feature-name>` - Create Bronze tier specification
  - `/sp.plan <feature-name>` - Design Bronze tier architecture
  - Review constitution and suggest amendments if needed
- 🧠 Reflection: Constitution provides strong foundation for incremental development with vault integrity prioritized above all else. Tier progression ensures safety before autonomy. Performance and compatibility requirements are measurable and testable.

## Evaluation notes (flywheel)

- Failure modes observed: None (constitution creation is non-executable artifact)
- Graders run and results (PASS/FAIL): N/A (manual review required)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Create Bronze tier spec following constitution principles to validate constitution completeness
