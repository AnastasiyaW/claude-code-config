# <Layer name> -- Architectural Decisions

Layer-scoped ADR log. Decisions affecting this layer only.
Project-wide decisions remain in `docs/kb/decisions.md`.

Each decision has: a unique ID (`D-N`), context, decision, consequences,
and references to the invariants or features it produces.

## Identity and format

- IDs are stable per layer (`D-1`, `D-2`, ...). Never reuse retired IDs.
- Format follows lightweight ADR: Context / Decision / Consequences.
- Each ADR cites the feature(s) or invariant(s) it produces or retires.

## D-1 -- <short decision name> (YYYY-MM-DD)

**Context:** <what we were trying to do, what alternatives existed, what
constraint forced a choice>.

**Decision:** <what we chose, stated as a positive assertion>.

**Consequences:**

- <good consequence>
- <good consequence>
- <bad consequence or trade-off>

**Implements / produces:** [IV-N](invariants.md#iv-n), F-NNN.

**Supersedes:** <prior decision if any, else "none">.

**Related principle:** [P-NN](https://github.com/AnastasiyaW/claude-code-config/blob/main/principles/NN-name.md).

<!-- Copy the block above per new decision. Order is chronological
top-down within this file. Keep the ID sequence monotonic. -->
