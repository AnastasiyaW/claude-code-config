# 06 - Multi-Agent Task Decomposition

**Source:** [2603.14703] Multi-Agent System Optimization + [2603.13256] Training-Free Multi-Agent Coordination

## Overview

Not every task needs multiple agents. The key question is: does this task involve cross-cutting concerns across multiple files and components, or is it contained within a single function or file? The answer determines whether a single agent suffices or whether decomposition into specialized sub-agents is warranted.

---

## Optimization Levels

### Function-Level (Single Agent)

One agent, one file (or a small set of closely related files). This is the standard workflow and covers the majority of development tasks.

**Characteristics:**
- Changes are localized to one module
- No cross-cutting concerns (security, performance, accessibility all within scope of one file)
- The agent can hold the full context in its working memory
- Verification is straightforward (run the tests for this module)

**Examples:**
- Fix a bug in a utility function
- Add a new API endpoint
- Update a database query
- Refactor a single component

### System-Level (Multi-Agent)

Multiple files, cross-cutting concerns, dependencies between components. A single agent either loses track of the big picture or misses side effects in distant files.

**Characteristics:**
- Changes span 3+ files across different modules
- Side effects in one component affect others (shared state, API contracts, database schema)
- No single agent can hold all relevant context simultaneously
- Verification requires checking multiple integration points

**Examples:**
- Adding a new feature that touches frontend, backend, and database
- Security hardening across multiple services
- Performance optimization that requires changes to caching, queries, and API layer
- Migrating from one library to another across the codebase

---

## Control-Flow and Data-Flow Representation

Before decomposing a system-level task, build a dependency graph. This step is often skipped and its absence is the primary cause of multi-agent coordination failures.

### What to Map

**Control flow:** Which components call which?
```
loginHandler() --> validateCredentials() --> database.query()
                --> createSession() --> redis.set()
                --> generateToken() --> jwt.sign()
```

**Data flow:** What data moves where?
```
User input --> loginHandler (email, password)
           --> validateCredentials (returns user object)
           --> createSession (writes session to Redis, returns session ID)
           --> generateToken (reads user.id, returns JWT)
           --> Response (JWT + session cookie)
```

### Why This Matters

Without the dependency graph:
- Agent A changes the return type of `validateCredentials()` without knowing Agent B depends on the old type
- Agent C optimizes a database query without knowing it feeds a cache that Agent D is also modifying
- The coordinator assigns work to agents based on file boundaries, missing the functional dependencies

With the dependency graph:
- Work boundaries follow data dependencies, not file boundaries
- Side effects are visible before they cause failures
- Integration points are identified upfront and assigned to specific agents

---

## Lightweight Coordinator Pattern

For system-level tasks, replace a monolithic agent with a coordinator plus specialized sub-agents.

### Architecture

```
                    Coordinator
                   (plans, assigns, integrates)
                  /      |       \        \
           Frontend   Backend    Infra    Tests
           Agent      Agent      Agent    Agent
```

### Coordinator Role

The coordinator:
- **Plans** -- breaks the task into sub-tasks based on the dependency graph
- **Assigns** -- gives each sub-task to a specialized agent
- **Integrates** -- combines results, checks for conflicts
- **Does NOT write code** -- the coordinator is a manager, not an implementer

### Sub-Agent Specialization

Each sub-agent handles a domain:

| Agent | Domain | Typical Files | Expertise |
|---|---|---|---|
| Frontend | UI, components, styles | `.vue`, `.tsx`, `.css` | Component APIs, reactivity, accessibility |
| Backend | API, business logic, auth | `.ts` (server), `.py` | REST conventions, validation, security |
| Infra | Docker, CI/CD, configs | `Dockerfile`, `docker-compose.yml`, `.yml` | Networking, volumes, environment variables |
| Tests | Test suites, fixtures | `*.test.ts`, `*.spec.py` | Testing patterns, mocking, coverage |

### Coordination Through Shared Artifacts

Sub-agents do NOT coordinate through conversation history. They coordinate through files in the repository:

- `PLAN.md` -- the coordinator's task breakdown with assignments
- `CONTRACTS.md` -- API contracts and interfaces between components
- `STATE.json` -- current progress, completed items, blockers
- Individual agent output files in designated directories

