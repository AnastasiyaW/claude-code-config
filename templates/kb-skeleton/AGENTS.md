# AGENTS.md -- entry point for coding agents

> Read this file first. It points at the sources of truth for writing
> code that matches this repo. Keep it under 150 lines so it fits in a
> cached prompt prefix.

## What this project is

<!-- TODO: one paragraph. What is the product, who uses it, what is the
current phase. -->

## Quick commands

<!-- TODO: the ~5 commands you run daily. pytest / ruff / mypy / build /
deploy / lint. -->

```bash
# Example:
# pytest                          # run all tests
# ruff check .                    # lint
# python -m <package>             # run local
```

## Source-of-truth docs

| Topic | File |
|-------|------|
| High-level architecture | `docs/ARCHITECTURE.md` |
| Operations runbook | `docs/OPERATIONS.md` |
| **Hard rules that MUST hold** | `docs/kb/INVARIANTS.md` |
| **Coding conventions / idioms** | `docs/kb/conventions.md` |
| **Recipes for common tasks** | `docs/kb/patterns.md` |
| **Known foot-guns** | `docs/kb/gotchas.md` |
| **Why we chose what we chose** | `docs/kb/decisions.md` |
| **Per-module API contract** | `docs/kb/modules/*.md` |

Minimum reading when you are about to write code:
`INVARIANTS.md` + `conventions.md` + the `modules/<area>.md` that
covers the files you touch.

## Hard boundaries (no-go zones)

<!-- TODO: list places the agent MUST NOT touch. -->

- `.env`, `.env.*`, `*.env`, `secrets/` -- gitignored, never commit.
- <your-sensitive-path>/ -- reason.

## Writing code -- short version

1. **Find the nearest kb page.** `docs/kb/modules/` has per-area rules.
2. **Read the file you are editing entirely.**
3. **Check `INVARIANTS.md`** for any rule that applies. Violation =
   either the code or the invariant must change, and invariants change
   only via explicit proposal in `decisions.md`.
4. **Run regression tests** before claiming completion. Tests carry
   docstrings naming the finding they lock in.
5. **Write a regression test for any new convention** you establish.

## Review workflow

<!-- TODO: if you use agent-based code review (see principle 21), list
your review templates here. Otherwise delete this section. -->

## Multi-agent collaboration

<!-- TODO: if multiple Claude sessions / Codex / teammates push here,
describe the handoff convention. Common pattern:
docs/handoffs/YYYY-MM-DD-from-<name>.md -->

## Asking "should I X or Y?"

1. Check `decisions.md` -- the question may already have a documented
   answer.
2. Check `conventions.md` -- there may be an idiom that resolves it.
3. Ask the human.
4. If still unblocked, pick the option that is easier to revert;
   document your choice at the top of the commit.
