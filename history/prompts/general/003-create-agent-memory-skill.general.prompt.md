---
id: 003
title: Create Agent Memory Skill
stage: general
date: 2026-02-11
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: bronze-tier
user: ps_qasim
command: /skill-creator
labels: ["skill-creation","agent-memory","pgvector","chromadb","langchain","vector-database"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/agent-memory/SKILL.md
  - .claude/skills/agent-memory/references/pgvector.md
  - .claude/skills/agent-memory/references/chromadb.md
  - .claude/skills/agent-memory/references/memory-patterns.md
  - .claude/skills/agent-memory.skill
tests:
  - skill validated and packaged via package_skill.py
---

## Prompt

Using your skill creator skill create a new skill for AI Agent Memory Systems. I will use it to implement short-term and long-term memory for AI agents using vector databases and PostgreSQL. Study patterns from LangChain memory, pgvector, and ChromaDB documentation and then build it so no self assumed knowledge.

## Response snapshot

Created the `agent-memory` skill by:
1. Fetching real documentation from pgvector GitHub, ChromaDB docs, LangChain docs
2. Initialized skill with init_skill.py
3. Built SKILL.md with architecture decision table and quick-start examples for all three memory systems
4. Created references/pgvector.md — full SQL reference, HNSW/IVFFlat indexes, distance operators (<->, <=>, <#>), LangChain PGVector API
5. Created references/chromadb.md — all 4 client types, collection CRUD, query/get API with filter operators, embedding functions, HNSW config, LangChain Chroma API
6. Created references/memory-patterns.md — sliding window, summarization, entity/fact extraction, hybrid memory, hot-path vs background writing strategies
7. Validated and packaged to agent-memory.skill

## Outcome

- ✅ Impact: New agent-memory skill available for implementing short-term (in-session) and long-term (pgvector/ChromaDB) memory in AI agents
- 🧪 Tests: Skill validated by package_skill.py — all checks passed
- 📁 Files: SKILL.md + 3 reference files + packaged .skill file
- 🔁 Next prompts: Use /agent-memory when implementing memory for personal-ai-employee agent
- 🧠 Reflection: All API signatures sourced from live documentation (pgvector v0.8.1, ChromaDB current, langchain-postgres). No assumed knowledge.

## Evaluation notes (flywheel)

- Failure modes observed: Parallel Write tool calls conflict when writing to new subdirectory files — use Bash heredoc for new reference files
- Graders run and results (PASS/FAIL): package_skill.py validation PASS
- Prompt variant (if applicable): null
- Next experiment: Test skill triggering by asking about adding memory to an agent
