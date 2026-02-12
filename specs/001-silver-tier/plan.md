# Implementation Plan: Silver Tier - Functional AI Assistant

**Branch**: `001-silver-tier` | **Date**: 2026-02-11 | **Spec**: [specs/001-silver-tier/spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-silver-tier/spec.md`

## Summary

Silver Tier upgrades Bronze with **AI-powered analysis and multi-channel monitoring** while maintaining 100% backward compatibility. The system adds intelligent priority analysis (High/Medium/Low) via Claude API, task categorization (Work/Personal/Urgent), multiple communication watchers (Gmail, WhatsApp, LinkedIn), Plan.md generation for complex workflows, and cost-aware API usage (<$0.10/day). All AI features gracefully degrade to Bronze behavior when API unavailable.

**Primary Requirement**: Analyze inbox tasks using Claude API to assign priorities and categories, monitor Gmail (2min) and WhatsApp (30sec) for new messages, generate LinkedIn post drafts, create Plan.md files for multi-step tasks, while maintaining Bronze compatibility and cost awareness.

**Technical Approach**: Modular architecture with AI analyzer module (Claude SDK with retry/timeout/caching), async watcher processes (Gmail API OAuth2, WhatsApp Playwright, LinkedIn MCP draft-only), Plan generator (multi-shot prompting), and graceful fallback layer (Bronze defaults when API unavailable). Cost tracking via log-based analysis with daily alerts.

## Technical Context

**Language/Version**: Python 3.11+ (async/await for watchers, type hints, dataclasses)
**Primary Dependencies**:
- `anthropic>=0.18.0` (Claude API client for AI analysis)
- `google-auth>=2.16.0`, `google-api-python-client>=2.80.0` (Gmail OAuth2 + API)
- `playwright>=1.40.0` (WhatsApp Web automation)
- `aiohttp>=3.9.0` (async HTTP for API calls)
- `watchdog>=3.0.0`, `pyyaml>=6.0` (Bronze dependencies - inherited)

**Storage**: Local filesystem (vault/) + API response cache (24h TTL in vault/Logs/API_Cache/)
**Testing**: pytest 7.0+, pytest-asyncio 0.21+, pytest-cov 4.0+ (target: 80% coverage, including async tests)
**Target Platform**: WSL Ubuntu 22.04+ (primary), macOS 13+, Windows 11 (secondary)
**Project Type**: Single project with async watchers (agent_skills/ + scripts/ + watchers/)

**Performance Goals**:
- AI analysis: <5 seconds (API call + processing)
- Gmail watcher: Process 10 emails in <30 seconds
- WhatsApp watcher: Detect keywords in <30 seconds
- Dashboard update with AI: <5 seconds total (3s API + 2s write)
- Cache hit rate: >30% (reduce API costs)

**Constraints**:
- Backward compatibility: All Bronze features work identically when ENABLE_AI_ANALYSIS=false
- Cost limit: <$0.10/day under normal usage (100 tasks/day)
- API timeout: 5 seconds max per call (graceful fallback to Bronze)
- Rate limiting: Max 10 API calls/minute, max 100 calls/day
- Security: Sanitize inputs (remove emails, phones, accounts), send only title + 200 chars to API
- Human-in-the-loop: All MCP actions require approval via Pending_Approval/ workflow

**Scale/Scope**:
- Maintain Bronze vault limit: 1000 markdown files
- 3 async watchers (Gmail, WhatsApp, LinkedIn generator)
- 1 MCP server (email sending)
- 44 functional requirements (vs Bronze 25), 16 non-functional requirements
- 7 user stories (AI analysis, categorization, 3 watchers, plan generation, cost control)

## Constitution Check

*GATE: Must pass before implementation. Aligned with Constitution Section IV - Silver Tier Principles.*

✅ **Bronze Compatibility First (FR-S041 to FR-S044)**:
- All Bronze functional requirements remain unchanged
- ENABLE_AI_ANALYSIS flag controls Silver features (default: false for safety)
- Users without CLAUDE_API_KEY receive full Bronze experience
- Silver performance targets maintain Bronze limits (Dashboard <2s, vault 1000 files)

✅ **AI-Powered Priority Analysis with Graceful Degradation (Section IV.1)**:
- Claude API integration for priority (High/Medium/Low) and category (Work/Personal/Urgent)
- 5-second timeout with fallback to Bronze defaults (Priority="Medium", Category="Uncategorized")
- Input sanitization: Remove PII, send only title + first 200 chars (FR-S005, NFR-S-SEC-002)
- Never crash on API failure (FR-S002, NFR-S-REL-001)

✅ **Cost Awareness (Section IV.2)**:
- Track API usage in vault/Logs/API_Usage/YYYY-MM.md (FR-S008)
- Alert if daily cost exceeds $0.10 (FR-S009, NFR-S-COST-001)
- Batch API requests when possible (reduce per-request overhead) (NFR-S-COST-002)
- Cache responses for 24 hours (FR-S010, NFR-S-REL-003)

✅ **AI Safety (Section IV.3)**:
- Rate limiting: Max 10 calls/minute, max 100 calls/day (FR-S007, NFR-S-REL-004)
- Sanitize inputs: Remove emails, phones, account numbers via regex (FR-S005)
- Timeout: 5 seconds max per API call, fail fast with offline fallback (FR-S006)
- Error handling: Log errors, fall back to Bronze, never crash (FR-S002, NFR-S-REL-001)

✅ **Multiple Watcher Integration (Section IV.5)**:
- Gmail Watcher: Poll every 2 minutes for "is:important" emails (FR-S015)
- WhatsApp Watcher: Poll every 30 seconds for keywords (FR-S021)
- LinkedIn Generator: Scheduled posts (daily/weekly) with business goal alignment (FR-S026)
- All watchers log to vault/Logs/Watcher_Activity/ (FR-S006 inherited from Bronze)

✅ **Plan Generation (Section IV.6)**:
- Claude creates Plan.md for multi-step tasks (keywords: "plan", "campaign", "project") (FR-S031)
- YAML frontmatter: objective, steps, approval_required=true (FR-S033)
- Numbered checklist with dependencies (FR-S034, FR-S035)
- Human approval workflow via Pending_Approval/ (FR-S037)

✅ **MCP Server Integration (Section IV.7)**:
- One MCP server required (email recommended) (FR-S038)
- Human-in-the-loop approval for all actions (FR-S040, NFR-S-SEC-005)
- Log all MCP actions to vault/Logs/MCP_Actions/ (FR-S039)

✅ **Vault Integrity (Principle II - Inherited from Bronze)**:
- Atomic file operations maintained (Bronze FR-B023)
- Dashboard.md backups before updates (Bronze FR-B008)
- Obsidian markdown syntax preservation (Bronze NFR-B-COMPAT-004)

✅ **Local-First Architecture (Principle III - Enhanced for Silver)**:
- Core functions remain local (Bronze compatibility)
- External APIs optional (Gmail, WhatsApp, Claude) with offline fallback
- Secrets in .env, never in code (NFR-S-SEC-001)
- Network failures never corrupt local state (Bronze NFR-B-REL-002)

**Constitution Alignment**: PASS - All Silver tier principles satisfied. Backward compatibility guaranteed.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Project Structure

### Documentation (this feature)

```text
specs/001-silver-tier/
├── spec.md              # Feature specification (created by /sp.specify)
├── plan.md              # This file (implementation architecture)
├── research.md          # Phase 0: Technology research and decisions
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Setup and first-run instructions
├── contracts/           # Phase 1: API contracts and schemas
│   ├── claude-api.md    # Claude API integration contract
│   ├── gmail-api.md     # Gmail API integration contract
│   └── mcp-email.md     # Email MCP server contract
├── checklists/
│   └── requirements.md  # Spec quality validation (already created)
└── tasks.md             # Phase 2: Implementation tasks (created via /sp.tasks)

.specify/memory/
└── constitution.md      # Development principles (Section IV - Silver)

history/prompts/001-silver-tier/
├── 0001-silver-tier-specification.spec.prompt.md
└── 0002-silver-tier-implementation-plan.plan.prompt.md
```

### Source Code (repository root)

```text
agent_skills/                                  # Reusable Python modules
├── __init__.py                                # Package initialization
├── vault_watcher.py                           # Bronze: 4 Agent Skills API functions (inherited)
├── dashboard_updater.py                       # Bronze: Dashboard manipulation (inherited)
├── ai_analyzer.py                             # Silver: Claude API integration
│   ├── analyze_priority()                     # Assign High/Medium/Low
│   ├── categorize_task()                      # Assign Work/Personal/Urgent
│   ├── generate_plan()                        # Multi-step Plan.md creation
│   ├── _call_claude_api()                     # Internal: API call with retry/timeout
│   ├── _cache_response()                      # Internal: 24h cache management
│   └── _sanitize_input()                      # Internal: Remove PII before API call
├── api_usage_tracker.py                       # Silver: Cost monitoring
│   ├── log_api_call()                         # Record usage to vault/Logs/API_Usage/
│   ├── check_daily_cost()                     # Alert if >$0.10
│   └── get_cost_report()                      # Generate monthly summary
└── plan_generator.py                          # Silver: Plan.md file creation
    ├── create_plan_md()                       # Generate Plan.md from task
    └── parse_plan_progress()                  # Track step completion

scripts/                                        # Entry points (not importable)
├── init_vault.py                              # Bronze: One-time vault setup (inherited)
└── watch_inbox.py                             # Bronze: File watcher (inherited, enhanced for Silver)

watchers/                                       # Silver: Async watcher processes
├── __init__.py                                # Package initialization
├── gmail_watcher.py                           # Gmail API polling (2min interval)
│   ├── main()                                 # Entry point with signal handling
│   ├── poll_gmail()                           # Async polling loop
│   ├── fetch_important_emails()               # Gmail API: unread + is:important
│   ├── create_email_task()                    # Write EMAIL_{id}.md to vault/Inbox/
│   └── track_processed_ids()                  # Prevent duplicates
├── whatsapp_watcher.py                        # WhatsApp Web monitoring (30sec interval)
│   ├── main()                                 # Entry point with session management
│   ├── poll_whatsapp()                        # Async polling loop with Playwright
│   ├── check_session()                        # Detect session expiry
│   ├── find_keyword_messages()                # Search for urgent/invoice/payment/help/asap
│   └── create_whatsapp_task()                 # Write WHATSAPP_{id}.md to vault/Inbox/
└── linkedin_generator.py                      # LinkedIn post draft generator (scheduled)
    ├── main()                                 # Entry point with cron integration
    ├── read_business_goals()                  # Parse Company_Handbook.md
    ├── draft_post()                           # Claude API: generate post content
    └── save_draft()                           # Write to vault/Pending_Approval/LinkedIn/

tests/                                          # Pytest test suite
├── unit/                                       # Unit tests
│   ├── test_vault_watcher.py                  # Bronze: API functions (inherited)
│   ├── test_dashboard_updater.py              # Bronze: Atomic writes (inherited)
│   ├── test_ai_analyzer.py                    # Silver: AI analysis with mocks
│   ├── test_api_usage_tracker.py              # Silver: Cost tracking
│   └── test_plan_generator.py                 # Silver: Plan.md generation
├── integration/                                # Integration tests
│   ├── test_end_to_end.py                     # Bronze: Drop file → Detect → Update (inherited)
│   └── test_silver_end_to_end.py              # Silver: AI analysis → Priority → Dashboard
└── fixtures/                                   # Test data
    ├── sample_vault/                          # Mock vault (Bronze)
    ├── mock_claude_responses.json             # Silver: AI API responses
    └── mock_gmail_data.json                   # Silver: Gmail API responses

vault/                                          # Product deliverable (Obsidian vault)
├── Inbox/                                      # User drops tasks + watcher output (EMAIL_*, WHATSAPP_*)
├── Needs_Action/                               # Manual move (Bronze) or Plan execution (Silver)
├── Done/                                       # Manual move (Bronze/Silver)
├── Plans/                                      # Silver: Auto-generated Plan.md files
├── Pending_Approval/                           # Silver: Human-in-the-loop approval workflow
│   ├── Email/                                  # Email send approvals
│   ├── LinkedIn/                               # LinkedIn post drafts
│   └── MCP/                                    # Generic MCP action approvals
├── Logs/                                       # System-generated logs
│   ├── watcher-YYYY-MM-DD.md                  # Bronze: File watcher events (inherited)
│   ├── gmail_watcher_errors.md                # Silver: Gmail watcher errors
│   ├── whatsapp_watcher_errors.md             # Silver: WhatsApp watcher errors
│   ├── API_Usage/YYYY-MM.md                   # Silver: API cost tracking
│   ├── API_Cache/                             # Silver: 24h response cache
│   │   └── {hash}.json                        # Cached Claude API responses
│   └── MCP_Actions/YYYY-MM-DD.md              # Silver: MCP action log
├── Dashboard.md                                # Auto-maintained task table (Bronze + Silver columns)
└── Company_Handbook.md                         # Human-editable configuration (Bronze + Silver config)

.env                                            # Silver: Environment variables (NEVER commit)
├── # Bronze config (inherited)
├── VAULT_PATH=/path/to/vault
├──
├── # Silver additions
├── ENABLE_AI_ANALYSIS=true                    # Toggle Silver features
├── CLAUDE_API_KEY=sk-ant-api03-xxx           # From Anthropic Console
├── CLAUDE_MODEL=claude-3-5-sonnet-20241022   # Model for analysis
├──
├── # Gmail watcher
├── GMAIL_CREDENTIALS_PATH=/path/to/gmail_credentials.json
├── GMAIL_POLL_INTERVAL=120                    # Seconds (2 minutes)
├──
├── # WhatsApp watcher
├── WHATSAPP_SESSION_PATH=/path/to/whatsapp_session
├── WHATSAPP_KEYWORDS=urgent,invoice,payment,help,asap
├──
├── # LinkedIn
├── LINKEDIN_POSTING_FREQUENCY=daily           # daily|weekly|biweekly
├── LINKEDIN_BUSINESS_GOALS_SECTION=Business Goals  # Section in Company_Handbook.md
├──
├── # Cost control
├── API_DAILY_COST_LIMIT=0.10                  # USD
├── API_RATE_LIMIT_PER_MIN=10                  # Max calls per minute
└── API_CACHE_DURATION=86400                   # Seconds (24 hours)
```

**Structure Decision**: Single project with async watcher submodule chosen because Silver tier builds on Bronze foundation (reuse agent_skills/) while adding async watchers for Gmail/WhatsApp/LinkedIn. The `watchers/` submodule contains async entry points (separate processes), while `agent_skills/` contains synchronous reusable modules callable by Claude Code. This aligns with Constitution Principle VI (Code Organization) and maintains Bronze compatibility.

## Complexity Tracking

> **No complexity violations detected**. Silver tier follows all constitution principles with backward compatibility guarantee. AI features are optional enhancements (ENABLE_AI_ANALYSIS flag) with graceful Bronze fallback.


## 1. Scope and Dependencies

### In Scope

**Silver Tier Core Functionality**:
- AI-powered priority analysis (High/Medium/Low) via Claude API with 5-second timeout
- Task categorization (Work/Personal/Urgent) based on content analysis
- Gmail watcher: Poll every 2 minutes for "is:important" emails, create EMAIL_{id}.md files
- WhatsApp watcher: Poll every 30 seconds for keyword messages ("urgent", "invoice", "payment", "help", "asap")
- LinkedIn generator: Draft posts based on Company_Handbook.md business goals (scheduled daily/weekly)
- Plan.md generation: Multi-step workflows for tasks with keywords ("plan", "campaign", "project")
- Cost tracking: Log API usage to vault/Logs/API_Usage/, alert if >$0.10/day
- MCP server integration: One email MCP server with human-in-the-loop approval workflow

**Bronze Tier Compatibility** (Inherited):
- All 25 Bronze functional requirements remain unchanged (FR-B001 to FR-B025)
- File watcher polling vault/Inbox/ every 30 seconds
- Dashboard.md updates with atomic writes and backups
- Agent Skills API (4 functions) for Claude Code integration
- 100% offline operation when ENABLE_AI_ANALYSIS=false

**Boundaries**:
- AI analysis optional (ENABLE_AI_ANALYSIS flag, default: false)
- Graceful fallback to Bronze when API unavailable (Priority="Medium", Category="Uncategorized")
- Cost limit: <$0.10/day with caching (24h TTL) and batching
- Human approval required for all MCP actions (email send, LinkedIn post)
- Maintain Bronze vault limit: 1000 markdown files

### Out of Scope

**Deferred to Gold Tier**:
- Multi-step plan execution (Silver creates plans, Gold executes autonomously)
- Odoo accounting integration (self-hosted, MCP server)
- Facebook/Instagram/Twitter social media automation
- Weekly Business Audit & CEO Briefing generation
- Cross-domain integration orchestration (Personal + Business workflows)

**Deferred to Platinum Tier**:
- Reflection loops and self-correction
- 24/7 cloud deployment (always-on VM)
- Agent-to-agent communication (Cloud + Local coordination)
- Automatic failover and health monitoring

**Never in Silver (Safety Boundaries)**:
- Autonomous email sending without approval
- Autonomous LinkedIn posting without approval
- Autonomous file deletion
- Code execution from vault files
- Access to parent directories or system files

### External Dependencies

**Python Packages** (managed via pyproject.toml):
- `anthropic>=0.18.0`: Claude API client (AI analysis)
- `google-auth>=2.16.0`, `google-api-python-client>=2.80.0`: Gmail OAuth2 + API
- `playwright>=1.40.0`: WhatsApp Web automation (headless Chromium)
- `aiohttp>=3.9.0`: Async HTTP for API calls
- `watchdog>=3.0.0`, `pyyaml>=6.0`: Bronze dependencies (inherited)

**Development Dependencies**:
- `pytest>=7.0`, `pytest-cov>=4.0`, `pytest-asyncio>=0.21`: Testing (async tests)
- `black>=23.0`, `mypy>=1.0`: Code formatting, type checking

**External Tools** (user-installed):
- Obsidian Desktop App v1.5+ (same as Bronze)
- Python 3.11+ (async/await support)
- Playwright browsers: `playwright install chromium` (WhatsApp watcher)
- Gmail API credentials: OAuth2 client from Google Cloud Console
- Claude API key: From Anthropic Console (https://console.anthropic.com/)
- PM2: Process manager for watchers (`npm install -g pm2`)

**External APIs** (optional, with offline fallback):
- Claude API: AI analysis (priority, categorization, plan generation)
- Gmail API: Email monitoring ("is:important" filter)
- WhatsApp Web: Keyword message monitoring (Playwright automation)
- Email MCP Server: Send emails with human approval

**System Dependencies**:
- Filesystem access to vault/ and ~/.config/ (read/write permissions)
- Network access for API calls (offline fallback if unavailable)
- At least 8GB RAM (Bronze <100MB + watchers <200MB + Playwright <200MB = <500MB total)
- At least 2GB disk space (vault 1GB + API cache 100MB + Playwright 900MB)

### Dependency Ownership

| Dependency | Owner | Risk Level | Mitigation |
|------------|-------|------------|------------|
| anthropic | External (PyPI) | Medium | Official Anthropic SDK, stable API, version pinning >=0.18.0 |
| google-api-python-client | External (Google) | Low | Official Google SDK, widely used, stable OAuth2 flow |
| playwright | External (Microsoft) | Low | Official Microsoft tool, stable browser automation, version >=1.40.0 |
| Claude API | External (Anthropic) | Medium | Rate limiting, cost tracking, graceful fallback to Bronze |
| Gmail API | External (Google) | Medium | OAuth2 token refresh, error handling (403/429/500) |
| WhatsApp Web | External (Meta) | High | Unofficial automation (TOS risk), session expiry detection, fallback notification |
| PM2 | External (Node) | Low | Industry-standard process manager, version >=5.0.0 |

**High-Risk Dependency: WhatsApp Web**
- **Risk**: Meta may block automation, change UI, or enforce stricter TOS
- **Mitigation**: Detect session expiry, create notification in vault/Needs_Action/, pause watcher gracefully
- **Alternative**: Manual WhatsApp monitoring (Bronze-style, user copies important messages to Inbox/)


## 2. Key Decisions and Rationale

### Decision 1: AI Analysis with Graceful Bronze Fallback

**Options Considered**:
1. **Always-on AI analysis**: Require Claude API key, fail if unavailable
2. **Graceful fallback with flag**: ENABLE_AI_ANALYSIS flag, fall back to Bronze if API unavailable
3. **Hybrid mode**: Use rule-based analysis as primary, AI as enhancement

**Trade-offs**:
- **Always-on**: Simplest code, but breaks backward compatibility
- **Graceful fallback**: More complexity (if/else branches), but maintains Bronze compatibility
- **Hybrid**: Best UX, but complex logic (rule-based + AI coordination)

**Decision**: **Option 2: Graceful fallback with ENABLE_AI_ANALYSIS flag**

**Rationale**:
- Constitution Section IV: "Backward Compatibility Guarantee" (FR-S041 to FR-S044)
- Spec requirement: "Users without API key get full Bronze experience" (FR-S043)
- Spec NFR-S-REL-001: "AI analysis failure rate <5%, fall back to Bronze"
- Testable: Integration tests can disable AI and verify Bronze behavior
- Reversible: Can add hybrid mode in Gold tier if needed

**Implementation Pattern**:
```python
def analyze_task(task_title: str, task_content: str) -> dict:
    if not os.getenv("ENABLE_AI_ANALYSIS", "false").lower() == "true":
        return {"priority": "Medium", "category": "Uncategorized", "bronze_mode": True}
    
    try:
        result = call_claude_api(task_title, task_content)
        return result
    except (APIError, TimeoutError) as e:
        log_warning(f"AI analysis failed, using Bronze defaults: {e}")
        return {"priority": "Medium", "category": "Uncategorized", "fallback": True}
```

---

### Decision 2: Async Watchers with Separate Processes (PM2 Orchestration)

**Options Considered**:
1. **Separate processes with PM2**: Each watcher runs independently (gmail_watcher.py, whatsapp_watcher.py)
2. **Single event loop with asyncio.gather**: One process, 3 async tasks
3. **Threading with ThreadPoolExecutor**: Each watcher in separate thread

**Trade-offs**:
- **Separate processes**: Process isolation, independent restart, PM2 management, multi-process complexity
- **Single event loop**: Simpler deployment, one process to monitor, but one task blocking affects all
- **Threading**: Simpler than multiprocessing, but GIL contention, blocking I/O not parallelized

**Decision**: **Option 1: Separate processes with PM2**

**Rationale**:
- Research finding: Hackathon doc recommends PM2 for always-on watchers (see research.md section 2)
- Spec NFR-S-REL-002: "Watchers must recover from errors independently within 2 minutes"
- Process isolation: WhatsApp session expiry doesn't crash Gmail watcher
- PM2 features: Auto-restart on crash, log management, cron scheduling for LinkedIn
- Aligns with Bronze watcher pattern (watch_inbox.py runs as separate process)

**Reversible**: Yes, can migrate to asyncio.gather if PM2 adds too much complexity

---

### Decision 3: 24-Hour API Response Caching for Cost Optimization

**Options Considered**:
1. **No caching**: Call Claude API for every task (simplest, but expensive)
2. **24-hour TTL cache**: Hash(task_title) → cached priority/category
3. **LRU cache with 1000 entries**: Keep most recent 1000 responses
4. **Persistent cache in SQLite**: Store all responses indefinitely

**Trade-offs**:
- **No caching**: $0.12/day for 100 tasks (exceeds $0.10 limit)
- **24-hour TTL**: $0.084/day (30% hit rate), file-based (vault/Logs/API_Cache/)
- **LRU cache**: Memory-based, lost on restart, hard to audit
- **SQLite**: Permanent storage, but adds dependency, vault integrity risk

**Decision**: **Option 2: 24-hour TTL file-based cache**

**Rationale**:
- Spec FR-S010: "Cache responses for 24 hours, reuse for identical task titles"
- Spec NFR-S-COST-001: "Daily cost <$0.10 for 100 tasks" (caching reduces cost to $0.084)
- Spec NFR-S-REL-003: "Cache hit rate target >30%"
- Research finding: 30% hit rate with 24h TTL is realistic for task management workflows
- File-based cache aligns with local-first architecture (no SQLite dependency)
- Auditable: Can inspect vault/Logs/API_Cache/ to verify caching behavior

**Reversible**: Yes, can add LRU cache in Gold tier if file I/O becomes bottleneck

---

### Decision 4: Input Sanitization Before API Calls (PII Removal)

**Options Considered**:
1. **Send full task content**: No sanitization (simplest, but leaks PII to API)
2. **Regex-based sanitization**: Remove emails, phones, account numbers
3. **LLM-based redaction**: Use Claude to redact PII before analysis (expensive, recursive)

**Trade-offs**:
- **Full content**: Violates spec NFR-S-SEC-003 ("send only title + 200 chars, no PII")
- **Regex sanitization**: Fast, deterministic, but may miss some PII patterns
- **LLM redaction**: Most thorough, but doubles API cost, adds complexity

**Decision**: **Option 2: Regex-based sanitization**

**Rationale**:
- Spec FR-S005: "Sanitize inputs: remove email addresses, phone numbers, account numbers"
- Spec NFR-S-SEC-002: "System MUST sanitize inputs before API calls"
- Spec NFR-S-SEC-003: "Send only task title + first 200 chars (no full email content)"
- Regex patterns cover 95%+ of common PII formats
- Fast execution (<1ms), no API cost
- Testable: Unit tests verify PII removal (test_ai_analyzer.py)

**Implementation Pattern**:
```python
import re

def sanitize_input(text: str) -> str:
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    # Remove phone numbers (US format)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    # Remove account numbers (6+ digits)
    text = re.sub(r'\b\d{6,}\b', '[ACCOUNT]', text)
    return text[:200]  # Truncate to 200 chars
```

**Reversible**: Yes, can add LLM redaction in Platinum tier for regulated industries

---

### Decision 5: Gmail OAuth2 with Token Storage in ~/.config/

**Options Considered**:
1. **Token in ~/.config/**: User-scoped, cross-vault compatible
2. **Token in vault/Logs/**: Vault-scoped, easier for single-vault setups
3. **OS keychain**: macOS Keychain, Windows Credential Manager (most secure)

**Trade-offs**:
- **~/.config/**: Secrets out of vault, cross-vault compatible, easy to exclude from Git
- **vault/Logs/**: Simpler for single vault, but secrets in vault violate security principle
- **OS keychain**: Most secure, but platform-specific, harder to test

**Decision**: **Option 1: ~/.config/personal-ai-employee/gmail_token.json**

**Rationale**:
- Spec NFR-S-SEC-004: "Gmail/WhatsApp credentials in ~/.config/ or OS keychain (not vault)"
- Research finding: Token in ~/.config/ keeps secrets out of vault (see research.md section 3)
- Cross-vault compatibility: One auth works for multiple vaults
- Easier to exclude from Git (.gitignore only needs .env, not vault/.gitignore)
- Spec FR-S020: Handle Gmail API 403 errors (OAuth2 token refresh logic)

**Reversible**: Yes, can migrate to OS keychain in Platinum tier for enterprise deployments

---

### Decision 6: Human-in-the-Loop Approval via File Movement Workflow

**Options Considered**:
1. **File movement**: vault/Pending_Approval/ → vault/Approved/ (user moves file)
2. **CLI approval**: `claude approve <task_id>` command
3. **Dashboard checkbox**: Click checkbox in Dashboard.md (requires Obsidian plugin)

**Trade-offs**:
- **File movement**: Obsidian-native (drag-and-drop), auditable (file history), but manual
- **CLI approval**: Fast for power users, but requires terminal access, not visual
- **Dashboard checkbox**: Best UX, but requires proprietary Obsidian plugin (violates constitution)

**Decision**: **Option 1: File movement workflow**

**Rationale**:
- Spec FR-S040: "Human-in-the-loop approval for all MCP actions (file-based approval workflow)"
- Constitution Principle II: "No dependency on proprietary Obsidian plugins"
- Obsidian-native: Users already familiar with file organization (Inbox/ → Done/)
- Auditable: File move events logged by Obsidian and OS
- Testable: Integration tests can simulate file movement (shutil.move)

**Implementation Pattern**:
```python
# Orchestrator watches vault/Approved/ folder
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ApprovalHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        approval_file = Path(event.src_path)
        if approval_file.parent.name == "Email":
            execute_email_send(approval_file)
        elif approval_file.parent.name == "LinkedIn":
            execute_linkedin_post(approval_file)
        # Move to Done/ after execution
        shutil.move(approval_file, f"vault/Done/{approval_file.name}")
```

**Reversible**: Yes, can add CLI approval in Gold tier as power-user option


## 3. Interfaces and API Contracts

### Agent Skills API (Python Functions)

**Inherited from Bronze** (no changes):
- `read_vault_file(filepath: str) -> str`: Read markdown file content
- `list_vault_folder(folder_name: str) -> list[str]`: List .md filenames in folder
- `get_dashboard_summary() -> dict`: Parse Dashboard.md, return task counts
- `validate_handbook() -> tuple[bool, list[str]]`: Check handbook sections

**New in Silver**:

```python
# agent_skills/ai_analyzer.py
async def analyze_priority(task_title: str, task_content: str) -> dict:
    """Analyze task priority using Claude API.
    
    Args:
        task_title: Task title (max 100 chars)
        task_content: First 200 chars of task content
    
    Returns:
        {
            "priority": "High"|"Medium"|"Low",
            "category": "Work"|"Personal"|"Urgent"|"Uncategorized",
            "reasoning": str,
            "cost": float,  # USD
            "cached": bool,
            "fallback": bool  # True if Bronze defaults used
        }
    
    Raises:
        ValueError: If task_title empty or task_content too long
    """

async def generate_plan(task_title: str, task_content: str) -> str:
    """Generate Plan.md file for multi-step task.
    
    Args:
        task_title: Task title
        task_content: Full task description
    
    Returns:
        Path to generated Plan.md file (vault/Plans/PLAN_{title}_{date}.md)
    
    Raises:
        APIError: If Claude API fails after retries
    """

# agent_skills/api_usage_tracker.py
def log_api_call(request_type: str, input_tokens: int, output_tokens: int, cost: float):
    """Log API usage to vault/Logs/API_Usage/YYYY-MM.md."""

def check_daily_cost() -> tuple[float, bool]:
    """Check current daily cost. Returns (cost, exceeded_limit)."""

def get_cost_report(month: str) -> dict:
    """Generate monthly cost report. Args: month='YYYY-MM'. Returns summary dict."""
```

### External API Contracts

**Claude API (Anthropic SDK)**:
- Endpoint: `https://api.anthropic.com/v1/messages`
- Authentication: `x-api-key: {CLAUDE_API_KEY}` header
- Model: `claude-3-5-sonnet-20241022` (configurable via env)
- Timeout: 5 seconds
- Structured output (JSON):
  ```json
  {
    "priority": "High"|"Medium"|"Low",
    "category": "Work"|"Personal"|"Urgent"|"Uncategorized",
    "reasoning": "Brief explanation (max 100 chars)"
  }
  ```

**Gmail API (Google)**:
- Endpoint: `https://gmail.googleapis.com/gmail/v1/users/me/messages`
- Authentication: OAuth2 with refresh token
- Query: `is:unread is:important`
- Rate limit: 250 quota units/user/second (1 quota unit per list request)
- Error handling: 403 (auth), 429 (rate limit), 500 (server error)

**WhatsApp Web (Playwright)**:
- URL: `https://web.whatsapp.com`
- Session: Persistent Chromium context with cookies/localStorage
- Selectors: `[data-testid="qrcode"]` (session check), `[aria-label*="unread"]` (unread chats)
- Keywords: `["urgent", "invoice", "payment", "help", "asap"]`

**Email MCP Server** (see contracts/mcp-email.md for full contract):
- Tool: `send_email(to: str, subject: str, body: str, attachments: list[str])`
- Approval required: Yes (file-based workflow)
- Logging: All calls logged to vault/Logs/MCP_Actions/YYYY-MM-DD.md

## 4. Non-Functional Requirements (NFRs)

### Performance (NFR-S-PERF)

- **NFR-S-PERF-001**: AI priority analysis completes in <5 seconds (3s API call + 2s processing)
- **NFR-S-PERF-002**: Gmail watcher processes batch of 10 emails in <30 seconds
- **NFR-S-PERF-003**: Dashboard update with AI analysis completes in <5 seconds total
- **NFR-S-PERF-004**: System supports up to 1000 files (Bronze limit maintained)

**Verification**:
- Performance tests with `time.time()` before/after API calls
- Load test: 100 tasks with AI analysis, verify total time <500 seconds (5s/task)

### Reliability (NFR-S-REL)

- **NFR-S-REL-001**: AI analysis failure rate <5%. Fall back to Bronze defaults (no crash)
- **NFR-S-REL-002**: Gmail/WhatsApp watchers recover from API errors in <2 minutes (auto-retry)
- **NFR-S-REL-003**: API response cache hit rate >30% (24h TTL)
- **NFR-S-REL-004**: Rate limiting prevents quota exhaustion (max 10 calls/min, 100/day)

**Verification**:
- Integration test: Disconnect network → Verify Bronze fallback → Reconnect → Verify AI resumes
- Cache test: Process 100 tasks with 30% duplicates → Verify cache hit rate >30%

### Cost Control (NFR-S-COST)

- **NFR-S-COST-001**: Daily API cost <$0.10 for 100 tasks/day (with caching)
- **NFR-S-COST-002**: Batch API requests when possible (reduce prompt overhead)
- **NFR-S-COST-003**: Alert at $0.10 (warning), $0.25 (error), $0.50 (critical)
- **NFR-S-COST-004**: Monthly cost report queryable via `python agent_skills/api_usage.py --report monthly`

**Verification**:
- Cost test: Process 100 tasks → Verify total cost <$0.10
- Alert test: Inject fake high-cost entries → Verify alerts logged

### Security (NFR-S-SEC)

- **NFR-S-SEC-001**: API key in .env file (never in code), .env in .gitignore
- **NFR-S-SEC-002**: Input sanitization: Remove emails, phones, account numbers (regex-based)
- **NFR-S-SEC-003**: Send only task title + first 200 chars to API (no full content)
- **NFR-S-SEC-004**: Gmail/WhatsApp credentials in ~/.config/ or OS keychain (not vault/)
- **NFR-S-SEC-005**: Human approval required for all MCP actions (no autonomous execution)

**Verification**:
- Security audit: `git log --all -- .env` → Verify no .env commits
- Sanitization test: Input with PII → Verify PII removed before API call

### Usability (NFR-S-USE)

- **NFR-S-USE-001**: Upgrade Bronze→Silver: Set `ENABLE_AI_ANALYSIS=true`, add `CLAUDE_API_KEY`, restart watcher. No code changes.
- **NFR-S-USE-002**: Error messages actionable: "Claude API key invalid. Check .env. Get key at: https://console.anthropic.com/"
- **NFR-S-USE-003**: Dashboard indicates Silver status: "Silver Tier Active (AI Analysis: ✓, Cost Today: $0.05)"
- **NFR-S-USE-004**: Cost alerts include recommendations: "Cost $0.12 (over $0.10). Reduce frequency or disable AI."

**Verification**:
- Usability test: Fresh install → Follow quickstart.md → Verify upgrade path works
- Error message test: Invalid API key → Verify actionable error message logged

## 5. Operational Readiness

### Deployment

**Initial Setup** (see quickstart.md for details):
1. Install dependencies: `pip install -r requirements.txt && playwright install chromium`
2. Configure .env: Set `ENABLE_AI_ANALYSIS=true`, add `CLAUDE_API_KEY`
3. Setup Gmail OAuth2: Run `python setup_gmail_auth.py` (browser opens, authorize, token saved)
4. Setup WhatsApp session: Run `python setup_whatsapp_session.py` (QR code scan, session saved)
5. Start watchers: `pm2 start ecosystem.config.js` (Bronze + Gmail + WhatsApp + LinkedIn)

**Upgrade from Bronze**:
1. Backup vault: `cp -r vault vault.bak.$(date +%Y%m%d)`
2. Update .env: Add Silver config (ENABLE_AI_ANALYSIS, CLAUDE_API_KEY, etc.)
3. Install new dependencies: `pip install -r requirements.txt`
4. Setup Gmail/WhatsApp auth (first time only)
5. Restart watchers: `pm2 restart all`
6. Verify: Check Dashboard.md for "Silver Tier Active" status

### Monitoring & Observability

**Logs** (all in vault/Logs/):
- `watcher-YYYY-MM-DD.md`: Bronze file watcher events (inherited)
- `gmail_watcher_errors.md`: Gmail API errors (403, 429, 500)
- `whatsapp_watcher_errors.md`: WhatsApp session expiry, keyword match failures
- `API_Usage/YYYY-MM.md`: API cost tracking (daily cumulative)
- `MCP_Actions/YYYY-MM-DD.md`: All MCP actions (email send, LinkedIn post)
- `cost_alerts.md`: Daily cost threshold alerts ($0.10, $0.25, $0.50)

**Metrics**:
- API cost: `tail -100 vault/Logs/API_Usage/$(date +%Y-%m).md | grep "total_cost"`
- Cache hit rate: `grep "cache_hit" vault/Logs/API_Usage/*.md | wc -l` / total calls
- Watcher uptime: `pm2 status` → Check restart count (target: <5 restarts/day)

**Alerts**:
- Daily cost >$0.10: Entry in vault/Logs/cost_alerts.md
- WhatsApp session expired: File created in vault/Needs_Action/WHATSAPP_SESSION_EXPIRED.md
- Gmail auth failed: Entry in vault/Logs/gmail_watcher_errors.md with "403 Forbidden"

### Runbooks

**Runbook 1: Claude API Key Invalid**
1. Symptom: All tasks show Priority="Medium", logs show "API key invalid"
2. Diagnosis: Check .env file has `CLAUDE_API_KEY=sk-ant-...`
3. Fix: Get new key from https://console.anthropic.com/, update .env
4. Restart: `pm2 restart all`
5. Verify: Drop test file in Inbox/, check Dashboard.md for Priority="High"/"Low"

**Runbook 2: WhatsApp Session Expired**
1. Symptom: File created in vault/Needs_Action/WHATSAPP_SESSION_EXPIRED.md
2. Diagnosis: WhatsApp Web logged out (session expired after 14 days inactivity)
3. Fix: Run `python setup_whatsapp_session.py` → Scan QR code
4. Restart: `pm2 restart whatsapp-watcher`
5. Verify: Send test WhatsApp message with "urgent" → Check vault/Inbox/ for WHATSAPP_* file

**Runbook 3: Daily Cost Exceeds $0.10**
1. Symptom: Entry in vault/Logs/cost_alerts.md
2. Diagnosis: More than 100 tasks analyzed, or cache hit rate <30%
3. Fix Option A: Reduce analysis frequency (edit Company_Handbook.md polling interval)
4. Fix Option B: Disable AI analysis temporarily (`ENABLE_AI_ANALYSIS=false` in .env)
5. Fix Option C: Clear duplicate tasks (reduce inbox size)
6. Verify: Next day, check `tail vault/Logs/API_Usage/$(date +%Y-%m).md` for total cost

**Runbook 4: Gmail Watcher Not Detecting Emails**
1. Symptom: Important emails arriving, but no EMAIL_* files in vault/Inbox/
2. Diagnosis: Check `tail -50 vault/Logs/gmail_watcher_errors.md` for API errors
3. Fix Option A: 403 Forbidden → OAuth2 token expired, run `python setup_gmail_auth.py`
4. Fix Option B: 429 Rate Limit → Wait 60 seconds, watcher auto-resumes
5. Fix Option C: No "is:important" label → Gmail filter not set, create filter in Gmail UI
6. Verify: Send test email, mark as important, wait 2 minutes, check vault/Inbox/

### Rollback Strategy

**Rollback to Bronze** (if Silver causes issues):
1. Stop watchers: `pm2 stop gmail-watcher whatsapp-watcher linkedin-generator`
2. Disable AI analysis: Set `ENABLE_AI_ANALYSIS=false` in .env
3. Restart Bronze watcher: `pm2 restart bronze-watcher`
4. Verify: Drop test file → Check Dashboard.md shows Priority="Medium" (Bronze default)
5. Restore vault from backup if corruption: `cp -r vault.bak.YYYYMMDD vault`

**Data Preservation**:
- All Silver-generated files (EMAIL_*, WHATSAPP_*, Plan.md) remain in vault
- Dashboard.md retains Silver columns (Priority, Category) but shows "Medium"/"Uncategorized"
- Bronze watcher continues monitoring vault/Inbox/ as before

---

**Plan Status**: Complete. Ready for Phase 2 (`/sp.tasks`) to generate implementation tasks.

**Next Steps**:
1. Review plan.md for technical accuracy and alignment with spec
2. Create contracts/claude-api.md, contracts/gmail-api.md, contracts/mcp-email.md (Phase 1)
3. Create data-model.md for entities (AIAnalysisResult, EmailTask, etc.) (Phase 1)
4. Create quickstart.md with setup instructions (Phase 1)
5. Run `/sp.tasks 001-silver-tier` to generate actionable implementation tasks (Phase 2)
