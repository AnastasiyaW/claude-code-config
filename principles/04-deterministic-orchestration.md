# 04 - Deterministic Orchestration: Keep the LLM Out of Mechanical Work

**Source:** Deterministic orchestration patterns for AI coding agents. See also: [jpicklyk/task-orchestrator](https://github.com/jpicklyk/task-orchestrator), [inngest/agent-kit](https://github.com/inngest/agent-kit)

## Overview

The fundamental problem: LLMs are poor executors of deterministic processes. They forget steps, lose counters in loops, confuse branching conditions, and "fix" prompts that open new unexpected behaviors. The more context accumulates, the worse it gets.

The principle is simple: **mechanical tasks must not pass through the LLM.** Tests, linters, formatters, stack detectors -- these are deterministic. Run them as scripts. Feed the results as structured input to the next step. Reserve the LLM for reasoning, creativity, and judgment.

---

## Shell Bypass Principle

Any task that is deterministic -- meaning the same input always produces the same output -- should execute as a shell command, not as an LLM instruction.

### What qualifies as deterministic

- Running tests (`pytest`, `vitest`, `go test`)
- Linting (`eslint`, `ruff`, `clippy`)
- Type checking (`tsc --noEmit`, `mypy`)
- Formatting (`prettier`, `black`)
- Stack/dependency detection (`package.json` parsing, `go.mod` reading)
- File operations (copy, move, search, grep)
- Git operations (commit, diff, log)

### How to implement

**Wrong approach -- LLM as executor:**
```
"Run the test suite and tell me if it passes"
--> LLM invokes tests with slightly different flags each time
--> LLM interprets output with varying accuracy
--> LLM may hallucinate that tests passed when they did not
```

**Right approach -- Shell bypass:**
```
$ pytest --tb=short -q > test_output.txt 2>&1
$ echo "Exit code: $?" >> test_output.txt
--> Feed test_output.txt to LLM for analysis
--> LLM reasons about failures, not about running tests
```

### Benefits

1. **Token savings** -- deterministic operations do not consume reasoning tokens
2. **Reproducibility** -- same command, same result, every time
3. **No creative interpretation** -- "each time slightly different flags" is eliminated
4. **Structured output** -- JSON/exit codes are unambiguous; free-form text is not

---

## Relay Pattern (One Task at a Time)

For complex multi-step processes, the agent should NOT see the entire workflow. It receives one task, executes it, returns the result, and receives the next task. Control flow lives outside the agent.

### The Problem

When an agent sees a 10-step plan:
- It starts skipping or merging steps around step 5-6
- It loses track of which step it is on
- It "remembers" completing steps it has not actually done
- Quality degrades as the plan grows

### The Solution

Without a full workflow engine, implement the relay pattern through:

#### 1. Break skills into small steps

Each step should be at most one screen of instructions. If a step requires scrolling to read, it is too long.

#### 2. State lives in files, not in the agent's memory

```json
// state.json
{
  "current_step": 3,
  "completed": ["lint", "test", "build"],
  "pending": ["deploy", "verify"],
  "variables": {
    "build_hash": "abc123",
    "test_count": 47
  }
}
```

Or a plan with checkboxes:

```markdown
## plan.md
- [x] Run linter
- [x] Run tests (47 passed, 0 failed)
- [x] Build artifact (hash: abc123)
- [ ] Deploy to staging
- [ ] Verify deployment
```

#### 3. Each step reads state, does work, updates state

The agent does NOT "remember" what happened 5 steps ago. It reads the state file, does its assigned work, writes results back to the state file. The file is the source of truth, not the conversation history.

#### 4. External control flow

Something outside the agent (a script, a human, a workflow engine) decides what step to execute next based on the state file. The agent is a worker, not a planner.

---

## Findings Taxonomy

During development, use structured tags to capture knowledge as it emerges:

| Tag | Purpose | Example |
|---|---|---|
| `[DECISION]` | Architectural decision with rationale | `[DECISION] Use Redis for session store -- PostgreSQL advisory locks too slow under concurrent load` |
| `[GOTCHA]` | Non-obvious behavior or pitfall | `[GOTCHA] docker-compose environment: overrides env_file values -- order matters` |
| `[REUSE]` | Pattern worth remembering | `[REUSE] BullMQ retry pattern: exponential backoff with jitter, maxRetries=3` |
| `[DEFER]` | Out of scope but needs doing later | `[DEFER] Add rate limiting to public API -- not in current sprint` |

### Processing Findings

Raw findings during development are not immediately useful. They must be processed:

1. **Capture** -- Tag findings during development (in comments, commit messages, or a log file)
2. **Triage** -- After the task, review findings. Keep only those relevant to the future. Discard findings that are specific to a resolved issue.
3. **Transform** -- Rewrite as knowledge, not history. "We tried X and it failed because Y" becomes "Y causes X to fail. Use Z instead."
4. **Persist** -- Update CLAUDE.md, memory files, or skill documentation with the transformed knowledge.

---

## Anti-Fabrication

This extends the Proof Loop principle (see [02-proof-loop.md](02-proof-loop.md)) with specific enforcement rules:

### The Rule

An agent **cannot claim** that a task is complete. It must produce durable artifacts that prove completion:

| Claim | Required Artifact |
|---|---|
| "Tests passed" | File containing actual test output with exit code |
| "Review done" | Document with specific findings (file, line, issue) |
| "Subtask complete" | Updated state file with results |
| "Build succeeded" | Build log or artifact hash |
| "Deployment verified" | Health check response or screenshot |

### Special case: Parallel and sub-agent tasks

When using sub-agents or parallel execution:

- Before accepting a sub-agent's result, **verify that the child process actually completed**
- Check the output artifacts, not the status claim
- A sub-agent saying "I finished successfully" is not evidence -- the output file it was supposed to produce IS evidence

---

## context_hint for Sub-Agents

When launching an Agent tool (or any sub-agent) for an isolated task, explicitly specify what context to transfer:

### The Spectrum

- **Too much context:** Agent is overwhelmed, burns tokens on irrelevant information, may get confused by unrelated state
- **Too little context:** Agent lacks necessary information, makes incorrect assumptions, asks unnecessary questions

### The Practice

Include exactly three things in the sub-agent prompt:

1. **What to do** -- the specific task
2. **Relevant state** -- only the files, variables, and context needed for THIS task
3. **Constraints** -- output format, boundaries, what NOT to do

### Example

```
Task: Security review of authentication module
Context: files auth.ts, middleware.ts, session.ts
Check: OWASP top 10 relevant items
Output: JSON with {file, line, severity, description} per finding
Do NOT: modify any files, review non-auth code, check UI
```

This is better than "review security of the whole project" (too broad) or "check auth.ts line 47" (too narrow without context of why).

---

## Tool Registry Pattern (Claw Code)

**Source:** [Claw Code](https://github.com/ultraworkers/claw-code) - clean-room Python+Rust reimplementation of Claude Code architecture (April 2026, 100K+ GitHub stars in days). Specifically the `rust/crates/tools/` crate.

### The pattern

Instead of hard-coding tool invocation inside the agent loop, define tools as **declarative data**:

```rust
pub struct ToolSpec {
    pub name: String,
    pub description: String,         // For the LLM to decide when to use it
    pub input_schema: serde_json::Value,  // JSON Schema object
}
```

The runtime dispatches tools generically by reading the registry, validating input against `input_schema`, consulting the permission policy, and executing. The tool itself does not know about the agent loop; the agent loop does not know about specific tools.

### Why this is deterministic orchestration

The separation is the whole point. Three pieces that used to be entangled are now independent:

1. **Tool definition** - declarative schema (data)
2. **Tool dispatch** - generic runtime logic (shell-bypassable)
3. **Tool execution** - the actual side-effect (often shell-bypassable)

Adding a new tool becomes a pure data change - write a new `ToolSpec`, drop it in the registry, done. The agent loop does not need modification. The LLM discovers the new tool via the description in the prompt. The dispatch layer validates inputs deterministically (JSON Schema validation is not an LLM call).

### The three benefits

1. **Audit surface is tiny.** To know "which tools exist and what can they do," you read the registry. You do not trace through agent code.
2. **Tool tests are isolated.** You can unit-test a tool's side effect without spinning up the full agent. Schema validation is a separate test from execution.
3. **Tool additions do not require LLM prompt changes.** As long as descriptions follow the same conventions, the LLM handles new tools automatically.

### What to avoid

Do **not** treat this as an excuse to ship 200 tools "just in case." Each tool definition adds to every prompt, which both costs tokens and degrades LLM decision quality (more choices = worse choices). Keep the registry lean - 15-25 well-chosen tools that compose, not 200 narrow ones. Claw Code ships 19 built-in tools, which is a reasonable baseline.

### How this relates to our other principles

- **Deterministic Orchestration (this principle):** dispatch logic is a shell-bypassable mechanism, not an LLM reasoning step
- **Skills Best Practices (08):** skill descriptions are model triggers; tool descriptions in a registry work the same way and must follow the same rules
- **Agent Security (10):** the registry is a natural place to attach permission policies - see the Hierarchical Permission Overrides section there

---

## Relationship to Other Principles

| Principle | Relationship |
|---|---|
| **Proof Loop (02)** | Anti-Fabrication is shared: both patterns demand artifacts over claims |
| **Harness Design (01)** | Shell Bypass handles the mechanical evaluation; the LLM handles the creative evaluation |
| **Autoresearch (03)** | The eval scripts in autoresearch ARE the shell bypass -- they must run deterministically |
| **Codified Context (07)** | State files (state.json, plan.md) are codified context -- the relay pattern is context-as-infrastructure in action |
| **Structured Reasoning (05)** | When the agent DOES reason (after receiving deterministic outputs), structured reasoning improves the quality of that reasoning |

---

## When to Apply

**Always apply Shell Bypass for:**
- Running tests, linters, formatters, type checkers
- Git operations
- File system operations
- Any command with deterministic output

**Apply Relay Pattern when:**
- A process has more than 5 steps
- Steps have dependencies (step 3 needs output from step 2)
- The agent keeps forgetting or skipping steps
- Quality degrades toward the end of long processes

**Apply Findings Taxonomy when:**
- Building a new feature or protocol
- Debugging a non-trivial issue
- Any work that generates knowledge worth preserving
