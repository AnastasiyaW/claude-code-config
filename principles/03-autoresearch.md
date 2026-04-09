# 03 - Autoresearch: Iterative Self-Optimization

**Source:** Andrej Karpathy (github.com/karpathy/autoresearch, Mar 2026) + uditgoenka/autoresearch (universal Claude Code plugin) + HyperAgents paper [2603.19461]

## Overview

Autoresearch is the principle that any artifact with a measurable output can be improved automatically through iterative experimentation. The cycle is simple: Read the current state, change ONE thing, test mechanically, keep or discard the change, repeat. It works on skills, prompts, code, templates -- anything where you can compute a numerical score.

---

## Three Conditions for Applicability

Before applying autoresearch, verify all three conditions are met:

### 1. Numerical Scoring

The artifact must have a score that can be expressed as a number.

- Binary pass/fail criteria aggregated into a percentage score
- Example: 5 out of 8 test cases pass = 62.5%
- Example: Prompt achieves 73% accuracy on evaluation set

**If you cannot define a numerical score, autoresearch does not apply.** Subjective assessments ("does this look good?") are not amenable to automated optimization because agents will game subjective scales.

### 2. Automated Evaluation

Evaluation must run without human involvement.

- Eval scripts that return a number or pass/fail
- Test suites with deterministic outcomes
- Benchmark harnesses with reproducible results

**If evaluation requires human judgment, autoresearch will not converge.** The feedback loop must be fully mechanical.

### 3. Single-File Mutation

Each iteration changes exactly one target file.

- One prompt file, one config file, one skill file
- Atomicity ensures clear causality: this change caused this score delta
- Multi-file mutations make it impossible to attribute improvements

---

## Key Rules

### One Change Per Iteration

Atomicity is non-negotiable. If you change two things and the score improves, you do not know which change helped. If you change two things and the score drops, you do not know which change hurt (or if one helped and the other hurt more).

### Mechanical Verification Only

Metrics, not opinions. Agents will game any subjective scale you give them. Use:

- Test pass rates
- Latency measurements
- Coverage percentages
- Bundle sizes
- Error rates

Do NOT use: "rate the quality of this output on a scale of 1-10."

### Git as Memory

```
experiment: try shorter system prompt (score: 65% -> 71%)
experiment: add few-shot examples (score: 71% -> 68%) [REVERTED]
experiment: change temperature to 0.3 (score: 71% -> 74%)
```

- Every mutation gets an `experiment:` commit
- Successful experiments are kept
- Failed experiments are reverted via `git revert`
- The git history IS the experiment log

### Guard Mechanism

Every evaluation has two checks:

1. **Verify** -- Did the target metric improve?
2. **Guard** -- Did anything else break?

An improvement that breaks something else is not an improvement. Both checks must pass to keep the change.

### 3-6 Binary Assertions

The scoring rubric should have between 3 and 6 binary (pass/fail) assertions:

- **Fewer than 3:** Too many loopholes. The agent finds degenerate solutions that technically pass but are useless.
- **More than 6:** Checklist gaming. The agent optimizes for checking boxes rather than genuine quality improvement.

The sweet spot is 4-5 assertions that cover the essential quality dimensions.

---

## Autoresearch Cycle (Linear)

```
  +---> Read current artifact
  |         |
  |     Mutate ONE thing
  |         |
  |     Run eval script
  |         |
  |     Score improved?
  |      /        \
  |   YES          NO
  |    |            |
  |  Keep        Revert
  |  (commit)    (git revert)
  |    |            |
  +----+------------+
```

### Practical Cost

- Per cycle: ~$0.10 (one read + one mutation + one eval)
- Overnight run (50-100 experiments): $5-25
- Typical improvement: measurable gains within 20-30 iterations

---

## HyperAgent Upgrade Path

The linear autoresearch cycle is Level 1. The HyperAgents paper [2603.19461] describes three additional levels of sophistication:

### Level 1 to Level 2: Branching Version Graph

Instead of linear keep/discard, maintain a **tree of experiments** with `select_next_parent`.

- Multiple experimental branches can be explored in parallel
- After N experiments, select the best-performing branch as the new parent
- Allows exploring fundamentally different approaches simultaneously

**When to upgrade:** Linear search plateaus (the same region of the solution space keeps being explored).

### Level 2 to Level 3: Meta-Optimization

The mutation strategy itself evolves.

- Every ~20 iterations, analyze which *types* of changes produced improvements
- Update the search strategy based on what worked
- Example: if "adding examples" consistently improves scores but "shortening" does not, bias future mutations toward adding examples

**Metric:** imp@50 (improvement after 50 iterations). Research shows 0 to 0.63 improvement over ~200 iterations.

**When to upgrade:** You have enough experiment history to detect patterns in what works.

### Level 3 to Level 4: Multi-Task Transfer

When optimizing multiple artifacts in parallel, successful patterns transfer between tasks.

