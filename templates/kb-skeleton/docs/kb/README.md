# docs/kb -- Knowledge Base for coding agents

**This directory is context-as-infrastructure.** It is consulted by
Claude (and any other coding agent) at the start of a task, and again
whenever a rule might apply to what they are about to change.

Humans are welcome, but the tone is tuned for agents: dense,
rule-forward, cross-referenced, no marketing.

## What lives where

| File | Purpose | When to consult |
|------|---------|-----------------|
| `INVARIANTS.md` | Hard rules that MUST hold across the codebase | Before writing or reviewing any code |
| `conventions.md` | Code-style idioms (naming, imports, error handling) | When starting a new file or editing idiom-sensitive code |
| `patterns.md` | Recipes for common tasks | When adding functionality of an existing type |
| `gotchas.md` | Known foot-guns + workarounds | When something behaves unexpectedly |
| `decisions.md` | ADR-like log | Before challenging an apparent "weird" choice |
| `modules/*.md` | Per-module API contract + invariants | When touching a specific module |

## How a session uses this

1. First turn of a fresh session: read `AGENTS.md` at repo root.
2. Read `INVARIANTS.md`. Every rule there is load-bearing.
3. When beginning a task, read the `modules/*.md` covering the file(s)
   you will touch.
4. If patterns overlap with a recipe, read `patterns.md`.
5. If you encounter unexpected behavior, `gotchas.md` often has it.
6. If you are about to deviate from a rule, read `decisions.md` first.

## How to update this

**Content rules (what goes in):**

- Only facts that survive the next refactor. Do not document
  implementation details that will obviously drift -- point at the
  relevant file instead.
- Every rule carries a **reason**. Not "we want uniformity" but
  "because review L3 F3 showed X drift when sessions overlap".
- Cross-reference by file path with line numbers where possible.

**Process rules:**

- New rule in `INVARIANTS.md` needs: a unique ID, a statement, a
  reason, and -- ideally -- a regression test that fails when the rule
  is broken.
- New section in `modules/*.md` for a new module: add it, and update
  `AGENTS.md` pointer table.
- Removing a rule: note date + reason in `decisions.md` as an ADR
  "retired rule X because...". Never silently drop an invariant.

**Enforcement:**

- `scripts/validate_kb.py` (pre-commit + CI) checks coverage and
  reference integrity. Stale docs fail the build.

## When NOT to put something here

- Session-ephemeral context -> `docs/handoffs/*.md` instead.
- Runbook / ops -> `docs/OPERATIONS.md`.
- User-facing command behavior -> user docs.
- Historical narrative -> `CHANGELOG.md` or `MIGRATION.md`.

## Meta-rule

When you find yourself repeating an instruction to future-you or to
another agent across sessions -- that instruction belongs here.
