# {PROJECT} — Knowledge Base

Per-project knowledge, co-located with the code (feature-layer architecture, principle 28).
Rendered by the shared `kb-renderer` container (MkDocs Material).

## Map
- **[kb/](kb/)** — cross-cutting project knowledge: invariants, decisions (ADR), gotchas, patterns, conventions.
- **[layers/](layers/)** — bounded concerns (security / data / ui / infra / domain), each with its own KB + feature narratives.

## Conventions
- IDs: `IV-N` invariant · `D-N` decision · `G-N` gotcha · `PT-N` pattern · `F-NNN` feature.
- Decisions are append-only ADRs; an invariant changes only via a new decision.
- Keep entries dense and runnable — code/configs/gotchas, not tutorials.
