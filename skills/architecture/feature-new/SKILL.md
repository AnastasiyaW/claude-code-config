---
name: feature-new
description: >
  Scaffold a new feature narrative document in an existing layer
  following the ULTRAPACK-style template extended for feature-layer
  architecture (principle 28). Creates docs/layers/<layer>/features/feat-NNN-<slug>.md
  with Design / Plan / Verify / Conclusion sections, populates layer
  README features table, and adds entry to feature_list.json if
  present. Use when: "create a new feature", "start work on feature",
  "scaffold feature doc", "/feature-new", "new feature in <layer>",
  "begin feature narrative". Auto-allocates next F-NNN ID.
user-invocable: true
model: sonnet
---

# /feature-new -- scaffold a feature narrative

Creates a feature document in an existing layer. The document follows
the ULTRAPACK-style narrative template (Design / Plan / Verify /
Conclusion) extended with explicit cross-references to layer
invariants and global principles.

## When to use

- Beginning design work on a new feature, **before** writing code
- Migrating an in-flight feature from "scattered context" into the
  formal narrative
- Creating a feature placeholder when planning future work that
  another session will pick up

## When NOT to use

- One-line bug fixes that do not need a design phase (just commit)
- Documentation-only changes (those go in handoffs or PR
  descriptions)
- Refactors with no behavioral change (commit message is sufficient)

## Arguments

```
/feature-new <layer> <slug> [--title "..."] [--branch <name>] [--id F-NNN]
```

- `<layer>` -- existing layer name. Must be a directory under
  `docs/layers/`. If missing, suggest `/layer-new <layer>` first.
- `<slug>` -- kebab-case feature identifier without the `F-NNN-`
  prefix. Examples: `api-key-rotation`, `audit-log`,
  `dual-encryption`.
- `--title` -- human-readable feature title. If omitted, derive from
  slug by title-casing.
- `--branch` -- git branch name. If omitted, default to
  `feature/<slug>`.
- `--id` -- override the auto-allocated F-NNN. Use only when
  migrating a pre-existing feature with a known ID. Refuse if the ID
  already exists in this layer.

## Direction (what to do, in order)

### Step 1 -- Verify environment

1. Determine repo root via `git rev-parse --show-toplevel`.
2. Confirm `docs/layers/<layer>/` exists. If not, refuse with a
   suggestion to run `/layer-new <layer>` first.
3. Confirm `docs/layers/<layer>/features/_FEATURE-TEMPLATE.md`
   exists. If not, copy from
   `<claude-code-skills-checkout>/templates/kb-skeleton/docs/layers/_LAYER-TEMPLATE/features/_FEATURE-TEMPLATE.md`.

### Step 2 -- Allocate F-NNN

If `--id` was provided:

- Validate format (`F-\d{3,}`).
- Check that
  `docs/layers/<layer>/features/feat-<NNN>-*.md` does not already
  exist. Refuse if it does.

If `--id` was NOT provided:

- Scan all existing feature files across **all** layers (not just
  this one) for the highest F-NNN already used.
- Allocate the next number, zero-padded to 3 digits (F-001, F-042,
  F-099, F-100, ...).
- Cross-check that the ID is not in use anywhere -- F-NNN is a
  **project-wide** namespace, not per-layer.

### Step 3 -- Validate slug

- Lowercase kebab-case (`[a-z][a-z0-9-]*`).
- Length <= 50 characters.
- Does not start with `f-` or `feat-` (avoid double-prefix).
- The resulting file `feat-<NNN>-<slug>.md` does not already exist.

### Step 4 -- Copy and fill the template

Source: `docs/layers/<layer>/features/_FEATURE-TEMPLATE.md`

Destination: `docs/layers/<layer>/features/feat-<NNN>-<slug>.md`

In the new file, replace placeholders:

| Placeholder | Replacement |
|-------------|-------------|
| `F-NNN: <feature title>` | `F-<NNN>: <title>` |
| `**Layer:** [<layer-name>](../README.md)` | `**Layer:** [<layer>](../README.md)` |
| `**Status:** design` | leave as `design` |
| `**Branch:** feature/<slug>` | use `--branch` value or default |
| `**Started:** YYYY-MM-DD` | today's date |
| `**Owner:** <name>` | infer from git config user.name, or leave placeholder |

Leave Design / Plan / Verify / Conclusion section bodies as template
placeholders -- the user fills these.

### Step 5 -- Update layer README

In `docs/layers/<layer>/README.md`, find the `## Features in this
layer` table. Insert a new row at the bottom (sorted by F-NNN
ascending):

```
| F-<NNN> | <title> | design | YYYY-MM-DD | [feat-<NNN>-<slug>.md](features/feat-<NNN>-<slug>.md) |
```

If the table has only the placeholder rows from the template, replace
them entirely with the real entry.

### Step 6 -- Update feature_list.json (if present)

If `<repo>/feature_list.json` exists at repo root, parse it and
**append** a new feature entry:

```json
{
  "id": "F-<NNN>",
  "name": "<title>",
  "layer": "<layer>",
  "doc": "docs/layers/<layer>/features/feat-<NNN>-<slug>.md",
  "branch": "feature/<slug>",
  "status": "not-started",
  "dependencies": [],
  "evidence": []
}
```

Important encoding rule (per
`~/.claude/rules/api-utf8-posting.md`): write the JSON file with
`json.dump(data, f, ensure_ascii=False, indent=2)` to preserve any
Cyrillic in titles.

Do NOT change existing entries.

If `feature_list.json` does not exist, do not auto-create it -- emit
a hint instead.

### Step 7 -- Confirm and suggest next step

Print a summary:

```
Created: docs/layers/<layer>/features/feat-<NNN>-<slug>.md
Updated: docs/layers/<layer>/README.md (added F-<NNN> to features table)
Updated: feature_list.json (added F-<NNN>, status: not-started)

Suggested next steps:
1. Fill the Design section in feat-<NNN>-<slug>.md
   - Approach (one paragraph)
   - Invariants (IV-1, IV-2, ...)
   - Rejected alternatives
2. When Design is reviewed, change Status: design -> planning and fill Plan
3. Create the git branch: git checkout -b feature/<slug>
```

## Blueprints (files this skill writes from)

- `templates/kb-skeleton/docs/layers/_LAYER-TEMPLATE/features/_FEATURE-TEMPLATE.md` -- the source template

## Status lifecycle

Two parallel state systems exist; you maintain both manually after this
skill creates them. They serve different purposes:

### Doc Status (narrative phase, in feature.md frontmatter)

Tracks where in the ULTRAPACK Design / Plan / Verify / Conclusion
journey the feature is.

```
design --> planning --> executing --> reviewing --> done
                                  \
                                   --> blocked --> executing
```

Six states: `design`, `planning`, `executing`, `reviewing`, `done`,
`blocked`. Transitions are manual edits. Once `done`, the feature doc
is read-only history; further changes go into a superseding feature.

### feature_list.json status (machine state, for tooling)

Tracks the machine-readable state used by build_kb_graph.py and
validate_kb_links.py.

```
not-started --> in-progress --> done
              \
               --> blocked --> in-progress
```

Four states: `not-started`, `in-progress`, `blocked`, `done`. `done` is
**one-way** (no rollback; regression becomes a new feature) per
[principle 27](https://github.com/AnastasiyaW/claude-code-config/blob/main/principles/27-feature-tracking.md).

### Mapping between the two

| Doc Status | feature_list.json status | Notes |
|------------|--------------------------|-------|
| design | not-started | newly created, no plan yet |
| planning | in-progress | plan being written |
| executing | in-progress | code being written |
| reviewing | in-progress | review/verify phase |
| blocked | blocked | identical |
| done | done | identical |

This skill creates the doc with `Status: design` AND the json entry
with `status: "not-started"`. Subsequent transitions are manual --
update both files in lockstep, or use future `/feature-done`,
`/feature-block` skills (not yet implemented).

## Gotchas

- **F-NNN is project-wide.** Even though features live under layers,
  the F-NNN namespace is shared. Two features in different layers
  cannot share an ID. The skill enforces this by scanning all layer
  directories before allocating.
- **Migration of in-flight features.** When migrating an existing
  feature into the new format, pass `--id F-NNN` explicitly so the
  feature retains its prior ID in any links from PROBLEMS.md or
  handoffs. The skill will not auto-detect existing IDs.
- **Cyrillic titles + Windows.** Per global rule
  `api-utf8-posting.md`, when writing the markdown file or
  feature_list.json, always specify `encoding="utf-8"` explicitly to
  avoid mojibake on Windows.
- **Layer README table edit.** The skill performs a text-level edit
  to insert a row into the features table. If the user has heavily
  customized the table (added columns, changed format), the edit may
  fail. Detect by checking for the canonical 5-column header; if
  absent, emit a warning and skip table edit.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Layer does not exist" | `docs/layers/<layer>/` missing | Run `/layer-new <layer>` first |
| F-NNN conflict | Allocator hit a manually-set ID | Pass `--id F-MMM` explicitly with the next free number |
| `feature_list.json` parse error | Invalid JSON in file | Stop, surface the parse error. User fixes manually before retry |
| Template missing on this machine | Different host / fresh clone | Pull from public repo: `gh api repos/AnastasiyaW/claude-code-config/contents/templates/kb-skeleton/docs/layers/_LAYER-TEMPLATE/features/_FEATURE-TEMPLATE.md` |
| Cyrillic in title shows as `?????` | File written without explicit utf-8 | Re-write the file with `encoding="utf-8"`; see `~/.claude/rules/api-utf8-posting.md` |

## Implementation note

This is a **scaffolding** skill: file copy + placeholder replacement +
small JSON merge. Keep it deterministic. The Design / Plan / Verify
sections of the produced document are meant for the user (or the
session that invoked the skill) to fill -- this skill does not
attempt to generate Design content from the title.

Auto-allocating F-NNN requires reading the full tree of
`docs/layers/*/features/feat-*.md` files; do this lazily and cache for
the duration of the skill invocation.