This means:
- Any agent can be replaced or restarted without losing coordination state
- The coordinator can check progress by reading files, not by remembering conversations
- Conflicts between agents are visible in the artifacts (two agents modifying the same contract)

---

## Decomposition Guidelines

### When to stay single-agent

- Task touches 1-2 files
- No cross-module dependencies
- Straightforward, well-defined changes
- The full context fits in one session

### When to decompose

- Task touches 3+ files across modules
- Changes in one file affect behavior in another
- Multiple specializations needed (frontend + backend + infra)
- The task is too large for one session's context window

### How to decompose

1. **Map dependencies** -- build the control-flow and data-flow graph
2. **Identify boundaries** -- find natural seams where components interact through defined interfaces
3. **Assign by domain** -- group related files into sub-tasks aligned with agent expertise
4. **Define contracts** -- specify the interfaces between sub-tasks (API shapes, data formats, shared state)
5. **Plan integration order** -- determine which sub-tasks must complete before others can start

---

## Coordination Patterns: Two Real-World Implementations

There are two distinct production-tested approaches to sub-agent coordination, each with a different tradeoff profile. Both validate our "coordination via artifacts, not conversation history" principle, but they diverge on whether sub-agents share context or stay isolated.

### Pattern A: Shared Workspace (Paperclip)

