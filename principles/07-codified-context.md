# 07 - Codified Context: Context as Infrastructure

**Source:** [2602.20478] Codified Context: Infrastructure for AI Agents in a Complex Codebase

## Overview

AI coding agents have no project memory -- every session starts from zero. Files like CLAUDE.md and memory directories help, but treating them as documentation misses their true purpose. The key insight: **context is infrastructure, not documentation.** CLAUDE.md is a runtime config for the agent. Rules are conditional context injection. Memory files are persistent state. Plans and decisions are structured handoff artifacts.

When you stop thinking "how do I document this for the agent?" and start thinking "how do I configure the agent's runtime environment?", the quality of context engineering improves dramatically.

---

## Context as Infrastructure

### The Mindset Shift

| Documentation Mindset | Infrastructure Mindset |
|---|---|
| CLAUDE.md is a wiki | CLAUDE.md is a runtime config |
| `.claude/rules/` is a reference guide | `.claude/rules/` is conditional context injection |
| Memory files are notes | Memory files are persistent state |
| PLAN.md is a log | PLAN.md is structured handoff |
| DECISIONS.md is history | DECISIONS.md is cached reasoning |

### What Each File Type Really Is

**CLAUDE.md -- Runtime Configuration**

This file is loaded at the start of every session. It defines:
- What the agent can and cannot do
- How the agent should behave in specific situations
- Key architectural facts the agent needs for any task
- Operational constraints (SSH rules, deployment procedures)

It is NOT a place for historical notes, meeting minutes, or general project documentation. Every line should be something the agent needs to know to function correctly.

**`.claude/rules/` -- Conditional Context Injection**

Rules files are injected into context based on conditions (file patterns, task types). They are:
- Loaded on demand, not always present
- Specific to a domain or file type
- Instructions, not descriptions

Example: A rule that activates when editing `*.test.ts` files should contain testing conventions, not a history of how the test framework was chosen.

**Memory Files -- Persistent State**

Memory files track state that persists across sessions:
- What was done in previous sessions
- Current status of long-running tasks
- Known issues and their workarounds
- Credentials, endpoints, and configuration values

They are NOT journals or diaries. They are key-value state stores written in markdown for human readability.

**PLAN.md / TODO.md / DECISIONS.md -- Structured Handoff**

These files exist to transfer state between sessions:
- PLAN.md: current plan with completed/remaining items
- TODO.md: actionable items with priority and context
- DECISIONS.md: architectural decisions with rationale (so future sessions do not re-debate settled questions)

They are NOT logs of what happened. They describe the current state of the world and what should happen next.

---

## JIT Context Loading

Loading the entire project into context is wasteful and counterproductive. Large contexts:
- Burn tokens on irrelevant information
- Dilute important facts with noise
- Cause the model to lose focus on the actual task

### The Principle

Load only what is needed for the current step. This is Just-In-Time (JIT) context loading:

1. **Start with minimal context** -- CLAUDE.md, the task description, and the specific files being modified
2. **Load on demand** -- when the agent needs information about a component, load that component's context (rules, docs, related files)
3. **Write results to files** -- instead of accumulating results in conversation history, write them to state files
4. **After compaction** -- re-inject only critical state, not the full conversation

### Example Workflow

```
Step 1: Agent loads CLAUDE.md + task "fix auth bug"
Step 2: Agent reads auth.ts, middleware.ts (JIT load of relevant files)
Step 3: Agent writes findings to .agent/investigation.md (result to file)
Step 4: Context compaction occurs
Step 5: Agent re-loads CLAUDE.md + .agent/investigation.md (re-inject critical state)
Step 6: Agent applies fix based on documented findings
```

Without JIT loading, the agent would try to hold the entire investigation in conversation history, lose details during compaction, and potentially re-investigate from scratch.

---

## Context Engineering Pipeline

The full pipeline for managing context in an AI agent system:

```
rules --> state --> JIT retrieval --> pruning --> compaction policy --> re-inject --> isolation
```

### Stage 1: Rules

Static context that applies conditionally:
- CLAUDE.md (always loaded)
- `.claude/rules/*.md` (loaded based on file patterns or task type)
- Project-specific conventions and constraints

### Stage 2: State

Dynamic context from previous sessions:
- Memory files (MEMORY.md, task-specific state)
- Plans, todos, decisions
- Known issues and workarounds

### Stage 3: JIT Retrieval

