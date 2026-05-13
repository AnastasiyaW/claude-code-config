# 28 - Feature-Layer Architecture: project knowledge as a navigable tree

## The Problem

Long-running projects accumulate knowledge in three uncoordinated places:

1. **What the code is** -- captured in `docs/kb/` (principle 21) as
   cross-cutting rules, invariants, and per-module contracts.
2. **What we are working on now** -- captured in `feature_list.json`,
   `PROBLEMS.md`, and session handoffs as machine-readable state.
3. **How we got here** -- buried in git log, scattered across chat
   transcripts, and slowly evaporating into nothing.

The middle layer is missing. There is no place where a single feature's
**design rationale, implementation plan, verification evidence, and
post-mortem** live together as one narrative. Without that artifact, a
session six weeks later sees the code, sees the current task list, but
not the **journey** that produced the current shape.

This is the same gap ULTRAPACK addresses with `docs/tasks/<slug>.md`,
but ULTRAPACK is feature-scoped: one file, one feature, no organizing
principle above it. For multi-month projects with cross-cutting
concerns (security, data, UI, infra), feature files multiply and lose
coherence. You need a **layer** above the feature.

## The Paradigm

**Organize project knowledge as a three-tier tree, with hyperlinked
references flowing upward.**

```
Global KB (cross-project)           principles/, alternatives/, rules/
       ^
       | implements
       |
Layer KB (per-project)              docs/layers/<L>/
       ^                                README.md (purpose + linked principles)
       | governs                        kb/ (invariants, decisions, gotchas)
       |                                history.md (evolution timeline)
Feature (per-project)               docs/layers/<L>/features/feat-NNN-*.md
                                        ULTRAPACK-style narrative
                                        (Design / Plan / Verify / Conclusion)
```

A **layer** is a bounded concern: security, data, infrastructure, UI,
domain logic. Layers map to cross-cutting concerns, not file
directories. A single file may participate in multiple layers; a
single layer covers multiple files.

A **feature** belongs to a primary layer (the one whose invariants it
extends or fulfills) and may **touch** secondary layers (links
declared explicitly).

The triangle from [principle 21](21-knowledge-base-enforcement.md) --
fix in code, regression test, invariant entry -- still holds. Layer
documentation **adds** narrative context around the triangle; it does
not replace any vertex.

## Why three tiers (and not one mega-document)

| Concern | Where it lives | Why there |
|---------|---------------|-----------|
| "We chose Generator-Evaluator pattern" | Global KB principle | Reusable across projects |
| "This project encrypts secrets at rest" | Layer KB / security | Project-specific invariant |
| "Why F-042 chose dual-key rotation over single-key" | Feature doc | Decision rationale for one change |
| "Status: in-progress" | feature_list.json | Machine-readable state |
| "Token leaked in build log on 2026-04-12" | PROBLEMS.md | Incident log, not narrative |

Each tier has different change frequency, different audience, and
different lifecycle. Mixing them produces:

- Stale principles that have project-specific paths baked in
- Bloated feature docs that re-state global patterns
- Machine state that drifts from human narrative

## Tier 1: Global KB (this repository's `principles/`, `rules/`, `alternatives/`)

What lives here: knowledge that transfers between projects. Principle
01 (harness design), Principle 02 (proof loop), Rule "safety-secrets",
Alternative "session-handoff" -- these are not specific to any one
codebase.

Referenced from project tiers via **stable URLs** (GitHub raw URLs).
Never via relative path -- the project may move.

## Tier 2: Layer KB (per-project `docs/layers/<L>/`)

A layer is **represented** as a directory under `docs/layers/`, but
conceptually it remains a bounded concern (see line 46) -- the directory is the
storage location, not the definition. Each layer's directory has:

```
docs/layers/<layer-name>/
├── README.md           # Layer overview: purpose, governing principles, feature index
├── kb/                 # Layer-local KB (mirrors docs/kb/ structure but scoped)
│   ├── invariants.md   # Local invariants (IV-1, IV-2 ...)
│   ├── decisions.md    # Layer-scoped ADRs (D-1, D-2 ...)
│   ├── gotchas.md      # Layer-specific pitfalls (G-1, G-2 ...)
│   └── patterns.md     # Recipes scoped to this layer
├── history.md          # Reverse-chronological evolution log
└── features/           # Feature narratives (ULTRAPACK task.md style)
    └── feat-NNN-<slug>.md
```

**Layer README** is the entry point. It must contain:

- One-sentence purpose
- Status (active / deprecated / merging-into-<other>)
- Linked governing principles (Tier 1) and rules
- Local invariants summary (full list in `kb/invariants.md`)
- Features table with status snapshot
- Dependencies on other layers in this project

**Layer history** is reverse-chronological. Each entry is one paragraph
covering: date, feature ID, what changed, why, links to the feature
doc and any ADR generated. This is the **single answer** to "how did
this layer get to its current state?"

## Tier 3: Feature documents (per-project `docs/layers/<L>/features/`)

A feature document follows the ULTRAPACK template, extended with
explicit cross-references to layer and global KB.

```markdown
# F-NNN: <title>

**Layer:** <link to layer README>
**Status:** design | planning | executing | reviewing | done
**Branch:** <git branch>
**Implements invariants:** <links to IV-N in layer kb/invariants.md>
**Touches layers:** <primary>, <secondary>, ...
**Related features:** depends-on / enables / supersedes links

## Design
### Invariants (feature-local)
### Principles (feature-local PC-N)
### Assumptions (AS-N)
### Unknowns (UK-N)
### Rejected alternatives

## Plan
### Files (path:line)
### Interfaces
### Interface graph (Mermaid)
### Phases (PH-1, PH-2 ...) with topological order

## Verify
### Positive cases
### Negative cases
### Evidence (L1 / L2 / L3 with file pointers)

## Conclusion
### Deviations from plan
### Hands-off decisions (if applicable)
### Updated documents
### Future work
```

