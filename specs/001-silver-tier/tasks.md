# Tasks: Silver Tier - Functional AI Assistant

**Input**: Design documents from `/specs/001-silver-tier/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/ (complete)

**Tests**: Unit tests included for new modules (target: 80% coverage). Integration tests for end-to-end workflows.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure (single project):
- **Core modules**: `agent_skills/` (reusable Python modules)
- **Watchers**: `watchers/` (async entry points)
- **Scripts**: `scripts/` (CLI entry points)
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- **Vault**: `vault/` (Obsidian vault structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [X] T001 Install Python dependencies from requirements.txt (anthropic>=0.18.0, google-auth>=2.16.0, google-api-python-client>=2.80.0, playwright>=1.40.0, aiohttp>=3.9.0)
- [X] T002 Install Playwright browsers with `playwright install chromium` for WhatsApp watcher
- [X] T003 [P] Install PM2 process manager with `npm install -g pm2` for watcher orchestration
- [X] T004 [P] Create .env.example file in project root with Silver tier configuration template (ENABLE_AI_ANALYSIS, CLAUDE_API_KEY, CLAUDE_MODEL, GMAIL_CREDENTIALS_PATH, GMAIL_POLL_INTERVAL, WHATSAPP_SESSION_PATH, WHATSAPP_KEYWORDS, LINKEDIN_POSTING_FREQUENCY, API_DAILY_COST_LIMIT, API_RATE_LIMIT_PER_MIN, API_CACHE_DURATION)
- [X] T005 Create ~/.config/personal-ai-employee/ directory for credentials storage
- [X] T006 [P] Update .gitignore to exclude .env, ~/.config/personal-ai-employee/, vault/Logs/API_Cache/, vault/Logs/gmail_processed_ids.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Verify Bronze tier compatibility: Run Bronze tests (pytest tests/ -k bronze) and confirm all pass
- [X] T008 Create vault/Logs/API_Usage/ directory for API cost tracking
- [X] T009 [P] Create vault/Logs/API_Cache/ directory for 24h response caching
- [X] T010 [P] Create vault/Pending_Approval/ subdirectories (Email/, LinkedIn/, MCP/)
- [X] T011 [P] Create vault/Approved/ subdirectories (Email/, LinkedIn/, MCP/)
- [X] T012 [P] Create vault/Plans/ directory for Plan.md files
- [X] T013 Create agent_skills/__init__.py to initialize package
- [X] T014 [P] Create watchers/__init__.py to initialize watchers package
- [X] T015 [P] Create tests/fixtures/mock_claude_responses.json with sample API responses for unit tests
- [X] T016 [P] Create tests/fixtures/mock_gmail_data.json with sample Gmail API responses for unit tests

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - AI-Powered Priority Analysis (P1) 🎯 MVP

**Goal**: Analyze inbox tasks using Claude API to assign intelligent priorities (High/Medium/Low) with graceful fallback to Bronze defaults when API unavailable

**Independent Test**: Add 3 test files to vault/Inbox/ with different urgency levels ("urgent client request", "routine task", "low-priority note"). With ENABLE_AI_ANALYSIS=true, verify Dashboard.md shows High/Medium/Low priorities within 10 seconds.

### Implementation for User Story 1

- [X] T017 [P] [US1] Create agent_skills/ai_analyzer.py module with async functions: analyze_priority(), _call_claude_api(), _sanitize_input(), _cache_response()
- [X] T018 [US1] Implement analyze_priority() function: Accept task_title and task_snippet (max 200 chars), check ENABLE_AI_ANALYSIS flag, call Claude API with 5-second timeout, return priority dict with fallback to Bronze defaults on error
- [X] T019 [US1] Implement _call_claude_api() function: Use AsyncAnthropic client from anthropic SDK, create messages API call with model=claude-3-5-sonnet-20241022, max_tokens=100, system prompt for structured JSON output, handle asyncio.TimeoutError and APIError exceptions
- [X] T020 [US1] Implement _sanitize_input() function: Remove email addresses (regex pattern), remove phone numbers (US format), remove account numbers (6+ digits), truncate to 200 chars, return sanitized text
- [X] T021 [US1] Implement _cache_response() function: Hash task_title with SHA256, check vault/Logs/API_Cache/{hash}.json exists and timestamp < 24h, return cached response if valid, save new responses with timestamp
- [X] T022 [US1] Add graceful fallback logic: If API call fails (timeout, auth error, rate limit), return {"priority": "Medium", "category": "Uncategorized", "fallback": True, "cost": 0.0}
- [X] T023 [US1] Update scripts/watch_inbox.py: Import analyze_priority from agent_skills.ai_analyzer, call analyze_priority() for each new file in vault/Inbox/, update Dashboard.md with priority from API response or fallback
- [X] T024 [US1] Create tests/unit/test_ai_analyzer.py: Test analyze_priority() with mock API responses, test _sanitize_input() with PII data (emails, phones, accounts), test _cache_response() with 24h TTL validation, test graceful fallback when API unavailable, target 80% coverage

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Priority analysis works with fallback to Bronze defaults.

---

## Phase 4: User Story 2 - Task Categorization (P1)

**Goal**: Categorize tasks as Work/Personal/Urgent based on content analysis using Claude API

**Independent Test**: Add files with work-related content ("client proposal", "meeting notes") and personal content ("grocery list", "vacation planning"). Verify Dashboard.md includes "Category" column with correct classifications.

### Implementation for User Story 2

- [X] T025 [US2] Add categorize_task() function to agent_skills/ai_analyzer.py: Extend Claude API prompt to include category in JSON response, parse category field from API, return {"priority": "X", "category": "Work"|"Personal"|"Urgent"|"Uncategorized"}
- [X] T026 [US2] Update Dashboard.md schema in agent_skills/dashboard_updater.py: Add "Category" column after "Priority" column, update table header to include "| Category |", update task rows to include category from analysis result
- [X] T027 [US2] Update scripts/watch_inbox.py: Call analyze_priority() which now returns both priority and category, pass category to dashboard updater, fallback to "Uncategorized" when API unavailable
- [X] T028 [US2] Add Dashboard Statistics section: Update dashboard_updater.py to include "Work Tasks: X", "Personal Tasks: Y", "Urgent Tasks: Z" counts in Statistics section
- [X] T029 [US2] Update tests/unit/test_ai_analyzer.py: Add test cases for categorization (Work keywords: "client", "invoice", "proposal"; Personal keywords: "family", "vacation", "health"; Urgent keywords: "URGENT", "ASAP", "emergency"), verify category fallback to "Uncategorized" on API failure

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Tasks have both priority and category.

---

## Phase 5: User Story 3 - Gmail Watcher Integration (P1)

**Goal**: Monitor Gmail for important emails and create task files in vault/Inbox/ with email metadata

**Independent Test**: Send a test email to your Gmail account with "is:important" label. Verify the Gmail watcher creates a file vault/Inbox/EMAIL_{id}.md within 2 minutes with email subject, sender, and snippet.

### Implementation for User Story 3

- [X] T030 [US3] Create scripts/setup_gmail_auth.py: Implement OAuth2 flow with google_auth_oauthlib, use scopes (gmail.readonly, gmail.labels), run local server for authorization, save token to ~/.config/personal-ai-employee/gmail_token.json
- [X] T031 [US3] Create watchers/gmail_watcher.py main() function: Load credentials from ~/.config/, create Gmail API service with google-api-python-client, implement async polling loop (120-second interval from GMAIL_POLL_INTERVAL env var), add signal handling for graceful shutdown
- [X] T032 [US3] Implement poll_gmail() async function in watchers/gmail_watcher.py: Query Gmail API with "is:unread is:important", maxResults=10, fetch message metadata (from, subject, snippet, internalDate), return list of message dicts
- [X] T033 [US3] Implement create_email_task() function in watchers/gmail_watcher.py: Create vault/Inbox/EMAIL_{message_id}.md, write YAML frontmatter (type: email, from: sender, subject: subject, received: timestamp, priority: high, status: pending), include email snippet (first 200 chars), add suggested actions checklist
- [X] T034 [US3] Implement track_processed_ids() function in watchers/gmail_watcher.py: Read vault/Logs/gmail_processed_ids.txt, check if message_id already processed, append new message_id to file (prevent duplicates)
- [X] T035 [US3] Add Gmail API error handling in watchers/gmail_watcher.py: Catch 403 Forbidden (OAuth expired, log error, pause watcher), catch 429 Rate Limit (exponential backoff 60s/120s/240s), catch 500 Server Error (log and retry on next poll), log all errors to vault/Logs/gmail_watcher_errors.md
- [X] T036 [US3] Create tests/integration/test_gmail_watcher.py: Mock Gmail API responses, verify EMAIL_{id}.md file creation, verify duplicate prevention (same message_id), verify error handling (403, 429, 500)

**Checkpoint**: At this point, Gmail watcher creates email tasks independently. All P1 communication monitoring is functional.

---

## Phase 6: User Story 6 - Plan.md Generation Workflow (P1)

**Goal**: Generate Plan.md files for multi-step tasks with numbered checklist and approval workflow

**Independent Test**: Add a file to vault/Inbox/ containing "Plan Q1 marketing campaign". With AI analysis enabled, verify a Plan.md file is created in vault/Plans/ with multi-step breakdown.

### Implementation for User Story 6

- [ ] T037 [P] [US6] Create agent_skills/plan_generator.py module with functions: create_plan_md(), _detect_multi_step_task(), _generate_plan_steps()
- [ ] T038 [US6] Implement _detect_multi_step_task() function: Check for keywords ("plan", "campaign", "project", "implement") in task_title or task_content, return boolean indicating if plan generation needed
- [ ] T039 [US6] Implement _generate_plan_steps() async function: Call Claude API with multi-shot prompting to generate step breakdown, parse response into list of PlanStep dicts (step_number, description, dependencies, approval_required), return plan structure
- [ ] T040 [US6] Implement create_plan_md() function: Generate filename PLAN_{task_name}_{date}.md, create YAML frontmatter (objective, steps count, approval_required, estimated_time, created timestamp, status: pending), write numbered checklist with `[ ]` checkboxes, add dependency markers "[Blocked by: Step X]" where needed, save to vault/Plans/
- [ ] T041 [US6] Update scripts/watch_inbox.py: After analyze_priority(), call _detect_multi_step_task(), if True call create_plan_md() and log Plan.md creation to vault/Logs/watcher-YYYY-MM-DD.md
- [ ] T042 [US6] Create tests/unit/test_plan_generator.py: Test _detect_multi_step_task() with multi-step keywords, test _generate_plan_steps() with mock Claude API response, test create_plan_md() file creation and YAML format, verify dependency parsing

**Checkpoint**: At this point, Plan.md generation works for complex tasks. All P1 user stories are complete (US1, US2, US3, US6).

---

## Phase 7: User Story 7 - Cost-Aware API Usage (P2)

**Goal**: Track Claude API usage and alert if daily costs exceed $0.10

**Independent Test**: Process 50 tasks with AI analysis enabled. Check vault/Logs/API_Usage/YYYY-MM.md for cumulative cost tracking.

### Implementation for User Story 7

- [ ] T043 [P] [US7] Create agent_skills/api_usage_tracker.py module with functions: log_api_call(), check_daily_cost(), get_cost_report()
- [ ] T044 [US7] Implement log_api_call() function: Accept request_type, input_tokens, output_tokens, cost (USD), append entry to vault/Logs/API_Usage/YYYY-MM.md with timestamp, calculate daily cumulative cost
- [ ] T045 [US7] Implement check_daily_cost() function: Read vault/Logs/API_Usage/YYYY-MM.md for current date, sum all costs, compare to API_DAILY_COST_LIMIT env var ($0.10), return (current_cost, exceeded_limit boolean)
- [ ] T046 [US7] Add cost alerting logic in agent_skills/api_usage_tracker.py: If daily cost exceeds $0.10, create entry in vault/Logs/cost_alerts.md with warning, at $0.25 log error alert, at $0.50 log critical alert
- [ ] T047 [US7] Implement get_cost_report() function: Accept month (YYYY-MM), parse vault/Logs/API_Usage/YYYY-MM.md, return summary dict (total_cost, total_requests, cost_by_day, average_cost_per_request)
- [ ] T048 [US7] Update agent_skills/ai_analyzer.py: After each Claude API call, call log_api_call() with usage.input_tokens, usage.output_tokens, estimated cost, call check_daily_cost() and log alert if needed
- [ ] T049 [US7] Create tests/unit/test_api_usage_tracker.py: Test log_api_call() file writing, test check_daily_cost() threshold detection, test get_cost_report() monthly aggregation, verify alert creation at $0.10/$0.25/$0.50 thresholds

**Checkpoint**: Cost tracking active. Daily API costs monitored and alerts logged.

---

## Phase 8: User Story 4 - WhatsApp Watcher Integration (P2)

**Goal**: Monitor WhatsApp Web for urgent keywords and create task files

**Independent Test**: Send a test WhatsApp message containing "urgent invoice request". Verify the watcher creates a file in vault/Inbox/ within 30 seconds.

### Implementation for User Story 4

- [ ] T050 [US4] Create scripts/setup_whatsapp_session.py: Use Playwright sync API to launch Chromium in headed mode, navigate to https://web.whatsapp.com, wait for user to scan QR code, wait 30 seconds for chats to load, save persistent context to WHATSAPP_SESSION_PATH, close browser
- [ ] T051 [US4] Create watchers/whatsapp_watcher.py main() function: Use Playwright async API to launch_persistent_context from WHATSAPP_SESSION_PATH in headless mode, implement async polling loop (30-second interval from env var), add signal handling for graceful shutdown
- [ ] T052 [US4] Implement check_session() function in watchers/whatsapp_watcher.py: Check for QR code element `[data-testid="qrcode"]`, if present log "WhatsApp session expired", create notification file vault/Needs_Action/WHATSAPP_SESSION_EXPIRED.md, pause polling, return session_valid boolean
- [ ] T053 [US4] Implement find_keyword_messages() async function in watchers/whatsapp_watcher.py: Query unread chats with `[aria-label*="unread"]`, extract text from each chat, match against WHATSAPP_KEYWORDS env var (["urgent", "invoice", "payment", "help", "asap"]), return list of matching chats with contact_name and matched_keywords
- [ ] T054 [US4] Implement create_whatsapp_task() function in watchers/whatsapp_watcher.py: Create vault/Inbox/WHATSAPP_{chat_id}_{timestamp}.md, write YAML frontmatter (type: whatsapp, from: contact_name, received: timestamp, keywords: matched_keywords, priority: high, status: pending), include message preview (first 200 chars)
- [ ] T055 [US4] Add error logging in watchers/whatsapp_watcher.py: Log all Playwright errors to vault/Logs/whatsapp_watcher_errors.md, log session expiry events, log keyword match events
- [ ] T056 [US4] Create tests/integration/test_whatsapp_watcher.py: Mock Playwright page with fake QR code element, verify session expiry detection, mock unread chats with keywords, verify WHATSAPP_{id}.md file creation

**Checkpoint**: WhatsApp watcher monitors messages for urgent keywords. P2 communication monitoring complete.

---

## Phase 9: User Story 5 - LinkedIn Auto-Posting (P2)

**Goal**: Draft LinkedIn posts based on business goals and save to approval workflow

**Independent Test**: Configure business goals in vault/Company_Handbook.md. Trigger LinkedIn post generation. Verify a draft post file appears in vault/Pending_Approval/LinkedIn/.

### Implementation for User Story 5

- [ ] T057 [P] [US5] Create watchers/linkedin_generator.py module with main() function: Implement scheduled execution (daily/weekly based on LINKEDIN_POSTING_FREQUENCY env var), use cron scheduling via PM2 ecosystem.config.js
- [ ] T058 [US5] Implement read_business_goals() function in watchers/linkedin_generator.py: Parse vault/Company_Handbook.md, extract section specified by LINKEDIN_BUSINESS_GOALS_SECTION env var ("Business Goals"), return list of business goals as strings
- [ ] T059 [US5] Implement draft_post() async function in watchers/linkedin_generator.py: Call Claude API with system prompt including business goals, tone (professional), target audience, max 3000 chars (LinkedIn limit), parse response for post_content, return LinkedInPost dict
- [ ] T060 [US5] Implement save_draft() function in watchers/linkedin_generator.py: Create vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{YYYY-MM-DD}.md, write YAML frontmatter (type: linkedin_post, scheduled_date, status: pending_approval, character_count, business_goal), write post_content in markdown body
- [ ] T061 [US5] Add LinkedIn generator to PM2 config: Update ecosystem.config.js with linkedin-generator process, set cron_restart to "0 9 * * *" for daily at 9 AM (or per env var frequency)
- [ ] T062 [US5] Create tests/unit/test_linkedin_generator.py: Test read_business_goals() parsing Company_Handbook.md, test draft_post() with mock Claude API response, test save_draft() file creation and character count validation (max 3000), verify YAML frontmatter format

**Checkpoint**: LinkedIn post drafts generated on schedule. All P2 user stories complete (US4, US5, US7).

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T063 [P] Update agent_skills/dashboard_updater.py: Add "Silver Tier Status" section to Dashboard.md showing AI Analysis (Enabled/Disabled), API Cost Today (from api_usage_tracker.get_cost_report()), Watchers Active (Gmail: ✓/✗, WhatsApp: ✓/✗, LinkedIn: ⏸ Paused)
- [ ] T064 Update Dashboard.md task sorting: Modify dashboard_updater.py to sort tasks by priority order (Urgent → High → Medium → Low), then by date_added
- [ ] T065 [P] Create ~/.config/claude-code/mcp.json: Configure email MCP server with name "email", command "npx", args ["-y", "@modelcontextprotocol/server-email"], env vars GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH pointing to ~/.config/personal-ai-employee/
- [ ] T066 Create ecosystem.config.js in project root: Define 4 PM2 apps (bronze-watcher: scripts/watch_inbox.py, gmail-watcher: watchers/gmail_watcher.py, whatsapp-watcher: watchers/whatsapp_watcher.py, linkedin-generator: watchers/linkedin_generator.py with cron_restart), set env ENABLE_AI_ANALYSIS=true for Silver watchers, configure autorestart=true and max_restarts=10
- [ ] T067 [P] Create scripts/test_silver_integration.py: End-to-end integration test that drops test file in vault/Inbox/, waits for AI analysis, verifies Dashboard.md updated with priority/category, verifies Plan.md created if multi-step keywords present
- [ ] T068 [P] Update tests/integration/test_end_to_end.py: Add Silver tier test case - set ENABLE_AI_ANALYSIS=true, mock Claude API responses, verify AI analysis happens, verify graceful fallback when API unavailable (network disconnect test)
- [ ] T069 [P] Create docs/quickstart-silver.md: Copy from specs/001-silver-tier/quickstart.md, add troubleshooting section with runbooks for common issues (API key invalid, WhatsApp session expired, daily cost exceeds $0.10, Gmail watcher not detecting emails)
- [ ] T070 Update README.md: Add Silver Tier section with feature overview, upgrade instructions from Bronze (set ENABLE_AI_ANALYSIS=true, add CLAUDE_API_KEY, restart watchers), link to quickstart-silver.md
- [ ] T071 Run pytest with coverage: Execute `pytest tests/ --cov=agent_skills --cov=watchers --cov-report=term-missing`, verify coverage ≥80% for new Silver modules (ai_analyzer, api_usage_tracker, plan_generator, gmail_watcher, whatsapp_watcher, linkedin_generator)
- [ ] T072 Create scripts/rollback_to_bronze.sh: Bash script to stop Silver watchers (pm2 stop gmail-watcher whatsapp-watcher linkedin-generator), set ENABLE_AI_ANALYSIS=false in .env, restart bronze-watcher (pm2 restart bronze-watcher), verify Dashboard.md shows Bronze behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational (Phase 2) completion
  - **P1 stories** (US1, US2, US3, US6) can proceed in parallel after Phase 2
  - **P2 stories** (US4, US5, US7) can proceed in parallel after Phase 2
  - Or execute sequentially: US1 → US2 → US3 → US6 → US7 → US4 → US5
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (AI Priority Analysis)**: Foundational complete - No dependencies on other stories
- **US2 (Task Categorization)**: Foundational complete + US1 (extends analyze_priority function)
- **US3 (Gmail Watcher)**: Foundational complete - No dependencies on other stories
- **US4 (WhatsApp Watcher)**: Foundational complete - No dependencies on other stories
- **US5 (LinkedIn Generator)**: Foundational complete - No dependencies on other stories
- **US6 (Plan.md Generation)**: Foundational complete + US1 (uses AI analysis for detection)
- **US7 (Cost Control)**: Foundational complete + US1 (tracks API calls from ai_analyzer)

### Within Each User Story

- **US1**: T017 (module creation) → T018-T022 (functions) → T023 (integration) → T024 (tests)
- **US2**: T025 (categorization) → T026-T027 (dashboard integration) → T028 (statistics) → T029 (tests)
- **US3**: T030 (OAuth setup) → T031-T032 (polling) → T033-T034 (task creation) → T035 (error handling) → T036 (tests)
- **US4**: T050 (session setup) → T051-T052 (watcher main) → T053-T054 (keyword detection) → T055 (logging) → T056 (tests)
- **US5**: T057 (module creation) → T058-T059 (business goals + draft) → T060 (save draft) → T061 (PM2 config) → T062 (tests)
- **US6**: T037 (module creation) → T038-T039 (detection + generation) → T040 (file creation) → T041 (integration) → T042 (tests)
- **US7**: T043 (module creation) → T044-T046 (logging + alerts) → T047 (reporting) → T048 (integration) → T049 (tests)

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004, T006 can run in parallel

**Phase 2 (Foundational)**: T009, T010, T011, T012, T014, T015, T016 can run in parallel

**After Phase 2 completion**, these user stories can start in parallel:
- **Team Member A**: US1 (T017-T024)
- **Team Member B**: US3 (T030-T036)
- **Team Member C**: US4 (T050-T056)
- **Team Member D**: US5 (T057-T062)

**Within US1**: T017 (module creation) must complete first, then T018, T019, T020, T021, T022 can run in parallel (different functions), then T023, then T024

**Within US6**: T037 must complete first, then T038, T039 can run in parallel

**Within US7**: T043 must complete first, then T044, T045, T046, T047 can run in parallel (different functions)

**Phase 10 (Polish)**: T063, T065, T067, T068, T069, T071 can run in parallel

---

## Parallel Example: User Story 1

```bash
# After T017 (module creation) completes, launch these functions in parallel:
Task T018: "Implement analyze_priority() function"
Task T019: "Implement _call_claude_api() function"
Task T020: "Implement _sanitize_input() function"
Task T021: "Implement _cache_response() function"
Task T022: "Add graceful fallback logic"

