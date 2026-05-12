# Scoring Rubric

The five-subsystem audit produces a score from 1 to 5 in each dimension. The numbers are anchored — they are not vibes.

---

## The Five Levels

### 5 — Exemplary

- All hard checks pass
- Most soft checks pass
- Convention is **documented** (it exists in writing, not just in someone's head)
- Convention is **consistently followed** (sample 3 recent artifacts and the convention is visible)
- **Mechanical enforcement** present where applicable (hooks, scripts, schemas)

A 5/5 subsystem is one the user would point to as a model for other projects.

### 4 — Good, mostly complete

- All hard checks pass
- Some soft checks pass
- Convention is mostly documented but with one or two gaps
- Sampled artifacts follow the convention 80%+ of the time
- Some mechanical enforcement present but not comprehensive

A 4/5 subsystem is functional and unlikely to be the bottleneck. Improvement is polish, not foundation.

### 3 — Adequate, covers basics

- Hard checks split: half pass, half fail
- Soft checks mostly miss
- Convention exists but is informal (no document, just behavior)
- Sampled artifacts inconsistent
- No mechanical enforcement

A 3/5 subsystem works but degrades over time and across handoffs. Adding structure here gives real returns.

### 2 — Weak, incomplete

- Most hard checks fail
- Soft checks irrelevant (the foundation isn't there)
- Convention only exists by accident (one person did it once)
- Sampled artifacts show it usually doesn't happen
- No enforcement

A 2/5 subsystem is a leak: every session has to rebuild it. This is almost certainly the bottleneck.

### 1 — Missing or actively harmful

- No hard checks pass
- The subsystem is structurally absent
- OR: the subsystem exists but is **actively wrong** (e.g., CLAUDE.md contains contradictory rules; init.sh runs `rm -rf node_modules` unconditionally)

A 1/5 subsystem must be fixed before any work in adjacent subsystems pays back.

---

## How to Pick Between Adjacent Scores

The hard part of scoring is 3 vs 4, or 4 vs 5. Use these tiebreakers, in order:

### 1. Documented vs Behavioral

- If the convention is **only** behavioral ("we usually do X"), cap at 3.
- If documented but not consistently followed: cap at 4.
- Both documented AND followed: eligible for 5.

### 2. Mechanical Enforcement

- No enforcement at all: cap at 3.
- Soft enforcement (rule says "should"): cap at 4.
- Hard enforcement (hook blocks Stop, schema validates, CI fails): eligible for 5.

### 3. Sample 3 Recent Artifacts

Pick 3 recent files in the subsystem's domain (handoffs, problems entries, feature_list updates, commits). Ask: does each follow the convention?

- 3/3 follow: eligible for 5
- 2/3 follow: cap at 4
- 1/3 or 0/3: cap at 3

This is the most reliable tiebreaker. Documentation can lie about reality; sampling can't.

---

## Common Pitfalls

### Don't grade-inflate

The point of the rubric is signal. If every subsystem scores 4-5 by default, the user gets no actionable information. When in doubt, score lower. The user can correct ("actually we do X very well") and the conversation will be more productive than starting from "everything is fine."

### Don't grade-deflate

Conversely, don't score 1 when 2 fits. 1 is reserved for "structurally missing" or "actively harmful". A project with weak handoffs but no PROBLEMS.md is a 2, not a 1.

### Don't double-count

If `init.sh` is missing, that's a Verification problem (3/5 instead of 4/5). It's not also a Lifecycle problem (Lifecycle is about hooks and session boundaries, not about whether init.sh exists). Don't penalize the same gap twice.

### Don't reward intent

"They were going to add PROBLEMS.md" is not 3/5. It's 2/5 until the file exists with content. Scoring rewards what's present, not what's planned.

---

## Calibration Examples

### Example 1: Fresh prototype repo

- 1 CLAUDE.md file (50 lines, mostly project description)
- 1 test file
- No .claude/ directory
- Some recent commits

Scoring:

- Instructions: 2 (CLAUDE.md exists but is description, not guidance)
- State: 1 (no handoffs, no PROBLEMS.md, no feature_list)
- Verification: 2 (tests exist but no init.sh, no doc on validation gate)
- Scope: 2 (no scope rules, recent commits show drift)
- Lifecycle: 1 (no hooks, no settings.json)

Total: 8/25. Bottleneck: State (1/5) or Lifecycle (1/5) — tiebreaker: State (fixing it unlocks others).

### Example 2: Mature project with old conventions

- CLAUDE.md (400 lines, mostly current)
- `.claude/rules/` with 5 files
- `.claude/handoffs/` with 30 files going back 6 months, INDEX.md current
- No PROBLEMS.md, no feature_list.json
- `init.sh` exists and works (Makefile-based)
- `.claude/settings.json` has SessionStart + Stop hooks
- 3 hooks configured: auto_backup_git, stop-test-gate, remind_handoff

Scoring:

- Instructions: 4 (good CLAUDE.md, modular rules, slightly long)
- State: 3 (rich handoffs but missing PROBLEMS.md and feature_list)
- Verification: 4 (init.sh exists, tests run, 3-layer not explicit but Proof Loop referenced)
- Scope: 4 (no-pre-existing rule present, no WIP=1 yet because no feature_list)
- Lifecycle: 5 (hooks configured, settings.json complete, all hard + most soft)

Total: 20/25. Bottleneck: State (3/5). One concrete weakness in an otherwise mature project — and a fixable one.

### Example 3: Public OSS skill repo

A repo like `claude-code-skills` itself:

- CLAUDE.md, AGENTS.md, principles/, rules/, templates/, hooks/, MAINTENANCE.md
- UPDATES.md changelog
- Skills with their own SKILL.md following a schema
- No `feature_list.json` (this is a knowledge base, not a feature-delivering project)
- No `init.sh` (no build step)

Scoring (adjusted for project type):

- Instructions: 5
- State: 4 (UPDATES.md serves as a chronicle, but no PROBLEMS.md tracking active issues)
- Verification: 3 (validators exist in scripts/ but no init.sh entry point)
- Scope: 4 (no-pre-existing rule, but no WIP=1 since project type doesn't need it)
- Lifecycle: 3 (some hooks but not full lifecycle coverage)

Total: 19/25. Bottleneck: Verification (3/5). The skill repo would benefit from an init.sh that runs all validators in one command.

**Note**: For project types that don't need a subsystem (e.g., a knowledge base doesn't need WIP=1), score based on appropriate-to-type criteria. Don't penalize a knowledge repo for lacking feature delivery infrastructure.
