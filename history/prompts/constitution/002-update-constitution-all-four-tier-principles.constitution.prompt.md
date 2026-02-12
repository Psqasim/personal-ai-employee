---
id: 002
title: Update constitution with all four tier principles
stage: constitution
date: 2026-02-11
surface: agent
model: claude-sonnet-4-5
feature: none
branch: silver-tier
user: ps_qasim
command: /sp.constitution
labels: ["constitution", "tiers", "silver", "gold", "platinum", "hackathon", "backward-compatibility"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - none (constitution documentation update)
---

## Prompt

Read the hackathon requirements document at:
Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md

Then update .specify/memory/constitution.md to include principles for ALL FOUR TIERS (Bronze, Silver, Gold, Platinum) in one constitution.

Extend the existing Bronze principles (don't replace) and add:

SILVER TIER PRINCIPLES
- AI-powered priority analysis (Claude API integration)
- Optional feature with graceful fallback to Bronze behavior
- Cost-aware API usage (<$0.10/day target)
- Backward compatible with Bronze

GOLD TIER PRINCIPLES
- Multi-step plan execution with human approval gates
- External integrations (email, calendar, social media watchers)
- Task decomposition and delegation
- Autonomous execution with approval workflows

PLATINUM TIER PRINCIPLES
- Fully autonomous operation with reflection loops
- Self-correction and learning from mistakes
- 24/7 cloud deployment capability
- Agent-to-agent communication

UNIVERSAL PRINCIPLES (All Tiers)
- Each tier builds on previous (Bronze → Silver → Gold → Platinum)
- Lower tier functionality never breaks when upgrading
- Human oversight decreases gradually: Bronze (100% manual) → Platinum (fully autonomous)
- All tiers respect vault integrity and local-first architecture

Reference the hackathon document for specific tier requirements.

## Response snapshot

Successfully updated the constitution with comprehensive principles for all four tiers:

**Section I: Agent Autonomy & Tier Progression**
- Expanded Bronze tier with complete feature list (Dashboard.md, Company_Handbook.md, basic watchers, Agent Skills)
- Added Silver tier: AI analysis with Claude API, multiple watchers (Gmail+WhatsApp+LinkedIn), Plan.md generation, one MCP server, cost-aware (<$0.10/day), graceful fallback
- Added Gold tier: Cross-domain integration, Odoo Community, social media (Facebook/Instagram/Twitter), multiple MCP servers, weekly CEO briefing, Ralph Wiggum loop, error recovery
- Added Platinum tier: 24/7 cloud deployment, work-zone specialization (Cloud drafts, Local executes), vault sync via Git/Syncthing, agent-to-agent communication, reflection loops, secrets partitioning
- Emphasized backward compatibility and tier progression mandate

**Section III: Local-First Architecture**
- Enhanced Silver tier with rate limiting (10 calls/min), cost monitoring, data sanitization (only title+200 chars to API)
- Enhanced Gold tier with social media integrations, Odoo self-hosted requirements, human approval for external actions
- Added Platinum tier distributed architecture: Cloud VM for watchers, Local for approvals/execution, vault sync, secrets partitioning, network partition tolerance

**New Section IV: Silver Tier Specific Principles**
- Claude API integration with cost awareness and safety measures
- Multiple watcher integration (Gmail, WhatsApp, LinkedIn)
- Plan generation workflow with human approval
- MCP server integration (email recommended)
- Backward compatibility guarantee with Bronze

**New Section V: Gold Tier Specific Principles**
- Cross-domain integration (Personal + Business)
- Odoo Community integration via MCP server (self-hosted, local)
- Social media automation (Facebook/Instagram/Twitter) with draft-first approach
- Multiple MCP servers for different action types
- Weekly Business Audit & CEO Briefing generation
- Error recovery and graceful degradation strategies
- Ralph Wiggum loop for autonomous multi-step completion
- Comprehensive audit logging requirements

**New Section VI: Platinum Tier Specific Principles**
- Cloud VM deployment with health monitoring and process management
- Work-Zone specialization: Cloud (draft & monitor), Local (execute & approve)
- Delegation via synced vault with claim-by-move rule and single-writer rule
- Vault sync strategy (Git or Syncthing) with security partitioning
- Odoo cloud deployment with HTTPS and automated backups
- Reflection loop and self-correction (max 5 iterations)
- Agent-to-agent communication (file-based Phase 1, optional A2A Phase 2)
- Platinum demo requirements (minimum passing gate)

**New Section VII: Universal Principles Across All Tiers**
- Tier progression mandate (sequential: Bronze→Silver→Gold→Platinum)
- Backward compatibility (non-negotiable)
- Human oversight gradient (100% manual → fully autonomous)
- Vault integrity (sacred principle)
- Local-first architecture (default)
- Agent Skills mandate
- Audit logging (all tiers)

**Updated Constitutional Principles Hierarchy**
- Reordered to reflect tier-specific principles
- Added tier implementation order
- Updated version to 2.0.0
- Added amendment note with date 2026-02-11

## Outcome

- ✅ Impact: Constitution now covers all four tiers (Bronze, Silver, Gold, Platinum) with comprehensive principles for hackathon implementation
- 🧪 Tests: No tests required (documentation update)
- 📁 Files: Updated .specify/memory/constitution.md with 400+ new lines of tier-specific guidance
- 🔁 Next prompts: Begin Silver tier feature specification (/sp.specify) or create Silver tier planning document (/sp.plan)
- 🧠 Reflection: Constitution provides clear progression path from monitoring-only (Bronze) to fully autonomous (Platinum) with backward compatibility guarantees and safety principles at each tier

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review - PASS (comprehensive coverage of all four tiers, backward compatibility emphasized, safety principles maintained)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Create Silver tier spec.md to begin implementing AI-powered priority analysis with graceful fallback