**Real-world implementation:** [Paperclip](https://github.com/paperclipai/paperclip) - 43K+ stars in 3 weeks, CEO -> managers -> workers hierarchy built on file-based coordination.

**How it works:**
- Coordinator writes task assignments to `/assignments/<task-id>/`
- Sub-agents read from assignments, write results to `/results/<task-id>/`
- All communication through shared filesystem - no message queues, no shared conversation context
- Agents run in discrete "heartbeats" (triggered by task availability), not continuous loops
- Atomic task checkout prevents duplicate work (claim + allocate budget + return assignment in one transaction)

**Strengths:**
- Scales to 50+ agents without context window collapse
- Any agent can be replaced or restarted mid-task - state is durable on disk
- Coordinator reads progress by scanning files, not by remembering conversations
- Conflict detection is cheap (two results in the same file = visible diff)

**Weaknesses:**
- No security isolation - malicious code in one agent sees results from others
- Requires deterministic task IDs and directory discipline
- Agents must all trust the same filesystem

**Use when:** You are coordinating many trusted agents on loosely-coupled work. Typical case: documentation pipeline (researcher -> writer -> editor -> publisher), where each agent has a clear handoff format.

### Pattern B: Sandbox Isolation (DeerFlow 2.0)

**Real-world implementation:** [DeerFlow 2.0](https://github.com/bytedance/deer-flow) - ByteDance, 44K+ stars, LangGraph-based with per-agent Docker sandboxes.

**How it works:**
- Lead planner breaks task into N subtasks, spawns N sub-agents in parallel
- Each sub-agent runs in an isolated Docker container: own filesystem, terminal, browser, MCP server
- Sub-agents CANNOT see the parent context or each other's context
- Lead planner synthesizes structured outputs (not raw conversation) back into a single result
- Virtual path translation prevents sub-agents from reading host paths

**Strengths:**
- Security first: a compromised sub-agent cannot corrupt others or the host
- Context isolation forces clean decomposition - if a sub-agent needs data from a sibling, that becomes an explicit parent-mediated call
- Native Kubernetes path for enterprise deployment
- Prevents "context pollution" where one agent's exploration degrades another's focus

**Weaknesses:**
- Docker overhead (100-500MB per agent) limits parallelism to ~10-15 agents
- Coordination logic must live in the parent planner, which becomes a bottleneck
- Harder to debug - you cannot `grep` across all sub-agents' state

**Use when:** You are running untrusted code, processing sensitive data, or the task requires strict blast-radius control. Typical case: code execution for user-submitted tasks, security analysis, or sub-agents using third-party MCP tools of unknown provenance.

### Choosing Between Them

| Dimension | Shared Workspace (Paperclip) | Sandbox (DeerFlow) |
|---|---|---|
| **Max agents** | 50+ | 10-15 |
| **Trust model** | All agents trusted | No agent trusted |
| **Setup cost** | Zero (just filesystem) | Docker + orchestration |
| **Debugging** | Easy (grep all files) | Hard (isolated containers) |
| **Coordination overhead** | Distributed (each agent checks for new work) | Centralized (parent planner) |
| **Best for** | Pipelines, documentation, research | Code execution, security, untrusted input |

**Hybrid pattern:** Nothing prevents using both. Run a shared-workspace coordinator (trusted) that spawns sandboxed sub-agents (untrusted) when a task requires running unknown code. Results flow back into the shared workspace for downstream consumption.

---

## Relationship to Harness Design

Multi-Agent Decomposition extends the Generator-Evaluator pattern from [Harness Design (01)](01-harness-design.md):

| Pattern | Roles | When to Use |
|---|---|---|
| Solo agent | One agent does everything | Function-level tasks |
| Generator-Evaluator | Generator + Evaluator | Quality-critical single-domain tasks |
| Coordinator pattern | Coordinator + N specialized sub-agents | System-level multi-domain tasks |

The coordinator IS the third role. For tasks spanning more than 3 files, consider multi-agent decomposition. For tasks within a single domain but requiring quality assurance, the Generator-Evaluator suffices.

---

## Common Pitfalls

### 1. Premature decomposition

Splitting a simple task across multiple agents adds coordination overhead without quality benefit. If one agent can do it reliably, use one agent.

### 2. File-based boundaries instead of functional boundaries

Assigning "all .ts files to Agent A and all .py files to Agent B" ignores functional dependencies. The authentication flow might span both TypeScript and Python files. Boundaries should follow the dependency graph, not the file system.

### 3. Missing contracts

Without explicit interface contracts, sub-agents make incompatible assumptions. Agent A returns `{user_id: number}` while Agent B expects `{userId: string}`. Define contracts before parallel work begins.

### 4. Coordinator doing implementation

If the coordinator starts writing code, it loses its planning perspective. The coordinator should focus on decomposition, assignment, and integration -- not implementation.

---

## Cross-Agent Trajectory Sharing (HACRL Pattern)

Source: [2603.02604] HACRL -- Heterogeneous Agent Collaborative RL (Mar 2026)

In reinforcement learning, HACRL shows that heterogeneous models (different sizes, architectures) training together and **sharing successful reasoning trajectories** outperform isolated training. The key insight: it is bidirectional -- a smaller model can teach a larger one if it found a better reasoning path. At inference, models are fully independent (no coordination overhead).

### Practical Application to Multi-Agent Systems

This principle translates directly to agentic coding:

1. **Session learning as trajectory sharing.** Each Claude Code session is a "rollout." Successful patterns extracted into memory files become shared trajectories that improve all future sessions. This is the practical equivalent of HACRL's rollout sharing.

2. **Heterogeneous agent composition.** When launching parallel sub-agents, give them **different strategies** (conservative vs aggressive, breadth-first vs depth-first). Homogeneous agents produce homogeneous blind spots. HACRL shows diversity of perspectives + sharing winners > single strategy grinding.

3. **Share successful patterns, not raw outputs.** HACRL agents do not share everything -- they share **verified successful trajectories**. In practice: extract the pattern/approach that worked, not the full conversation history. Memory files should capture the reusable insight, not the debugging session.

4. **Independent at inference.** Sub-agents do not need runtime coordination if they share knowledge through artifacts (PLAN.md, CONTRACTS.md, memory files). This is why shared artifacts > conversation-based coordination -- it mirrors HACRL's "train together, infer independently."

### Production Validation: Claude Code Review

Anthropic's Code Review (Mar 2026) is a production implementation of parallel specialized agents:
- Fleet of agents, each checking a different class of bugs
- Verification step for cross-validation of false positives
- <1% of findings marked incorrect by engineers
- Confirms: parallel specialized agents > monolith reviewer

---

## Relationship to Other Principles

| Principle | Relationship |
|---|---|
| **Harness Design (01)** | Decomposition extends Generator-Evaluator with a coordinator role |
| **Proof Loop (02)** | Each sub-agent's output can be verified independently through the proof loop |
| **Autoresearch (03)** | HACRL's trajectory sharing strengthens autoresearch: diverse strategies in parallel + share winners |
| **Deterministic Orchestration (04)** | The coordinator's task assignment and integration checking can be partially deterministic (scripts checking contract compatibility) |
| **Codified Context (07)** | Shared artifacts (PLAN.md, CONTRACTS.md, STATE.json) are codified context that enables coordination without shared conversation history -- mirrors HACRL's "train together, infer independently" |