# Then integrate:
Task T023: "Update scripts/watch_inbox.py with AI analysis"

# Then test:
Task T024: "Create tests/unit/test_ai_analyzer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + US2 + US3 Only)

This MVP delivers core Silver value: AI-powered priority/categorization + Gmail monitoring

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T016) - CRITICAL
3. Complete Phase 3: US1 - AI Priority Analysis (T017-T024)
4. Complete Phase 4: US2 - Task Categorization (T025-T029)
5. Complete Phase 5: US3 - Gmail Watcher (T030-T036)
6. **STOP and VALIDATE**: Drop test email → Verify EMAIL_{id}.md created → Verify Dashboard.md shows AI priority/category
7. Deploy/demo MVP

**MVP Success Criteria**:
- ✅ AI analysis assigns High/Medium/Low priority
- ✅ Tasks categorized as Work/Personal/Urgent
- ✅ Gmail watcher creates email tasks
- ✅ Graceful fallback to Bronze when API unavailable
- ✅ Daily cost <$0.10 with caching

### Incremental Delivery (Add P1 Stories, Then P2)

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (AI Priority) → Test independently → Deploy/Demo (MVP!)
3. Add US2 (Categorization) → Test independently → Deploy/Demo
4. Add US3 (Gmail) → Test independently → Deploy/Demo
5. Add US6 (Plan Generation) → Test independently → Deploy/Demo
6. **P1 stories complete - all critical features delivered**
7. Add US7 (Cost Control) → Test independently → Deploy/Demo
8. Add US4 (WhatsApp) → Test independently → Deploy/Demo
9. Add US5 (LinkedIn) → Test independently → Deploy/Demo
10. **All P2 stories complete - full Silver tier delivered**
11. Add Phase 10 (Polish) → Final integration tests → Production ready

