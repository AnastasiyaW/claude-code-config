# 24 - Merge Conflict Resolution: Isolated Agents + Verified Data

**Source:** Real incident 2026-04-28 — two parallel Claude sessions editing the same TypeScript monolith concurrently. Codifies what worked.

## Overview

When merge conflicts arise — `git merge`, `rebase`, `cherry-pick`, manual sync with deployed code, or a race condition with a parallel session — the temptation is to resolve them "by logic": read both sides, pick the one that looks right, move on. This is **guessing dressed as judgment**, and it loses production fixes silently.

**Core principle:** Conflicts are resolved by **isolated agents independently verifying each side against confirmed data**, not by the operator's intuition. A second agent in fresh context independently audits the proposed resolution. Errors are checked in parallel as resolutions are produced. If errors emerge, the resolution is wrong even if both agents agreed.

This is the [Proof Loop](02-proof-loop.md) and [Generator-Evaluator](01-harness-design.md) patterns specialized to a high-stakes, low-context decision: which version of these N lines belongs in the final code?

## When to apply

- **Git merge conflict** on any file — even a single line can be a semantic conflict where both syntactic resolutions compile but one breaks runtime behavior
- **Race with a parallel session** — another agent or human edited the same file concurrently
- **Sync local ← deployed** — production has diverged ahead of git (hot-fixes, manual edits)
- **Rebase / cherry-pick conflicts** during backporting
- **Auto-merge tool resolved** something — **do not trust blindly**, verify even auto-resolved hunks (the tool sees syntax, not semantics)
- **Config conflicts** (env vars contradict): isolated agent reads each config + matches against deployed reality
- **Schema conflicts** (DB migration A vs B): agent reads applied migrations on prod = ground truth
- **Doc conflicts** (CLAUDE.md vs project rules): agent reads recent activity → which rule was actually followed

## Anti-patterns

- "I'll take my side, mine is fresher" — may erase a production fix the parallel session deployed
- "I'll take HEAD, master is ground truth" — master can be behind production if hot-fixes bypass git
- "Auto-merge tool already resolved this hunk, probably correct" — the tool sees text, not behavior
- "I read the conflict markers, understood the difference, picked the better one" — without verifying data, this is guessing
- "Merge fast, fix later if anything breaks" — fixing on master is an order of magnitude more expensive than verifying before merge

## The protocol

### 1. Pause before resolving

When you see conflict markers, do not immediately edit them. The first reflex should be to gather evidence, not to choose.

### 2. Spawn isolated agents

Each agent gets:
- The conflicting hunk(s) with both sides clearly labeled
- Surrounding context (the full file, not just the diff)
- `git log -p` on the affected lines to see how each side evolved
- Test files / probes / live behavior data that confirm current expectations
- The deployed production version if available (it is the strongest ground truth)

Crucially, isolated means **fresh context** — the agent does not see your reasoning or the operator's prior assumptions. This avoids confirmation bias.

### 3. Independent verification of each side

The agent's job is not to pick a side but to **understand what each side intends to do**. For each side:

- What behavior does this code produce?
- What test or live probe confirms that behavior?
- When was this added, and by whom?
- Is there a deployed version that matches one side?

Verified data sources, in descending order of authority:
1. **Live verify command output** (executable spec, just-now)
2. **Production deployment artifact** (running code, recent)
3. **Test run output** (post-conflict test results on each side)
4. **Git blame / log** (intent of each change)
5. **Code itself** (intent inferred from surrounding code)
6. **Documentation** (may be stale)

### 4. Synthesize, do not just choose

The best resolution is rarely "take side A wholesale" — it is often a synthesis that preserves both intents:

- If A added a defensive null check and B refactored the call site: keep both — the new call site with the null check
- If A renamed a variable and B added a new use of the old name: rename B's usage to match A
- If A and B both edited an error message: combine the more informative parts of each

Synthesis requires understanding why each change was made — which is why the verification step precedes the resolution step.

### 5. Independent verification of the resolution

A second agent in fresh context receives:
- The proposed resolution (only — not the reasoning that produced it)
- The same context that informed the first agent

It answers:
1. Is this syntactically valid?
2. Does it preserve A's semantic intent?
3. Does it preserve B's semantic intent?
4. Does it pass error checks (build, lint, tests)?

If the verifier disagrees, a third agent reads both reasonings and renders a verdict. Disagreement is a signal that the conflict was non-trivial and needs more data, not that one of the agents is wrong.

### 6. Parallel error checking

While agents are working, run continuously:

- `bun build` / `tsc --noEmit` / equivalent — syntax + types
- Project-specific linter (e.g. a regex hook for the class-of-bug pattern that triggered the conflict)
- Smoke test endpoint / unit tests — runtime behavior
- `git diff` post-resolution on uninvolved hunks — no accidental changes outside conflict areas

If errors appear, the resolution is wrong **even if both agents agreed**. Errors are ground truth; agent agreement is just consensus.

## Real-world case: the parallel-session sync

Two Claude sessions, two operators, one TypeScript file (a long-running monolith mid-refactor at ~6800 lines). Session A was extracting modules to a `lib/` directory; Session B was adding a new dashboard tab with extended endpoint code in a sibling file.

When Session A pulled the deployed version to sync local with production:

1. **Auto-merge tool resolved 8 conflicts** between successive reads (the IDE was applying its own merge logic)
2. **The operator did not trust this** — verified `grep -cE '^(<{7}|>{7}|={7}\s*$)'` returned `0` confirming no markers remained, and read each auto-resolved hunk
3. **For each ambiguous hunk**: read the deployed version (which had been redeployed by Session B, so it was newer than local), read Session B's diff (which added several new helper functions), confirmed which version of each call site was correct
4. **Cross-check via build** after merge — exit 0
5. **Smoke test the production endpoints** — both expected response shapes confirmed live

Without this protocol, Session A could have overwritten Session B's tab additions wholesale by taking its own side ("my refactor is fresher"). With the protocol, both sessions' work merged into a single PR with no lost code.

The PR also added a pre-commit linter that prevents the class-of-bug that caused the conflict in the first place — a virtuous loop where each conflict produces a structural defense against the next one.

## Mechanical enforcement (suggested)

A post-merge hook can:
1. Detect if the merge commit had conflicts (multiple parents + conflict markers were present in any file during merge)
2. Remind: "Verified via spawn isolated agents? Run smoke tests?"
3. Block push if any conflict markers remain in the working tree

Linters and build steps in CI catch syntactic regressions; the harder problem is semantic regressions where both versions compile but one is wrong. For that, the protocol — agents + verified data — is the only durable solution.

## Connection to other principles

- [No-Guessing Rule](../CLAUDE.md) — every resolution decision must be backed by verified data
- [02-proof-loop.md](02-proof-loop.md) — verifier in fresh context = independent audit
- [01-harness-design.md](01-harness-design.md) — generator-evaluator pattern applied at hunk granularity
- [11-documentation-integrity.md](11-documentation-integrity.md) — when documentation conflicts with code, code (verified live) wins

## Summary checklist

Before merging anything with conflicts:

- [ ] Auto-merge resolutions are read and verified (not blindly trusted)
- [ ] Each side's intent is understood via git log / blame / tests / prod
- [ ] Resolution synthesizes both intents rather than choosing one
- [ ] Second agent in fresh context independently verified the resolution
- [ ] Build / lint / smoke test pass post-resolution
- [ ] No conflict markers remain (`grep -cE '^(<{7}|>{7}|={7}\s*$)'` returns 0)
- [ ] No accidental changes outside conflict areas (`git diff` reviewed)

If any box is unchecked, the merge is premature.
