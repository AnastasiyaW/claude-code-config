# Orchestrating Multi-Step Processes

## Problem

LLMs lose track of complex sequences. They skip steps, forget loop counters, confuse branching conditions, and hallucinate completion. The longer the process, the worse it gets. "Fixing" with more detailed prompts opens new failure modes -- each instruction is one more thing the model can misinterpret.

## Quick Comparison

| Aspect | A: Harness Design | B: Proof Loop | C: Deterministic (Memento) | D: Prompt-Only |
|--------|-------------------|---------------|---------------------------|----------------|
| **Infrastructure** | Two agent sessions | 4 role sessions + repo artifacts | Python MCP server | None |
| **Setup cost** | Low | High | Medium | Zero |
| **Reliability at 5 steps** | Good | Excellent | Excellent | Acceptable |
| **Reliability at 20 steps** | Degraded | Good | Excellent | Poor |
| **Recovery on failure** | Manual restart | Fix role + re-verify | Auto-resume from checkpoint | Start over |
| **Verification** | Evaluator (same model) | Fresh session (independent) | Script-based (deterministic) | Self-assessment |
| **Artifacts** | Conversation history | Repo files (.agent/tasks/) | State machine + JSON | None |
| **Cost per run** | ~$9-20 | ~$50-200 | ~$5-15 | ~$2-5 |
| **Best for** | Quality-sensitive single tasks | Mission-critical verification | Long-running automation | Simple sequences |

---

## A: Harness Design (Generator-Evaluator)

**Source:** Anthropic Engineering -- "Harness design for long-running apps"

**Core idea:** Split work into two agents with separate contexts. The Generator produces output. The Evaluator reviews it with calibrated skepticism. They agree on success criteria before starting (Sprint Contract Pattern).

**Pros:**
- [+] Simple to implement -- just two agent sessions
- [+] Works with any LLM provider, no special infrastructure
- [+] Sprint Contract forces concrete success criteria upfront
- [+] Catches self-evaluation bias (models praise their own mediocre work)
- [+] 20x cost over solo agent produces qualitative leap in output

**Cons:**
- [-] Evaluator still has same model's blind spots (both are Claude, both miss the same things)
- [-] No checkpointing -- if Generator fails at step 15 of 20, restart from scratch
- [-] Sprint Contract can drift mid-execution (spec not frozen)
- [-] Conversation history is ephemeral -- knowledge lost between sessions
- [-] Evaluator calibration via few-shot is fragile and task-dependent

**When to choose:** You need better-than-solo quality on a bounded task (code generation, document writing, feature implementation). You have budget for 2x token cost. The task completes in one session.

---

## B: Proof Loop (repo-task-proof-loop)

**Source:** OpenClaw-RL paper (arxiv 2603.10165) + DenisSergeevitch/repo-task-proof-loop

**Core idea:** Frozen spec, durable artifacts, independent verification. Four roles with strict boundaries: Spec-freezer (reads repo, defines AC), Builder (writes code, collects evidence), Verifier (fresh session, writes verdict), Fixer (minimal patches). Loop until all acceptance criteria pass.

**Execution protocol:** `spec freeze -> build -> evidence -> fresh verify -> fix -> verify again`

**Pros:**
- [+] Verifier is a fresh session -- truly independent, not just a different prompt
- [+] All artifacts live in the repository (.agent/tasks/), not conversation history
- [+] Spec frozen before build -- no mid-sprint scope creep
- [+] Durable evidence: agent cannot claim "done" without proof files
- [+] Loop guarantees convergence toward acceptance criteria

**Cons:**
- [-] Heavy setup: 4 distinct roles, each with own session and constraints
- [-] High cost per task (~$50-200 for complex features)
- [-] Overkill for simple changes (adding a config value, fixing a typo)
- [-] Requires disciplined acceptance criteria writing -- garbage AC in = garbage verification out
- [-] Fixer role cannot sign off on its own work, adding another round trip

