# Claude Global Rules

## Quality of Solutions -- Core Principle

We do not pick the easiest path. We pick the best, highest-quality, most stable solution.

- Between a monkey-patch and a rewrite -- **always rewrite** (cleanly, with understanding), then verify.
- Between a quick hack and proper architecture -- proper architecture.
- After any rewrite -- **mandatory verification**: test, run, read the diff.
- Complexity is justified only when it produces more stability, not just because "it works."

## Supply Chain Defense

Always gate fresh packages. Most supply chain attacks are caught within 1-3 days; 7 days is a comfortable buffer.

```ini
# ~/.npmrc
min-release-age=7
```

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

When installing new dependencies in any project -- verify these configs are in place. Same for CI runners.

## Documentation First, Action Second -- NEVER Guess

**CRITICAL:** Before any fix or change to a server/infrastructure:

1. **Find documentation** -- CLAUDE.md, internal docs/, Slack threads, Confluence, README. If no docs exist -- ask the user.
2. **Find the source code** -- read the code responsible for the problem, understand the full flow.
3. **Understand the architecture** -- how components connect, what proxies/tunnels/DNS the traffic flows through.
4. **Only then act** -- with understanding of what exactly you are changing and why.

**FORBIDDEN:**
- Changing configs (hosts, env, ports) without understanding WHY the current values are set that way
- "Trying to fix" by trial and error -- every blind change can break a working system
- Ignoring non-obvious architecture (proxies, SNI tunnels, iptables redirects) -- if a value looks strange (e.g. `127.0.0.1` for an external service), first UNDERSTAND why it is that way

**Lesson learned:** `127.0.0.1 s3.example.com` looks like a bug, but it could be an SNI proxy through a local tunnel. "Fixing" it to the real IP can break uploads.

After making any change:
1. Review the code diff and check if it adheres to code style and guidelines of the project.
2. Review CLAUDE.md and relevant .claude/rules of the project and update them to be accurate given the changes.
3. Push changes to GitHub. If no repo exists yet -- offer to create a **private** one (`gh repo create --private`). Never create a public repo without explicit request.

## Skills -- Best Practices

When creating or updating any skill in `.claude/skills/`:

**Description = trigger for the model, not a description for humans:**
```
[What it does] + [When to use -- specific phrases] + [Key capabilities]
```
Bad: `"Helps with servers."` -- Good: `"Use when: service hangs, GPU health check, tunnel issues on port 2222."`

**Mandatory sections in SKILL.md:**
- `## Gotchas` -- populate from real failures, update on every edge case
- `## Troubleshooting` -- symptom -> cause -> fix

**File structure:** Keep SKILL.md under 5000 words. Details go in `references/`. Scripts go in `scripts/`. No `README.md` inside a skill folder.

**Critical validations belong in scripts**, not words. Code is deterministic; language is not.

## Harness Design -- Multi-Agent Architecture Principles

Source: Anthropic Engineering -- "Harness design for long-running apps"

### Generator-Evaluator Pattern (GAN-inspired)
- **Generator** and **Evaluator** are separate agents. Models praise their own work even when quality is mediocre (self-evaluation bias).
- Evaluator must be **independent**: separate context, separate prompt, calibrated skepticism.
- Calibrate the evaluator via few-shot examples with detailed score breakdowns.

### Sprint Contract Pattern
- Before implementation: generator and evaluator **agree** on "done" criteria.
- Concrete, testable success criteria -- not abstract user stories.
- Bridge between "what the user wants" and "what the code verifies."

### Context Management
- **Context reset > compaction** for long tasks. Compaction preserves continuity but does not give a clean slate.
- Structured handoff artifacts -- pass state between sessions via documents, not conversation history.
- **Context anxiety**: models start wrapping up work prematurely, thinking context is running out.

### Assumption Testing
- Every harness component encodes an **assumption** about what the model cannot do on its own.
- These assumptions **become stale** as models improve.
- Strategy: **remove components** and measure impact. Simplest solution first, complexity only when needed.

### Quality Criteria (Frontend)
- **Design Quality** -- coherence, not a collection of parts
- **Originality** -- penalize template layouts, library defaults, AI slop (purple gradients on white cards)
- **Craft** -- typographic hierarchy, spacing consistency, color harmony, contrast
- **Functionality** -- user completes the task without guessing

