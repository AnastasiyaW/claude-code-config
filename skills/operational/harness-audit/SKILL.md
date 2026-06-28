---
name: harness-audit
description: Score a project's agent harness across 5 subsystems (Instructions / State / Verification / Scope / Lifecycle), identify the bottleneck, and produce a prioritized improvement plan. Use when assessing if a project is ready to graduate to [LONG-RUN] status, when an agent keeps failing despite good models, or when adopting our stack on a new codebase. Do NOT use to design or build a new harness from scratch — this only scores an existing one; for greenfield harness/agent architecture use harness-design (or agent-harness-design).
when_to_use: |
  Trigger on phrases like: "audit my harness", "evaluate my agent setup", "score my CLAUDE.md", "is my project ready for long-run", "5-subsystem assessment", "what's missing from my project setup", "/harness-audit". Run proactively when joining an unfamiliar codebase that has agent artifacts (CLAUDE.md, .claude/, AGENTS.md) but obvious gaps. Skip for single-file scripts and pure exploration.
license: MIT
---

# Harness Audit

Score a project's agent harness across five subsystems and tell the user which one to fix first.

**Source**: Five-subsystem framework adapted from [Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/) (walkinglabs, MIT). Adapted to our concrete stack: CLAUDE.md, `.claude/rules/`, PROBLEMS.md, `feature_list.json`, `init.sh`, hooks, handoffs, chronicles.

## What This Skill Does

Given a project directory, produces a scorecard like this:

```
=== Harness Audit: project-xyz ===

Instructions  4/5  ✓ CLAUDE.md present, modular rules in .claude/rules/
                   ✗ No project-level REVIEW.md for PR review guidance
State         2/5  ✓ .claude/handoffs/ exists (3 files)
                   ✗ No PROBLEMS.md - issues scattered in handoffs
                   ✗ No feature_list.json - scope state not machine-readable
Verification  3/5  ✓ Tests run, pytest configured
                   ✗ No init.sh - new sessions take 15+ min to bootstrap
                   ✗ 3-layer gate not documented in CLAUDE.md
Scope         3/5  ✓ no-pre-existing-evasion principle in CLAUDE.md
                   ✗ No WIP=1 (no feature_list.json to enforce it)
                   ✗ Definition of Done not explicit
Lifecycle     2/5  ✗ No SessionStart hook (no .claude/settings.json)
                   ✗ No Stop hook for clean-state check
                   ~ Manual cleanup convention exists but not enforced

Bottleneck: State (2/5) — lack of structured progress tracking

Top 3 improvements (in order):
1. Create PROBLEMS.md (1h)   ↗ State 2→4
   Template: claude-code-skills/templates/long-run-project/ has examples
2. Create feature_list.json + init.sh (30min)   ↗ State 2→5, Verification 3→4
   Drop-in: claude-code-skills/templates/long-run-project/
3. Add Stop hook stop-test-gate.py (15min)   ↗ Lifecycle 2→4
   Source: claude-code-skills/hooks/stop-test-gate.py

After top 3: Instructions 4 + State 5 + Verification 4 + Scope 3 + Lifecycle 4 = 20/25 (was 14/25)
```

The skill does **not** make changes. It produces the scorecard. The user decides whether to apply recommendations.

---

## The Five Subsystems (Our Adaptation)

| Subsystem | Concrete files/conventions in our stack |
|---|---|
| **Instructions** | `CLAUDE.md` (root + `~/.claude/`), `.claude/rules/*.md` (project), `~/.claude/rules/*.md` (global), optional `REVIEW.md` |
| **State** | `PROBLEMS.md`, `feature_list.json`, `.claude/handoffs/`, `.claude/chronicles/` |
| **Verification** | `init.sh`, tests configured, 3-Layer Validation Gate referenced in CLAUDE.md, Proof Loop usage |
| **Scope** | `no-pre-existing-evasion.md` rule applied, WIP=1 enforced (one `in-progress` in feature_list.json), explicit Definition of Done |
| **Lifecycle** | SessionStart hooks, Stop hooks (stop-test-gate, check-problems-md), cleanup convention |

See `references/checklist-per-subsystem.md` for per-subsystem concrete checks.
See `references/scoring-rubric.md` for how to interpret 1-5 scores.

---

## How to Run an Audit

### Phase 1 — Gather

Read these files in order (skip silently if missing):