- "Persistent memory helps" discovered in Task A gets tried in Task B
- A shared meta-agent tracks cross-task improvement patterns
- Emergent: agents without explicit instructions begin creating persistent memory, performance tracking, and custom tools -- "context as infrastructure" invented automatically

**When to upgrade:** You are running autoresearch on 3+ artifacts simultaneously and see recurring improvement patterns.

---

## Execution Infrastructure: Contree

For Level 2+ autoresearch, the Contree microVM platform provides native support for version graphs:

| Concept | Contree Implementation |
|---|---|
| Immutable snapshot | `result_image` UUID |
| Save a branch | `disposable=false` |
| Parallel exploration | `wait=false` x N |
| Mark best parent | `set_tag` |
| Rollback | Zero-cost (just switch to a different snapshot) |

Key properties:
- Full isolation between experimental branches
- 3-5 mutations can run in parallel
- Self-modifying code executes in a sandbox, not on the host
- Zero-cost rollback (snapshots are immutable)

---

## Relationship to Other Principles

| Principle | Relationship |
|---|---|
| **Proof Loop (02)** | Proof Loop *verifies* (pass/fail on acceptance criteria). Autoresearch *optimizes* (iteratively improves a score). Best combo: autoresearch for optimization, then proof loop for final sign-off. |
| **Harness Design (01)** | Autoresearch is an automated Generator-Evaluator without manual review. The eval script IS the evaluator. |
| **Deterministic Orchestration (04)** | The eval scripts, git operations, and score comparisons are deterministic -- they should run as shell commands, not through the LLM. |
| **Codified Context (07)** | The experiment log (git history) and scoring artifacts are codified context for future optimization runs. |

---

## When to Apply

**Good fit:**
- Improving skills/prompts with a measurable pass rate
- Optimizing code against a metric (coverage, latency, bundle size)
- Tuning configurations with observable outcomes
- Any "make this better" task where "better" is numerically defined

**Do not apply:**
- Subjective tasks without scriptable evaluation
- Tasks where the scoring rubric is ambiguous or contested
- One-off tasks that will not be repeated (the overhead is not justified)
- Tasks where the search space is so small that manual tuning is faster

---

## Scope Limitations (SICA v2 Findings)

**Source:** [A Self-Improving Coding Agent v2, arxiv 2504.15228](https://arxiv.org/abs/2504.15228)

SICA demonstrated autoresearch at its extreme: an agent modifying its own Python codebase across ~14 improvement iterations, lifting SWE-Bench Verified from 17% to 53% without gradient training. The v2 update adds experiments on reasoning-heavy benchmarks (AIME, GPQA) that expose where autoresearch plateaus. Three failure modes are now documented:

### Failure Mode 1: Base model saturation

On AIME and GPQA, autoresearch barely moves the needle because the base model (o3-mini) is already near-optimal. Autoresearch refines scaffolding and tooling; it cannot push past what the underlying model fundamentally can do. When your metric is bottlenecked by raw model capability, autoresearch will grind without progress.

**Signal to stop:** Three consecutive iterations with no metric improvement. Do not assume the next mutation will break through.

### Failure Mode 2: Reasoning interruption

When the agent delegates reasoning to a strong sub-model, its own scaffolding often **interrupts the reasoning chain** with orchestration overhead. The paper calls this "crude reasoning-inducing components." Practically: if your autoresearch target is a system that wraps a reasoning model, you may be making things worse by adding more orchestration layers. The base model's chain-of-thought is more fragile than the autoresearch loop assumes.

**Signal to watch:** If your autoresearch target involves delegating to a reasoning model, benchmark the model alone (no scaffolding) as a baseline. If scaffolding is below that baseline, strip it - do not optimize it.

### Failure Mode 3: Path dependency and ideation difficulty

Early bad mutations anchor later ones. The agent's "ideation difficulty" means it tends to refine existing directions rather than propose genuinely new approaches. If the first few iterations head down a dead end, the later iterations refine the dead end rather than escape it.

**Mitigation:** Run multiple autoresearch branches from the same starting point with different seed mutations. Keep the best trajectory. This is the HyperAgent version-graph approach - which is why we added it to this principle.

### Revised scope guidance

Autoresearch works well when:
- **Task structure is stable** - the success signal does not change across iterations
- **Base model has headroom** - the metric is not already saturated
- **Architecture aligns with task** - coding tasks benefit from tool/code refinement; pure reasoning tasks do not

Autoresearch fails when:
- You are optimizing a system that wraps a strong reasoning model (the scaffolding interferes)
- The metric is already at or near the base model's ceiling
- The search space has ideation difficulty (rare successful paths the agent will not propose)

The 17 -> 53% jump is real, but it is **task-specific** (coding benchmarks with clear success signals, model with headroom, architecture aligned with task). Do not extrapolate to "autoresearch will improve anything measurable."
