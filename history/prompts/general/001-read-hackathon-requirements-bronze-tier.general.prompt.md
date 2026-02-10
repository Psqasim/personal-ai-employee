---
id: 001
title: Read Hackathon Requirements Bronze Tier
stage: general
date: 2026-02-10
surface: agent
model: claude-sonnet-4-5
feature: none
branch: main
user: ps_qasim
command: general
labels: ["hackathon-requirements", "bronze-tier", "preparation", "document-review"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md (read)
tests:
  - (None - document review only)
---

## Prompt

The Hackathon 0 requirements document is at:
/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md

Please read this file to understand the full Bronze tier requirements before we create the specification. ,also this prompt make save in history\prompts/genral/ etc ok ,means we if simple talk then save in genral

## Response snapshot

Successfully read the comprehensive Hackathon 0 requirements document (1,200+ lines). Key Bronze tier requirements identified:

**Bronze Tier: Foundation (Minimum Viable Deliverable)**
- Estimated time: 8-12 hours
- **Required deliverables:**
  1. Obsidian vault with Dashboard.md and Company_Handbook.md
  2. One working Watcher script (Gmail OR file system monitoring)
  3. Claude Code successfully reading from and writing to the vault
  4. Basic folder structure: /Inbox, /Needs_Action, /Done
  5. All AI functionality implemented as Agent Skills

**Bronze Tier Core Components:**

1. **Perception Layer (Watchers)**:
   - File system watcher (simplest option for Bronze)
   - BaseWatcher abstract class pattern provided
   - Polling-based monitoring (30-second interval per constitution)

2. **Obsidian Vault Structure**:
   - Dashboard.md: Real-time task summary with markdown table [File, Added, Status, Priority]
   - Company_Handbook.md: Agent operational rules (required sections validation)
   - Folder structure: /Needs_Action, /Plans, /Done, /Logs, /Pending_Approval, /Approved, /Rejected

3. **Claude Code Integration**:
   - File System MCP for vault read/write operations
   - Agent Skills for all functionality (not inline scripts)
   - Read → Think → Plan → Write workflow

4. **Architecture Pattern**:
   - Perception (Watcher) → Reasoning (Claude Code) → Action (MCP)
   - Local-first (100% offline for Bronze)
   - Human-in-the-loop for all actions (Bronze tier = monitor only)

**Key Technical Details from Document:**

- **Watcher Implementation**: BaseWatcher abstract class with `check_for_updates()` and `create_action_file()` methods
- **Action File Format**: Markdown with YAML frontmatter (type, status, priority)
- **Dashboard Format**: Markdown table with Obsidian wiki link syntax `[[filename]]`
- **Vault Integrity**: Atomic file operations, backup Dashboard.md before updates
- **Performance**: File watcher 30-second polling, dashboard update <2 seconds

**PHR Routing Clarification (User Request):**
- Constitution work → `history/prompts/constitution/`
- Feature-specific work → `history/prompts/<feature-name>/`
- **General conversations → `history/prompts/general/`** (this conversation)

User confirmed that simple conversations and preparation steps should be saved in `history/prompts/general/` rather than constitution or feature-specific directories.

Ready to create Bronze tier specification with full requirements context.

## Outcome

- ✅ Impact: Comprehensive understanding of Hackathon 0 requirements document, Bronze tier deliverables, and technical architecture patterns for Personal AI Employee system
- 🧪 Tests: No tests required (document review and PHR routing clarification)
- 📁 Files: Read Hackathon requirements document (1,200+ lines), created PHR in `history/prompts/general/` per user request
- 🔁 Next prompts:
  - `/sp.specify bronze-tier` - Create Bronze tier specification with full requirements
  - Review vault folder structure and create initial directories
  - Implement file system watcher as first agent skill
- 🧠 Reflection: The Hackathon document provides excellent architectural guidance with code examples for watchers, MCP integration, and HITL patterns. Bronze tier focuses on foundation (monitoring only) with 100% offline operation, which aligns perfectly with constitution's local-first and incremental development principles.

## Evaluation notes (flywheel)

- Failure modes observed: None (document review successful)
- Graders run and results (PASS/FAIL): N/A (preparation phase)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Create Bronze tier spec following constitution principles and Hackathon requirements, starting with file system watcher as simplest perception component
