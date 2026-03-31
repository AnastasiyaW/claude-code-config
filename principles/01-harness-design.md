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
