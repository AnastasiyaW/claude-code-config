# Long-Run Project Harness — Templates

Three artifacts that together form the standard harness for any project where work spans multiple sessions (typically >5 sessions, >5 features).

## The three artifacts

| File | Question it answers |
|---|---|
| `init.sh` | Is the project **healthy right now**? (binary check, <3 min) |
| `feature_list.json` | What **features** exist and what state are they in? (machine-readable) |
| `PROBLEMS.md` | What is **broken right now** and how was it fixed before? (incident log, not in this template — see `rules/long-run-problems-log.md`) |

These complement the existing per-project layers:

- **CLAUDE.md** — agent instructions ("how to work here")
- **`.claude/handoffs/`** — tactical session-to-session continuity ("what to do next")
- **`.claude/chronicles/`** — strategic project history ("how we got here")

`feature_list.json` and `init.sh` are the layer that was missing: machine-readable scope + binary health check.

## Files in this template

- `feature_list.schema.json` — JSON Schema for the feature list (drop-in)
- `feature_list.template.json` — example showing all 4 statuses (`not-started`, `in-progress`, `blocked`, `done`)
- `init.sh.template` — bash skeleton with commented-out language-specific sections
- `README.md` — this file

## How to bootstrap a project

For a **new** long-run project:

```bash
# From your project root
curl -O https://raw.githubusercontent.com/AnastasiyaW/claude-code-config/main/templates/long-run-project/feature_list.schema.json
cp /path/to/this/template/feature_list.template.json ./feature_list.json
cp /path/to/this/template/init.sh.template ./init.sh
chmod +x ./init.sh

# Edit feature_list.json — replace examples with your real features
# Edit init.sh — uncomment language sections, fill in actual commands
./init.sh  # Should exit 0
```

For an **existing** long-run project that already has handoffs and chronicle:

1. Read last 5-10 handoff files + chronicle entries
2. Extract list of completed features → `status: "done"` with evidence pointing to commits
3. Identify currently-active work → exactly **one** with `status: "in-progress"`
4. Identify planned work → `status: "not-started"` with dependencies
5. Identify blocked work → `status: "blocked"` with reason in evidence
6. Commit both files in one changeset: `harness: bootstrap feature_list + init.sh`

## Status transitions

```
not-started  →  in-progress  →  done
                  ↓               ↑
                blocked  →────────┘  (after unblock)
```

**Rules**:

- `not-started → in-progress` allowed only if all `dependencies` are `done` AND no other feature is `in-progress` (WIP=1 invariant)
- `in-progress → done` requires `evidence` populated with L1 + L2 + L3 artifacts
- `done → anything else` is **forbidden**. If a done feature regresses, create a new feature `feat-NNN` "fix regression in feat-MMM"

## What goes in `evidence` (status='done')

References to **durable artifacts** at three validation layers:

- **L1 (Syntax / Static)**: lint passed, types valid — output of `tsc --noEmit`, `ruff check`, `cargo clippy`
- **L2 (Runtime)**: tests passed, app started — test runner output file, log capture
- **L3 (System / E2E)**: integration verified — screenshot, curl response log, user flow video

Example:

```
L1: tsc clean (commit a3f2c1) + ruff check passed
L2: pytest tests/test_auth.py 12/12 passed (.agent/evidence/test-output-2026-05-10.txt)
L3: manual login + reset flow in staging (.agent/evidence/auth-flow.png)
```

**Not acceptable** as evidence:

- "Works for me" / "Looks good"
- "I tested it" without a file path or command output
- Reference to a chat — chats disappear, artifacts persist

## When to skip this template

- Short-term projects (<5 sessions of work)
- Projects with <5 distinct features
- Research / exploratory work where scope is fluid
- One-off scripts and utilities

For these, free-form notes in handoffs are fine.

## Source and license

Templates adapted from [walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering) (MIT license), specifically `skills/harness-creator/templates/`. See `principles/27-feature-tracking.md` for the full framework integration into our stack.

## Related

- `principles/27-feature-tracking.md` — full framework explanation
- `principles/02-proof-loop.md` — verification approach (Anti-Fabrication)
- `principles/16-project-chronicles.md` — strategic project history
- `rules/long-run-problems-log.md` — companion PROBLEMS.md convention (in the rules/ folder, not here)
