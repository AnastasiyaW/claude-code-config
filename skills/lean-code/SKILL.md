---
name: lean-code
description: On-demand minimalism intensifier — write the leanest correct code, kill over-engineering before it starts. Use when the user says "be lazy / yagni / simplest / minimal / shortest / don't over-engineer", complains about bloat / boilerplate / unnecessary dependencies / abstraction, or before writing a substantial chunk of new code. Supports intensity: lite / full / ultra. Pairs with the always-on quality-code rule and the over-engineering-advisor hook. Do NOT use as a general code-review or bug-hunting pass — it only strips over-engineering and won't catch correctness defects; use /code-review or /review for those.
---

# Lean Code

Aggressive YAGNI mode, on demand. The always-on baseline is `rules/quality-code.md`; this skill is the **intensifier** you invoke when minimalism matters most. The win is measured ("smallest solution that FULLY satisfies the task"), not a slogan.

## The ladder — stop at the first rung that holds
1. **Does this need to exist at all?** Speculative need → skip it, say so in one line. (YAGNI)
2. **Stdlib does it?** Use it.
3. **Native platform feature covers it?** (`<input type="date">` over a picker lib, CSS over JS, a DB constraint over app code.)
4. **An already-installed dependency solves it?** Use it. Never add a new dependency for what a few lines do.
5. **Can it be one line?** Make it one line.
6. **Only then** — the minimum code that works.

The ladder is a reflex, not a research project: two rungs hold → take the higher one and move on.

## Intensity
- **lite** — build what's asked, but name the leaner alternative in one line; user picks.
- **full** — the ladder enforced; stdlib/native first; shortest working diff. (Default.)
- **ultra** — YAGNI extremist: ship the one-liner and challenge the rest of the requirement in the same breath.

## When NOT to be lean (load-bearing — never simplify these away)
Input validation at trust boundaries · error handling that prevents data loss · security · accessibility · the calibration real hardware needs · anything the user explicitly asked to keep. **Lean ≠ incomplete:** non-trivial logic leaves ONE runnable check behind (assert-demo or one small test). User insists on the full version → build it, no re-arguing.

## Hard boundary — lean targets OVER-building, never completeness
This is orthogonal to thoroughness. "Minimal" means *less code per branch*, NOT *fewer branches done* or *cutting corners with a hack*. It must never be an excuse to under-deliver, skip verification, or leave a required branch — see `rules/finish-the-task.md` (its completeness + quality pillars win) and `rules/quality-code.md` (the no-monkey-patch pole). Mark a deliberate shortcut with a `simplification:` comment naming the ceiling + upgrade path.

## Output
Code first. Then at most three short lines: what was skipped, when to add it. If the explanation is longer than the code, delete the explanation. Read the surrounding code / requirements before pruning — prune to the task, not to a blanket rule.

## Why this works (evidence, not marketing)
AI agents measurably over-produce code (GitClear's 211M-line study: duplication up, refactoring down; Faros: +98% PRs, +91% review time, no velocity gain) — a "do I even need this?" constraint addresses a real, measured problem. But always-on minimalism is non-monotonic (arXiv 2601.22025, "When better prompts hurt": a blanket conciseness wrapper can drop accuracy/completeness), which is exactly why this is an **on-demand skill + an advisory hook**, never a hard gate. Success metric = rewrite/churn rate, not raw lines removed.