1. `CLAUDE.md` in project root
2. `AGENTS.md` in project root (some projects use this name)
3. `.claude/rules/*.md` (project-level rules)
4. `.claude/settings.json` and `.claude/settings.local.json` (hooks config)
5. `PROBLEMS.md` in root
6. `feature_list.json` in root
7. `init.sh` in root (and `Makefile` / `package.json` scripts as fallback)
8. `.claude/handoffs/` (count files, check `INDEX.md` existence)
9. `.claude/chronicles/` (count files)
10. Sample test config: `pytest.ini` / `package.json` test script / `Cargo.toml`

Use `Glob` + `Read`. Don't `grep` across entire codebase — this is metadata audit, not code review.

### Phase 2 — Score

For each subsystem, run the checks in `references/checklist-per-subsystem.md`. Each check is a binary pass/fail. Score:

- **5** = all checks pass + documented + consistently followed
- **4** = most checks pass, 1-2 gaps
- **3** = covers basics, missing polish
- **2** = weak, several checks fail
- **1** = missing or actively harmful

For each subsystem, list:
- ✓ what's present and working
- ✗ what's missing or broken
- ~ partial / unclear

### Phase 3 — Identify Bottleneck

The lowest-scoring subsystem is the bottleneck. **Even if other subsystems are weaker by absolute count of checks**, the lowest score is the one to fix first because it limits the value of the rest.

Tie-breaker (multiple subsystems at same low score): pick the one whose improvement *unlocks* progress in others. State usually wins ties because feature_list.json + PROBLEMS.md unlock Verification and Scope checks.

### Phase 4 — Prioritized Improvement Plan

Output exactly 3 next steps in order, each with:
- **Effort** estimate (15min / 30min / 1h / 1d)
- **Subsystem(s)** it improves and by how much (2→4, etc.)
- **Pointer** to a template or example in `claude-code-skills/` if available

The 3 steps must:
1. Address the bottleneck first
2. Each step independently shippable (no item depends on a later one)
3. Together raise the total score by at least 4 points (out of 25)

Do not give more than 3. Three is enough scope for one focused session.

---

## Output Format

Use the visual scorecard format shown at the top of this skill. Sections:

1. **Header**: `=== Harness Audit: <project-name> ===` (one line)
2. **Scorecard**: 5 lines, one per subsystem, with score + ✓/✗ findings
3. **Bottleneck**: one line naming the subsystem and score
4. **Top 3 improvements**: numbered list with effort + impact + pointer
5. **Projected total**: optional, only if user asked for "after" state

Keep the entire output under 50 lines. The user is scanning for next steps, not reading an essay. Detail goes into the per-subsystem checklist file, not the audit output.

---

## What This Skill Is NOT

- **Not a code review** — does not look at source code quality
- **Not a security audit** — does not check for vulnerabilities (use `/security-review` instead)
- **Not a test runner** — does not execute `init.sh` or tests, just checks existence
- **Not a fix tool** — produces recommendations only, user applies them
- **Not for short-term projects** — if the project is <5 features or <5 sessions, the harness overhead is not yet warranted; say so and skip the audit

---

## Honest Tradeoffs

- The 5-subsystem framework is **opinionated**. A project can be perfectly functional with 3 of 5 strong and 2 weak (e.g., a research repo with no lifecycle needs).
- Scoring is **subjective at the margins**. A 3 vs 4 for "covers basics" is a judgment call. Use the checklist to keep it consistent across audits, not to claim numeric precision.
- The skill assumes our stack conventions. For projects using completely different tooling (e.g., AGENTS.md without `.claude/`), translate concepts before scoring — don't fail the project on naming.

---

## Related

- **Principle 27** (feature-tracking) — full framework explanation
- **Principle 01** (harness-design) — Generator-Evaluator pattern, source of "subsystems" thinking
- **Templates** `templates/long-run-project/` — drop-in files for fixing State + Verification gaps
- **Rule** `rules/long-run-harness.md` — convention this audit checks against

---

## Quick Self-Audit (for skill development)

This skill is itself a `[LONG-RUN]`-style artifact. To audit the audit:

- **Instructions**: SKILL.md is this file (✓)
- **State**: Scoring decisions are reproducible from `references/scoring-rubric.md` (✓)
- **Verification**: 5 example evals in `references/example-audits.md` (TODO if added)
- **Scope**: Clear "what this skill is NOT" section (✓)
- **Lifecycle**: No hooks needed — this is a query skill, not a continuous one (N/A)
