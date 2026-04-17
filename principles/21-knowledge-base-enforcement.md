# 21 - Knowledge Base Enforcement: review findings become durable contracts

## The Problem

Multi-agent and multi-session projects leak knowledge at a predictable rate.
Someone runs a good code review, fixes 25 issues, and ships. Six weeks later
another session opens the repo and re-discovers three of those issues from
scratch. The fix commits are in git, but the *reasoning* - why this
decorator must be present, why this field is SecretStr, why this upsert
can't be SELECT-then-INSERT - has no home.

Documentation mindset says "write an ADR". Reality: ADRs drift, agents
do not read them consistently, and no one fails the build when a rule is
broken.

The gap is structural: review output is an **expensive ephemeral artifact**
(a few hundred dollars of agent time + hours of human synthesis), and most
teams let 80% of its value evaporate into commit messages.

## The Paradigm

**Every accepted review finding has three durable forms, not one.**

1. A **fix** in code (commit).
2. A **regression test** whose docstring names the finding ID
   (`"L2 F1 regression: /start bypasses @require_whitelist"`).
3. An entry in an **INVARIANTS file** that states the rule, names the
   finding that motivates it, and points at both the enforcement location
   in code and the regression test.

Missing any of the three loses guarantee. Missing the invariant loses
the *reason*, which is what future sessions need.

Once this triangle exists, the review artifact becomes a **durable
contract**. Breaking any invariant trips a named test. Reading any file
shows the invariants that govern it. Starting any session lands on the
invariants page before touching code.

## Structure

```
<repo-root>/
├── AGENTS.md                   # AAIF-standard entry, <=150 lines, cached prefix
│   # Lists commands, boundaries, pointers. Claude/Codex/Cursor read this first.
│
├── docs/kb/                    # Knowledge base for agents (not humans)
│   ├── README.md               # Meta-rules: how to use, when to update
│   ├── INVARIANTS.md           # Hard rules (I-1, I-2, ...) -- the heart
│   ├── conventions.md          # Idioms (imports, async, errors, types)
│   ├── patterns.md             # Recipes ("add a new handler", "add a field")
│   ├── gotchas.md              # Known foot-guns with workarounds
│   ├── decisions.md            # ADR-like log (D-1, D-2, ...)
│   └── modules/
│       ├── <area1>.md          # Per-module API + contracts
│       ├── <area2>.md
│       └── ...
│
├── scripts/validate_kb.py      # Pre-commit + CI check
├── .github/workflows/kb.yml    # CI gate
└── review-templates/           # If doing agent-based review rounds
    └── layers/L*.md            # Each layer references invariant IDs + modules/
```

## The Three Forms, Concretely

### Form 1 -- Fix in code

Normal PR. Nothing special here.

### Form 2 -- Regression test with finding ID in docstring

```python
def test_audit_record_takes_factory_not_session() -> None:
    """L3 F3 regression: audit.record() must take a session factory,
    not a session. Otherwise handler commits drift from audit commits.
    """
    sig = inspect.signature(audit.record)
    assert "factory" in sig.parameters
    assert "session" not in sig.parameters
```

Why: when a future session breaks this, pytest output tells them
*exactly* what review found and why it matters. Teaching via failing
test.

### Form 3 -- Invariant with cross-references

```markdown
### I-2 -- Audit rows write in their own session

**Statement:** `audit.record()` takes an `async_sessionmaker`.
Handler transactions and audit writes are independent.

**Reason:** Review L3 F3. Original signature took the decorator's
session and called commit(), which could commit a partial handler
side-effect with an "ok" audit row.

**Enforced in:** `bot/services/audit.py:22-42`.

**Test:** `tests/test_observability.py::test_audit_record_takes_factory_not_session`.
```

Every claim here is link-able. When the file moves, `validate_kb.py`
catches the broken reference.

## Validator

```
scripts/validate_kb.py (stdlib-only, <1s run)

Fails when:
  - bot/<area>/ exists without docs/kb/modules/<area>.md
  - docs/kb/*.md references a path that no longer exists
  - INVARIANTS.md names a test via `path::name` that is missing
  - AGENTS.md points at a kb/*.md that was removed
```

Run in CI via `.github/workflows/kb.yml` on push + PR. Documentation
drift becomes a build failure, not a silent rot.

See [`templates/kb-skeleton/`](../templates/kb-skeleton/) for a
drop-in starter set.

## Review Templates Cross-Link Back

If the project uses agent-based code review (e.g. per-security-layer
agents), each layer template gets a section:

```markdown
## Knowledge base consultation (read first)

* `AGENTS.md` (repo root)
* `docs/kb/INVARIANTS.md` SS **I-N, I-M** -- rules for this layer
* `docs/kb/modules/<area>.md` -- per-module contract
* `docs/kb/decisions.md` SS **D-N** (why we chose X over Y)

If a finding you report contradicts an invariant, the finding must be
stronger than the invariant -- call it out explicitly.
```

This bidirectional link prevents two classes of waste:

1. Agents re-finding issues that are already invariants.
2. Agents inventing interpretations where the repo has a documented
   decision.

## When to Adopt

This pattern costs work. Justified when:

- Project has **multiple agents or sessions** touching the same code
  (two Claude sessions, Claude + Codex, team of humans + agents).
- You just ran a **large review** and want to freeze its findings
  before they decay.
- Scope has **non-obvious invariants** (security, concurrency) that
  one-line code review cannot catch.

Not justified when:

- Solo work on a throwaway script.
- Code base is small enough that reading it end-to-end is cheap.
- The domain is so stable that conventions live in code idioms alone.

## Real-world Numbers

A Phase 2 security sweep on a Python Telegram-bot project:

- **Review round:** 8 independent Opus agents, ~$15 compute, 7 min wallclock.
- **Findings:** 123 (1 Critical, 23 High, 43 Medium).
- **Addressed in this sweep:** 25 findings (all P0 + P1 + P2).
- **Invariants created:** 25 (one per finding, mostly 1:1).
- **Regression tests written:** 65 (some invariants need multiple angle
  tests).
- **KB files:** 1 AGENTS.md + 6 topic files + 5 per-module files = ~2500
  LOC of codified context.
- **Commit footprint:** 5 commits -- review-templates, dockerignore, all
  P1/P2 code + tests, kb content, validator+CI.

Net effect: next reviewer (human or agent) starts from 25 known-guarded
rules instead of re-discovering them. Review-round-2 output drops to
genuinely new findings.

## Related Principles

- [07 - Codified Context](07-codified-context.md) -- the mindset this
  pattern is a concrete implementation of.
- [11 - Documentation Integrity](11-documentation-integrity.md) --
  validator-at-session-start generalization.
- [02 - Proof Loop](02-proof-loop.md) -- regression tests as durable
  proof artifacts for review conclusions.
- [06 - Multi-Agent Decomposition](06-multi-agent-decomposition.md) --
  parallel layer agents is the source of review findings here.

## Drop-in Starter

See [`templates/kb-skeleton/`](../templates/kb-skeleton/) for an empty
structure with placeholder-filled files and a working validate_kb.py.
Copy wholesale, fill in domain-specific invariants as review finds
them. First invariant can be added in <5 minutes.