### Cost vs Quality
- Solo agent: ~$9, 20 min -- broken core, layout issues
- Full harness: ~$200, 6 hours -- working product, polish, AI features
- **20x cost leads to a qualitative leap.** Evaluator is justified when the task exceeds reliable solo performance.

### Proof Loop Pattern (repo-task-proof-loop)
Source: OpenClaw-RL paper (arxiv 2603.10165) + DenisSergeevitch/repo-task-proof-loop

**Principle: next-state signals as universal proof.** Test results, tool outputs, user reactions -- all of these are verification evidence. An agent cannot simply "claim" completion -- durable artifacts are required.

**Execution Protocol:** `spec freeze -> build -> evidence -> fresh verify -> fix -> verify again`
- **Spec freeze**: AC1, AC2... -- concrete acceptance criteria, frozen before implementation
- **Build**: implement the minimal safe changeset
- **Evidence**: builder collects proof (tests, logs) in read-only mode
- **Fresh verify**: NEW session checks repo state, writes verdict.json
- **Fix**: minimal fixes per problems.md, regenerate evidence
- **Loop**: repeat until verdict = PASS on all ACs

**4 sub-agent roles with strict boundaries:**
- **Spec-freezer** -- reads repo, does not touch code
- **Builder** -- writes code, then switches to read-only for evidence
- **Verifier** -- fresh session, has not seen the build process, writes only verdict
- **Fixer** -- minimal fixes, cannot sign off on final result

**Key differences from Anthropic harness:**
- All artifacts live **in the repository** (.agent/tasks/), not in conversation history
- Verifier = **fresh session** (not just a separate prompt, but a separate context)
- Spec frozen **before** build (Anthropic Sprint Contract can change mid-sprint)
- Recommended for Codex (best sub-agents), but works in Claude Code too

## Autoresearch -- Iterative Self-Optimization

Source: Andrej Karpathy (github.com/karpathy/autoresearch, Mar 2026) + uditgoenka/autoresearch (universal Claude Code plugin)

**Principle: any measurable output can be improved automatically.** Cycle: Read -> Change ONE thing -> Test mechanically -> Keep/Discard -> Repeat. Works on skills, prompts, code, templates -- anything with a numerical score.

### Three Conditions for Applicability
1. **Numerical scoring** -- binary pass/fail criteria -> percentage score
2. **Automated evaluation** -- eval scripts without human involvement
3. **Single-file mutation** -- one target file changes per iteration

### Key Rules
- **One change per iteration** -- atomicity = clear causality
- **Mechanical verification only** -- metrics, not opinions. Agents game subjective scales
- **Git = memory** -- `experiment:` commits, git revert on failure
- **Guard mechanism** -- Verify (did the metric improve?) + Guard (did nothing break?)
- **3-6 binary assertions** -- <3 = loopholes, >6 = checklist gaming

### Relationship to Other Practices
- **vs Proof Loop**: proof loop *verifies* (pass/fail on ACs), autoresearch *optimizes* (iteratively)
- **vs Harness Design**: autoresearch = automatic Generator-Evaluator without manual review
- **Combination**: autoresearch for optimization -> proof loop for final verification
- **Cost**: ~$0.10/cycle, $5-25/night for 50-100 experiments

### When to Apply
- Improving skills/prompts with a measurable pass rate
- Optimizing code by metric (coverage, latency, bundle size)
- **Do NOT apply** to subjective tasks without scriptable evaluation

### HyperAgent Upgrade Path (from [2603.19461])

Autoresearch = linear cycle. HyperAgents shows three levels of evolution:

**Level 1 -> Level 2: Branching Version Graph**
Instead of linear keep/discard -- a tree of experiments with `select_next_parent`. Allows parallel exploration of multiple directions, then pick the best branch.

**Level 2 -> Level 3: Meta-optimization**
The mutation strategy itself changes. Every ~20 iterations, analyze which types of changes produced growth, update the search strategy. imp@50 metric: 0 -> 0.63 in ~200 iterations.

**Level 3 -> Level 4: Multi-task Transfer**
When optimizing multiple artifacts in parallel, improvement patterns (e.g. "persistent memory helps") transfer between tasks via a shared meta-agent.