**When to choose:** The change is mission-critical (payment processing, auth, data integrity). You need auditable proof that requirements are met. The cost of a bug reaching production far exceeds the cost of verification. Regulatory or compliance requirements demand evidence.

---

## C: Deterministic Orchestration

**Core pattern:** Separate deterministic control flow from LLM reasoning. See also: [task-orchestrator](https://github.com/jpicklyk/task-orchestrator), [inngest/agent-kit](https://github.com/inngest/agent-kit)

**Core idea:** The LLM is the wrong tool for controlling deterministic processes. Move control flow out of the model entirely. A state machine (Python MCP server) drives the workflow. The LLM is a "dumb relay" -- it receives one task, executes it, returns the result. The engine decides what happens next.

**Key principles:**
- **Shell Bypass:** Mechanical tasks (test, lint, format) never pass through the LLM -- run as scripts, pass results as structured input
- **Relay Pattern:** Agent sees one task at a time, not the whole workflow
- **State in files:** plan.md with checkboxes, state.json -- agent reads state, does work, updates state

**Pros:**
- [+] Deterministic: same input = same execution path, every time
- [+] Resumable: crash at step 12 of 20? Resume from step 12
- [+] Shell Bypass eliminates token waste on mechanical operations
- [+] No context degradation -- each step gets fresh, focused context
- [+] Scales to 50+ step workflows without quality loss

**Cons:**
- [-] Requires Python MCP server infrastructure (Memento or equivalent)
- [-] Workflow definition is upfront work -- you write the state machine before any execution
- [-] Less flexible for exploratory tasks where the path is not known in advance
- [-] LLM loses big-picture awareness (by design) -- cannot adapt if requirements shift mid-run
- [-] Debugging workflow definitions adds a layer of complexity

**When to choose:** The process is well-defined with known steps (CI/CD pipelines, migration scripts, batch processing). It runs unattended overnight or on a schedule. Reliability matters more than flexibility. You already have Python in your toolchain.

---

## D: Prompt-Only Orchestration

**Core idea:** Write detailed step-by-step instructions in SKILL.md or the prompt itself. No infrastructure, no extra agents. Just tell the model exactly what to do, in order.

**Pros:**
- [+] Zero infrastructure -- works anywhere Claude Code runs
- [+] Zero cost beyond the single session
- [+] Fast to create and iterate -- edit a text file
- [+] Good enough for 3-5 step sequences with clear instructions
- [+] Anyone can read and understand the process

**Cons:**
- [-] Unreliable beyond ~5 steps -- model skips, reorders, or forgets
- [-] No recovery on failure -- if it goes wrong at step 4, you start over
- [-] Self-assessment is unreliable -- model says "done" when it is not
- [-] Context window pressure increases with instruction length
- [-] Each prompt "fix" for one failure mode can create new ones
- [-] No verification beyond "the model says it worked"

**When to choose:** The task is simple and well-bounded (under 5 steps). You are iterating on the process itself and need fast feedback. The consequence of failure is low (dev environment, throwaway output). You want to validate the concept before investing in infrastructure.

---

## Recommendation

**Default progression path:**

1. **Start with D** (prompt-only) for any new process. If it works reliably, stop. Do not add complexity for its own sake.

2. **Graduate to A** (Generator-Evaluator) when you notice quality issues -- the model is producing output that needs human review to catch errors. The evaluator catches what the generator misses.

3. **Move to C** (Deterministic Orchestration) when the process is stable and needs to run unattended, or when step count exceeds ~10. The investment in workflow definition pays off in reliability and resumability.

4. **Use B** (Proof Loop) for mission-critical changes where you need auditable evidence that acceptance criteria are met. The cost is justified by the cost of failure.

**Combinations that work well:**
- C + B: Memento orchestrates the build, Proof Loop verifies the result
- A + D: Start with prompt-only, add an evaluator pass at the end
- C + A: Deterministic orchestration with Generator-Evaluator for creative steps within the pipeline