On-demand context for the current task:
- Read specific files when needed
- Search codebase for relevant patterns
- Load documentation for specific APIs or libraries

### Stage 4: Pruning

Remove irrelevant context before it accumulates:
- Drop file contents that have been fully processed
- Remove investigation notes that led to dead ends
- Clear temporary state that is no longer needed

### Stage 5: Compaction Policy

Define what survives context compaction:
- Critical facts (architecture, constraints, active bugs)
- Current task state (what is done, what remains)
- Decisions and their rationale

What does NOT survive:
- Raw file contents (can be re-read)
- Exploration history (only conclusions matter)
- Verbose output (only summaries matter)

### Stage 6: Re-Inject

After compaction, restore critical context:
- CLAUDE.md (always)
- Current task state file
- Active decisions and constraints

### Stage 7: Isolation

Different tasks should have isolated contexts:
- Sub-agents get only their relevant context (see [context_hint in 04](04-deterministic-orchestration.md))
- Parallel tasks do not share conversation history
- State is exchanged through files, not through context

---

## Research Evidence: Quality > Quantity

Two studies reached contradictory conclusions about context files:

**Study 1** (arxiv 2601.20404, Jan 2026): AGENTS.md files reduce task time by 28.6% and token consumption by 16.5%.

**Study 2** (ETH Zurich, Feb 2026): LLM-generated context files **decrease** success rate by 3%, **increase** inference cost by 20%, and add 2-4 extra reasoning steps.

**Resolution:** The difference is content quality. Auto-generated context that restates what the agent can infer from code is noise -- it costs tokens and dilutes focus. Human-written context with **non-inferable** information (specific build commands, custom flags, operational gotchas from real incidents) is what helps.

**The Rule:** Only include in CLAUDE.md what the agent **cannot derive** from reading the code. If the agent could figure it out by reading `package.json` or the source, it does not belong in CLAUDE.md. If it is a hard-won lesson from a production incident, a non-obvious architectural constraint, or a specific command that differs from the default -- that is exactly what CLAUDE.md is for.

---

## Practical Guidelines

### Writing Effective CLAUDE.md

**Do:**
- State constraints concisely ("SSH: one tunnel per host, no parallel connections")
- Include facts that affect every task ("ssr:false -- meta tags in source, content invisible to bots")
- Include non-inferable knowledge (build quirks, deployment gotchas, operational lessons)
- Update immediately when facts change

**Do not:**
- Let an LLM auto-generate CLAUDE.md content (ETH Zurich: -3% success rate)
- Include historical narratives ("Last week we tried X and it did not work")
- Restate what is obvious from the code (frameworks used, file structure, standard patterns)
- Duplicate information available elsewhere ("See architecture.md for details" is better than copying architecture.md)
- Include task-specific state (that belongs in memory files)

### Writing Effective Memory Files

**Do:**
- Use structured formats (headers, bullet points, tables)
- Include dates for time-sensitive information
- Mark items as resolved/active
- Include the "why" alongside the "what"

**Do not:**
- Write prose paragraphs (hard to scan, hard to update)
- Keep resolved issues without marking them (the agent will treat them as active)
- Include verbose descriptions when a one-liner suffices

### Writing Effective Rules

**Do:**
- Make rules actionable ("When editing *.test.ts, use vitest, not jest")
- Include examples of correct and incorrect patterns
- Keep rules under 500 words (rules that are too long get ignored)

**Do not:**
- Write rules that apply to everything (those belong in CLAUDE.md)
- Include rationale longer than the rule itself
- Create rules for edge cases that occur once a year

---

## Relationship to Other Principles

| Principle | Relationship |
|---|---|
| **Harness Design (01)** | Structured handoff artifacts enable context reset between Generator and Evaluator sessions |
| **Proof Loop (02)** | The `.agent/tasks/` directory structure is codified context -- durable artifacts stored as infrastructure |
| **Autoresearch (03)** | The experiment log (git history) and scoring artifacts are codified context for future optimization runs |
| **Deterministic Orchestration (04)** | State files (state.json, plan.md) are the relay pattern in action -- file-based state instead of memory-based state |
| **Multi-Agent Decomposition (06)** | Shared artifacts (PLAN.md, CONTRACTS.md) enable coordination between agents without shared conversation history |
| **Skills Best Practices (08)** | Skills themselves are codified context -- reusable packages of knowledge and procedure |
