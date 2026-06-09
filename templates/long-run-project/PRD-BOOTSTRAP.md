# PRD → feature_list.json bootstrap

Seed a new `[LONG-RUN]` project's `feature_list.json` from a product/requirements
doc (PRD, spec, design layers, or a plain task brief), instead of hand-authoring
the whole list. Adapted from [claude-task-master](https://github.com/eyaltoledano/claude-task-master)'s
`parse_prd` workflow — but our `done` gate stays **evidence/proof-loop**, not a
`testStrategy` string, and we keep the 4-state WIP=1 model.

## When

- New `[LONG-RUN]` project that already has a PRD/spec/design doc.
- Bootstrapping `feature_list.json` for an existing project (see long-run-harness
  skill "Bootstrap" section) — feed recent handoffs/chronicle as the "PRD".

## Procedure

1. **Input.** Point at the PRD: `docs/prd.md`, a design-layers doc, or a brief.
2. **Decompose into features (deliverables, not tasks).** 5–15 features is the sweet
   spot. Each feature = a user-facing capability with a verifiable "done".
3. **Allocate ids** `feat-001…` in dependency order (roughly: foundations first).
4. **Fill dependencies[].** A feature lists the `feat-NNN` ids that must be `done`
   before it can start. This is the DAG — keep it acyclic (validator enforces).
5. **All seeded features start `not-started`.** Do NOT mark anything `in-progress`
   yet (WIP=1: you choose the first one explicitly after bootstrap).
6. **Leave `evidence` empty** until a feature reaches `done`/`blocked` — it is filled
   with L1/L2/L3 artifact references at completion, never speculatively.
7. **Validate:** `python scripts/feature_dag_check.py feature_list.json` — must pass
   (no missing refs, no cycles, WIP≤1). It also prints the READY set (legal first
   features = those with all deps done, i.e. deps-free ones at bootstrap).

## Prompt template (for an agent doing the decomposition)

```
You are bootstrapping feature_list.json from the PRD below.
Output ONLY valid JSON matching feature_list.schema.json.
Rules:
- 5–15 features, each a user-facing DELIVERABLE (not an implementation task).
- ids feat-001.. in rough dependency order.
- dependencies[] = feat-NNN ids that must be done first. Acyclic. Empty if none.
- ALL features status="not-started". evidence="".
- description = what it does in user-facing terms (1 sentence).
Do not invent scope beyond the PRD. If the PRD is thin, list fewer features.

PRD:
<<<
{paste PRD / spec / brief here}
>>>
```

After generation: run `feature_dag_check.py`, fix any FAIL, then pick the first
feature (from the READY set) and set it `in-progress`.

## What we deliberately did NOT copy from task-master

- Its `status` is 3-state (`pending/done/deferred`); ours is 4-state with the
  WIP=1 invariant and a `blocked` state with a named blocker. Keep ours.
- Its done-signal is a `testStrategy` *string*. Ours is `evidence` referencing real
  L1/L2/L3 artifacts (proof-loop). Keep ours — it's stronger.
- We do not vendor its MCP server; the bootstrap is a one-shot decomposition, the
  ongoing source of truth is `feature_list.json` + the validator.

## Related

- `feature_list.schema.json` — the schema (already has dependencies[] + 4 states)
- `scripts/feature_dag_check.py` — DAG / WIP / VCR validator
- long-run-harness skill — when to mark `[LONG-RUN]`, bootstrap existing projects
- `no-pre-existing-evasion.md` — WIP=1 + VCR blocking rules this enforces