**Emergent behaviors**: an agent without instructions begins creating persistent memory, performance tracking, tools -- context as infrastructure, invented automatically.

**Execution infrastructure -- Contree:**
Contree microVM = native implementation of the version graph: `result_image` UUID = immutable snapshot, `disposable=false` = save branch, `wait=false` x N = parallel exploration, `set_tag` = mark best parent. Full isolation, zero-cost rollback, 3-5 mutations in parallel. Self-modifying code runs in sandbox, not on host.

## Deterministic Orchestration

Core pattern: separate deterministic control flow from LLM reasoning.

**Fundamental problem:** An LLM is a terrible executor of deterministic processes. It forgets steps, loses count in loops, confuses branching conditions. "Fixes" to prompts open new unexpected behaviors. The bigger the context, the worse it gets.

### Shell Bypass Principle
Mechanical tasks (test, lint, format, stack detection) **must not go through the LLM**. They are deterministic -- run them via scripts, pass the result as input for the next step.

**Practice:**
- Validations -> shell scripts, not instructions in the prompt
- `pytest`, `eslint`, `tsc --noEmit` -> Bash tool directly, without "creative" wrappers
- Script results -> structured output (JSON/exit code), not free-form text
- This saves tokens AND removes non-determinism ("slightly different flags every time")

### Relay Pattern (One-Task-at-a-Time)
For complex multi-step processes, the agent should NOT see the entire process. It receives one task, executes, returns the result, receives the next. Control flow is external.

**Without a full workflow engine, this means:**
- Break a complex skill into a chain of small steps (each <= 1 screen)
- Store state in a file (plan.md with checkboxes, state.json), not in the agent's head
- Each step reads state -> does work -> updates state
- The agent does not "remember" what happened 5 steps ago -- it reads the file

### Findings Taxonomy
During feature/protocol development -- structured tags for knowledge capture:
- `[DECISION]` -- architectural decision (why we chose X over Y)
- `[GOTCHA]` -- pitfall, non-obvious behavior
- `[REUSE]` -- pattern worth remembering for reuse
- `[DEFER]` -- out of scope, but needs to be done later (-> backlog)

**Flow:** development -> tagged findings -> triage (keep only future-relevant) -> transform into knowledge (rewrite as knowledge, not history) -> update CLAUDE.md / memory.

### Anti-Fabrication (extension of Proof Loop)
An agent **cannot claim** that a task is done -- durable artifacts are required:
- Tests passed? -> file with output, not the text "tests passed"
- Review done? -> artifact with findings, not "I checked, everything is fine"
- Subtask completed? -> check the state file, do not trust the claim
- **Especially for parallel/subagent tasks**: before accepting a result -- verify that child runs actually completed
- **Deletion = re-verification.** After executing a delete command (file, container, resource, branch), **always verify** the object is actually gone (`ls`, `docker ps`, `git branch`, etc.). Do not consider it deleted until confirmed. Commands can exit successfully without doing anything (permissions, locks, wrong path).

### context_hint for Sub-agents
When launching an Agent tool for an isolated task -- explicitly specify what context to pass:
- Not "send everything" (overload) and not "send nothing" (context loss)
- In the prompt for Agent include: (1) what we are doing, (2) only relevant state, (3) constraints
- Example: "Do a security review. Context: files X, Y, Z. Check: OWASP top 10. Format: JSON with severity."

## Structured Reasoning Protocol

Source: [2603.01896] Agentic Code Reasoning (Mar 2026)

**For complex tasks (debugging, architecture, optimization) -- replace free-form chain-of-thought with semi-formal reasoning:**

1. **Premises** -- what we know for certain (facts from code, logs, tests)
2. **Execution trace** -- step-by-step tracing of control-flow and data-flow
3. **Conclusions** -- what formally follows from premises + trace
4. **Rejected paths** -- which hypotheses were tested and discarded (with reason)

This eliminates "planning hallucinations" -- when the model builds plausible but incorrect chains of reasoning. Structured prompting > free-form for coding.

**When to apply:** debugging (non-obvious cause), architecture decisions (>2 options), performance optimization, security review. NOT needed for simple CRUD tasks.

## Multi-Agent Task Decomposition

Sources: [2603.14703] Multi-Agent System Optimization, [2603.13256] Training-Free Multi-Agent Coordination

