# Layer: <layer-name>

<!-- Replace <layer-name> with the bounded concern: security, data,
infrastructure, ui, domain, observability, etc. Do NOT name layers
after file directories ("src" is not a layer). Name them after the
concern the layer defends ("security", "image-processing"). -->

**Purpose:** <one sentence: what this layer guarantees or makes possible>
**Status:** active

<!-- Status values: active | deprecated | merging-into-<other-layer> -->

## Governing principles

<!-- Tier 1 (Global KB) references. Use stable GitHub raw URLs so the
links survive worktrees, container rebuilds, and project moves. -->

- [P-NN <name>](https://github.com/AnastasiyaW/claude-code-config/blob/main/principles/NN-name.md)
- [R-<rule> <name>](https://github.com/AnastasiyaW/claude-code-config/blob/main/rules/name.md)

## Local invariants summary

<!-- One-line summary per invariant. Full statement + reason + enforced-in
+ test pointers live in kb/invariants.md. Keep this section under 10
lines so the layer README fits a single screen. -->

- **IV-1:** <one-line statement>. See [kb/invariants.md#IV-1](kb/invariants.md#iv-1).
- **IV-2:** <one-line statement>. See [kb/invariants.md#IV-2](kb/invariants.md#iv-2).

## Features in this layer

<!-- Status snapshot. The authoritative state is in feature_list.json.
This table is for human navigation -- regenerate via /feature-new and
/feature-done commands, or by `build_kb_graph.py`. -->

| ID | Title | Status | Last touch | Doc |
|----|-------|--------|------------|-----|
| F-001 | <feature title> | done | 2026-MM-DD | [feat-001-slug.md](features/feat-001-slug.md) |
| F-002 | <feature title> | in-progress | 2026-MM-DD | [feat-002-slug.md](features/feat-002-slug.md) |

## Dependencies on other layers

<!-- Explicit edges in the layer dependency graph. If this layer reads
from or writes to another layer's contract, declare it here. -->

- **<other-layer>**: <one sentence about what we use>. See [layers/<other>/README.md](../<other>/README.md).

## See also

- [history.md](history.md) -- chronological evolution of the layer
- [kb/invariants.md](kb/invariants.md) -- full invariants list with enforcement pointers
- [kb/decisions.md](kb/decisions.md) -- architectural decisions (ADR-style)
- [kb/gotchas.md](kb/gotchas.md) -- known pitfalls and workarounds
- [kb/patterns.md](kb/patterns.md) -- reusable recipes within this layer

<!-- Cross-cutting docs at the project root remain authoritative:
- ../../kb/INVARIANTS.md for invariants that span multiple layers
- ../../kb/decisions.md for project-wide decisions -->