### Parallel Team Strategy

With 4 developers:

1. Team completes Setup + Foundational together (T001-T016)
2. Once Foundational is done:
   - **Developer A**: US1 + US2 (AI analysis core) - T017-T029
   - **Developer B**: US3 (Gmail watcher) - T030-T036
   - **Developer C**: US6 (Plan generation) - T037-T042
   - **Developer D**: US7 (Cost control) - T043-T049
3. After P1 stories complete, add P2:
   - **Developer A**: US4 (WhatsApp) - T050-T056
   - **Developer B**: US5 (LinkedIn) - T057-T062
4. Everyone on Phase 10 (Polish) - T063-T072
5. Stories integrate independently, test together

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **[Story] label** maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Bronze compatibility**: Always verify Bronze tests pass after each phase
- **Cost control**: Monitor API costs during development (target <$0.10/day with caching)
- **Security**: Never commit .env or ~/.config/personal-ai-employee/ to Git
- **Testing**: Run `pytest tests/ --cov` after each user story to verify coverage ≥80%
- **Graceful degradation**: Test network disconnect scenarios to verify fallback to Bronze
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Use PM2 for process management: `pm2 start ecosystem.config.js`, `pm2 status`, `pm2 logs`
- Rollback path available: scripts/rollback_to_bronze.sh if Silver causes issues
