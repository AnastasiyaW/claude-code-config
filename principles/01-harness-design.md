# 01 - Harness Design: Multi-Agent Architecture Principles

**Source:** Anthropic Engineering -- "Harness design for long-running apps"

## Overview

A harness is the orchestration layer around an AI agent that structures its work, evaluates its output, and manages its context. The core insight: models suffer from self-evaluation bias -- they praise their own work even when quality is mediocre. Separating generation from evaluation is the single most impactful architectural decision.

---

## Generator-Evaluator Pattern (GAN-Inspired)

The foundation of harness design is splitting work into two independent agents:

- **Generator** -- produces the output (code, text, plans, designs)
- **Evaluator** -- judges the output quality with calibrated skepticism

### Why separate agents?

Models consistently rate their own work higher than it deserves. This is not a prompting problem -- it is a structural limitation. The evaluator must be:

1. **Independent context** -- does not share conversation history with the generator
2. **Independent prompt** -- has its own evaluation criteria, not derived from the generation prompt
3. **Calibrated skepticism** -- tuned to catch specific failure modes, not generic "is this good?"

### Calibrating the Evaluator

Use few-shot examples with detailed score breakdowns:

- Show the evaluator examples of "good" and "bad" output
- Include explicit scoring rubrics for each dimension
- Provide examples where superficially-good output has hidden flaws
- The evaluator should be harder to impress than the generator

---

## Sprint Contract Pattern

Before implementation begins, the generator and evaluator must agree on what "done" means.

### The Problem

Without a contract, the generator optimizes for what it thinks is good, and the evaluator judges by different criteria. This creates a frustrating loop where work keeps getting rejected for reasons the generator did not anticipate.

### The Solution

Define **concrete, testable success criteria** before the first line of code:

- NOT: "Build a user dashboard" (abstract user story)
- YES: "Dashboard loads in <2s, shows 5 metrics, handles empty state, passes WCAG AA contrast"

The sprint contract is the bridge between "what the user wants" and "what the code must verify." It should be:

- **Specific** -- no ambiguous terms
- **Testable** -- each criterion can be checked mechanically or by the evaluator
- **Frozen** -- does not change mid-sprint (unlike Anthropic's original pattern, see [Proof Loop](02-proof-loop.md) for the frozen-spec variant)

---

## Escalation via Trace Similarity (SEMAG Extension)

**Source:** [SEMAG: Self-Evolutionary Multi-Agent Code Generation, arxiv 2603.15707](https://arxiv.org/abs/2603.15707)

The vanilla Generator-Evaluator loop assumes a fixed number of iterations or runs until the evaluator is satisfied. SEMAG adds a third signal: **execution trace similarity**. When consecutive attempts produce near-identical runtime behavior (not just near-identical code), the loop has stagnated and should escalate rather than retry.

### The Mechanism

For each generation attempt, capture the **execution trace** - the sequence of runtime states, variable values, or output diffs observed when running the generated code. Compare to the previous trace:

```
rho(t, t-1) = 1 - EditDistance(trace_t, trace_{t-1}) / max(|trace_t|, |trace_{t-1}|)
```

When `rho` exceeds a threshold (SEMAG uses an adaptive `delta_0 = 0.85` decaying with iteration count), the generator is stuck. Two more loops will not help. Escalate.

### Escalation Levels

SEMAG defines three levels, from cheapest to most expensive:

1. **Single-shot regeneration** (cheap) - default Generator-Evaluator loop
2. **Trace-guided debugging** (medium) - pass the failing execution trace to the generator as additional context
3. **Multi-agent discussion-decision** (expensive) - spawn multiple debater agents, each proposes a different approach, aggregate via weighted voting based on historical performance

### Discussion-Decision Phase

When Level 2 stalls, spawn N independent debaters (typically 3-5). Each sees the full history and the current stalled state, then proposes a solution along with their reasoning. Aggregation is NOT majority vote - it is weighted by each debater's historical success rate:

```
weight_j = softmax(eta_j / tau_w)
final = argmax sum(weight_j * proposal_j)
```

This is **orthogonal** to the original Generator-Evaluator pattern - debaters are generators, aggregation is evaluation, but they run in parallel instead of sequentially. Use it when sequential regeneration has demonstrably stopped helping.

### When to Use This

- You have an iterative loop (Generator-Evaluator, autoresearch, or similar)
- You can capture a trace signal (test output, runtime behavior, diff, error messages)
- You are wasting budget on retries that produce near-identical failures
- SEMAG reports a +3.3% improvement on CodeContests with same backbone; the automatic model selector pushes this to 52.6% overall

### What We Explicitly Do NOT Adopt

SEMAG's full Automatic Model Selector (which swaps LLM backbones mid-task based on task complexity) is powerful but task-specific. Without a measurable task-difficulty signal, model switching becomes guesswork. Adopt the escalation mechanism; keep the backbone fixed unless you have independent difficulty measurements.

---

## Context Management

Long-running agent tasks face three context challenges:

### Context Reset vs. Compaction

| Approach | Pros | Cons |
|---|---|---|
| **Compaction** | Preserves continuity, retains nuance | Accumulates noise, may retain outdated assumptions |
| **Context Reset** | Clean slate, eliminates stale context | Loses progress, requires explicit handoff |

**Recommendation:** For long tasks, prefer **context reset with structured handoff artifacts**. Compaction is convenient but does not give you a clean slate when you need one.

### Structured Handoff Artifacts

When resetting context, transfer state through documents rather than relying on conversation history:

- `PLAN.md` -- current plan with completed/remaining items
- `STATE.json` -- machine-readable state (variables, counters, flags)
- `FINDINGS.md` -- discoveries, decisions, gotchas found so far

### Context Anxiety

Models begin to wrap up work prematurely when they estimate the context window is filling up. This manifests as:

- Cutting corners on later steps
- Producing shorter, less detailed output
- Skipping verification steps
- Declaring "done" earlier than warranted

**Mitigation:** Break work into smaller chunks that fit comfortably within the context window. Do not rely on the model to self-manage context usage.

---

## Assumption Testing

Every component of a harness encodes an assumption about what the model cannot do on its own.

### The Principle

- Each guardrail, evaluator, or orchestration step exists because someone believed the model would fail without it
- These assumptions **expire** as models improve
- What required a complex harness 6 months ago may now work with a solo agent

### The Strategy

Periodically **remove components** and measure impact:

1. Disable a guardrail or evaluator
2. Run the same tasks
3. Measure quality difference
4. If quality holds, the component is no longer needed

**Default stance:** Simplest solution first. Add complexity only when measured quality demands it. Do not build a 6-agent harness for a task a solo agent handles reliably.

---

## Quality Criteria

When evaluating output (especially frontend/UI work), use these four dimensions:

| Dimension | What to Check | Red Flags |
|---|---|---|
| **Design Quality** | Coherence as a whole, not sum of parts | Inconsistent spacing, mixed visual languages |
| **Originality** | Distinctive, purposeful choices | Template layouts, library defaults, "AI slop" (purple gradients on white cards) |
| **Craft** | Typographic hierarchy, spacing consistency, color harmony, contrast | Misaligned elements, inconsistent font sizes, poor contrast ratios |
| **Functionality** | User completes their task without guessing | Hidden affordances, ambiguous labels, broken flows |

These criteria apply to evaluator calibration -- they define what "good" means for the scoring rubric.

---

## Cost vs. Quality

Real-world measurements from production harness deployments:

| Setup | Cost | Time | Outcome |
|---|---|---|---|
| Solo agent | ~$9 | 20 min | Broken core functionality, layout issues |
| Full harness (generator + evaluator + coordinator) | ~$200 | 6 hours | Working gameplay, visual polish, AI features |

**The 20x cost produces a qualitative leap, not a linear improvement.**

### When to use each:

- **Solo agent:** Routine tasks within the model's reliable capability range. Simple CRUD, single-file changes, well-defined transformations.
- **Full harness:** Tasks beyond reliable solo performance. Multi-file features, complex UI, anything where "good enough" is not good enough.

The evaluator is justified when the task is at the boundary of -- or beyond -- what a solo agent handles reliably. If the solo agent consistently produces good results, you do not need the harness overhead.

---

## Relationship to Other Principles

- **Proof Loop (02):** Extends the evaluator concept with fresh-session verification and durable artifacts
- **Autoresearch (03):** Automates the Generator-Evaluator loop for iterative optimization
- **Multi-Agent Decomposition (06):** Adds a coordinator role to Generator-Evaluator, creating a three-agent architecture
- **Deterministic Orchestration (04):** Handles the mechanical parts of evaluation (running tests, linting) outside the LLM