Feature documents are **closed once done**. They become read-only
history. Updates go into new features that supersede them, with a
link.

## ID system

A single ID space makes cross-tier references compact and unambiguous.

| Prefix | Scope | Format | Example |
|--------|-------|--------|---------|
| `P-NN` | Global principle | `principles/NN-name.md` | P-28 |
| `R-name` | Global rule | `rules/name.md` | R-safety-secrets |
| `A-name` | Global alternative | `alternatives/name.md` | A-session-handoff |
| `L-name` | Project layer | `docs/layers/name/` | L-security |
| `F-NNN` | Project feature (**project-wide namespace**, not per-layer) | `layers/<L>/features/feat-NNN-*.md` | F-042 |
| `IV-N` | Invariant (project or feature-local) | inline | IV-3 |
| `D-N` | Decision (layer-local ADR) | `layers/<L>/kb/decisions.md` | D-7 |
| `G-N` | Gotcha (layer-local) | `layers/<L>/kb/gotchas.md` | G-3 |
| `PT-N` | Pattern (layer-local, reusable recipe) | `layers/<L>/kb/patterns.md` | PT-1 |
| `PC-N` | Principle (feature-local) | inline in feature doc | PC-2 |
| `AS-N` | Assumption (feature-local) | inline in feature doc | AS-1 |
| `UK-N` | Unknown (feature-local) | inline in feature doc | UK-2 |
| `PH-N` | Phase (feature-local) | inline in feature Plan | PH-3 |

Combined references are compact: "F-042 violates IV-2 in L-security
because P-02 requires a fresh-context verifier."

## Hyperlink convention

Three contexts, three link styles:

1. **Within a feature**: anchor links (`#section-name`). Cheap, no
   maintenance burden.
2. **Within the project**: relative paths
   (`../security/features/feat-001.md`). Validated by
   `validate_kb_links.py`. Break if files move; that is a feature, not
   a bug -- breaking forces an update.
3. **Cross-project (to Tier 1)**: GitHub raw URLs. Stable across
   project moves, worktrees, container rebuilds. Cost: requires
   internet for the reader to resolve. Acceptable for documentation;
   not used for code dependencies.

## Promotion: when project knowledge graduates to Global KB

A pattern starts in a feature. If it survives verify and gets reused,
it may earn promotion through these gates:

1. **Feature-local PC-N** -- the principle is named in one feature doc
2. **Layer-local pattern** -- the principle is added to
   `layers/<L>/kb/patterns.md` after appearing in 2+ features
3. **Global principle** -- after appearing in 2+ projects, write a
   `principles/NN-name.md` entry, push to public KB

This is **promotion by usage**, not by intent. Most layer-local
patterns never promote. That is fine.

## What feature_list.json knows vs what feature docs know

`feature_list.json` carries the **machine-readable state**: id,
status, dependencies, evidence file pointers, doc path. It does NOT
carry rationale, invariants, or narrative.

Feature docs carry the **human-readable rationale**: why this design,
what we tried first, what is still unknown. They do NOT duplicate
state -- they reference it.

Both files cite each other:

```json
{
  "id": "F-042",
  "layer": "security",
  "status": "in-progress",
  "doc": "docs/layers/security/features/feat-042-api-key-rotation.md",
  "evidence": [
    ".agent/F-042/L1-ruff.log",
    ".agent/F-042/L2-pytest.log",
    ".agent/F-042/L3-manual-2026-05-12.md"
  ]
}
```

```markdown
**State:** see `feature_list.json#F-042`
```

## Why this works (and when it does not)

### Where this earns its complexity

- Multi-month projects with 5+ active concerns
- Projects with team members across timezones or sessions
- Codebases approaching 50K+ lines where mental model loss is real

### Where this is overkill

- Single-developer pet projects with <5 features
- Prototypes / spike work where scope changes daily
- Short-lived utilities (a shell script, a one-off migration)

For those, `feature_list.json` + `PROBLEMS.md` alone is sufficient.
Adding the layer tree creates documentation that nobody reads.

## Relationship to other principles in this repository

- **[Principle 21 (Knowledge Base Enforcement)](21-knowledge-base-enforcement.md)** -- the triangle of
  fix/test/invariant lives at the layer-KB tier. This principle adds
  the narrative wrapper above it.
- **[Principle 18 (Multi-Session Coordination)](18-multi-session-coordination.md)** -- feature docs are
  append-only per session. Layer history is append-only. Both compose
  cleanly with the lock-vs-handoff distinction.
- **[Principle 07 (Codified Context)](07-codified-context.md)** -- this is JIT context loading
  applied to product knowledge: load only the relevant layer + feature
  doc, not the entire project history.
- **[Principle 11 (Documentation Integrity)](11-documentation-integrity.md)** --
  `validate_kb_links.py` validates cross-tier hyperlinks the same way
  the existing drift validator validates rule references.

## Adoption

1. Copy `templates/kb-skeleton/docs/layers/_LAYER-TEMPLATE/` for each
   bounded concern in the project.
2. Identify 2-3 in-flight features; migrate their narrative into the
   new template.
3. Add `feature_list.json#layer` and `feature_list.json#doc` fields
   for those features.
4. Wire `scripts/build_kb_graph.py` into your CI or pre-commit. It
   generates `docs/_graph/tree.md` (Mermaid) and backlink injection.
5. Wire `validate_kb_links.py` into SessionStart so broken
   cross-references surface before the agent acts on stale paths.

The full skill commands `/layer-new` and `/feature-new` scaffold both
tiers automatically.