### Optimization Levels
- **Function-level** -- one agent, one file -> standard workflow
- **System-level** -- multiple files, cross-cutting concerns -> needs multi-agent

### Control-flow + Data-flow Representation
Before system-level optimization: build a dependency graph (which components call which, which data flows where). This reveals bottlenecks and side effects invisible at function-level analysis.

### Lightweight Coordinator Pattern
Instead of a monolithic agent -- coordinator + specialized sub-agents:
- Coordinator distributes tasks, does not write code
- Sub-agents are specialized (frontend, backend, infra, tests)
- Coordination via shared artifacts (files in repo), not conversation history

### Relationship to Harness Design
This extends Generator-Evaluator: coordinator = third role. For tasks touching >3 files, consider multi-agent decomposition.

### Cross-Agent Trajectory Sharing (HACRL Pattern)

Source: [2603.02604] HACRL -- Heterogeneous Agent Collaborative RL

**Principle**: heterogeneous models share **successful reasoning trajectories** during training. Bidirectional -- a smaller model can teach a larger one. At inference -- fully independent.

**Practical implementation in Claude Code:**
- Each session = rollout. Successful patterns -> memory files = trajectory sharing between sessions
- Multi-agent tasks: agents with different strategies (conservative vs aggressive) -> share successful approaches through artifacts
- Session Learning Extraction (below) = the mechanism for trajectory sharing

**Result**: +3.3% vs baseline at **half** rollout cost. Diversity of approaches + sharing winners > single model grinding.

## REVIEW.md -- Review-Specific Guidance

Source: code.claude.com/docs/en/code-review (Mar 2026)

**REVIEW.md** -- a file in the repo root, read **only** during code review (not during regular sessions).

**Purpose**: separate review-specific rules from CLAUDE.md -- "what to flag during review" should not clutter everyday instructions.

**Structure:**
```markdown
## Always check
- New API endpoints have integration tests
- DB migrations are backward-compatible
## Style
- Prefer match over chained isinstance
## Skip
- Generated files under src/gen/
```

**Severity taxonomy:**
| Marker | Level | Meaning |
|--------|-------|---------|
| 🔴 | Important | Blocker before merge |
| 🟡 | Nit | Worth fixing, not blocking |
| 🟣 | Pre-existing | Bug predates the PR |

**Bidirectional**: if a PR makes CLAUDE.md/REVIEW.md outdated, that is also a finding.

## Session Learning Extraction -- Memory Between Sessions

Source: Lukyanenko BigTech patterns (Mar 2026)

**Principle**: after each session, automatically collect "learnings" and merge into memory. This is the practical implementation of HACRL trajectory sharing -- successful reasoning from session N is available in session N+1.

**What to extract:**
1. **New capabilities** -- the model learned to do X (new tool, workflow, framework)
2. **Corrections** -- user corrected the approach (-> feedback memory)
3. **Permissions granted** -- new allowed commands (-> settings)
4. **Bugs + fixes** -- symptom -> cause -> fix (-> gotchas in skill or CLAUDE.md)
5. **Decisions** -- architectural decisions with rationale (-> DECISIONS.md or memory)

**Mechanism**: hook at session end or `/revise-claude-md` skill + structured extraction -> merge into memory/CLAUDE.md.

## Codified Context -- Context as Infrastructure

Source: [2602.20478] Codified Context: Infrastructure for AI Agents in a Complex Codebase

**Problem:** AI coding agents have no project memory -- every session starts from scratch. CLAUDE.md + memory help, but are insufficient for complex codebases.

**Principle: context = infrastructure, not documentation.**
- CLAUDE.md is not a wiki, it is **runtime config** for the agent
- `.claude/rules/` is **conditional context injection**, not a reference manual
- Memory files are **persistent state**, not notes
- `PLAN.md`, `TODO.md`, `DECISIONS.md` are **structured handoff**, not logging

**Practice: JIT context loading**
- Do not load the entire project into context
- Load only what is needed for the current step
- Step result -> to a file, not to chat
- After compaction -> re-inject only critical state

This reinforces the Context Engineering pipeline:
```
rules -> state -> JIT retrieval -> pruning -> compaction policy -> re-inject -> isolation
```
