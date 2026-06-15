# Activity Journal + State Registry — make "what is running and who started it" answerable

## Principle

Any work that (a) spans **multiple sessions/agents** or (b) touches a **shared resource**
(a server, GPU host, database, queue, deploy target) needs three things so that *at any
moment anyone can answer "what is running right now, who started it, and why"*:

1. an **append-only activity journal** — every state-changing action logged;
2. a **current-state registry** — a human-readable "running now" of active services/jobs;
3. **mechanical enforcement** — a guard that blocks a mutating command which does not log,
   because discipline decays under context pressure but a hook does not.

Without these, the recurring failure is: *"something is downloading / loading the system /
got restarted and nobody knows what or who."* That is not a tooling gap — it is an
**agent-legibility** gap (what the agent/operator cannot inspect is operationally absent).

This is the operational rule for [principle 18 (multi-session coordination)](../principles/18-multi-session-coordination.md),
[19 (inter-agent communication)](../principles/19-inter-agent-communication.md) and
[25 (coordination primitives)](../principles/25-coordination-primitives-mapping.md). Classical
analogs: the journal is a **Write-Ahead Log / audit log**; the registry is a **materialized
view / status table**; the enforcement guard is **write-ahead-before-mutate**.

## The three artifacts

### 1. Activity journal — append-only (WAL)
One line per state-changing action: `ts · actor (session id) · scope/project · action · detail`.
JSONL is ideal (`grep`/`jq`-able, one record per line, never edit past lines). Records
**who / when / what / why** for: starts/stops of jobs & services, deletes, restarts, config
edits, deploys, resource (un)locks, space freed, anything that changes shared state.
Read-only inspection (status/ls/cat/tail) need not be logged.

> **Always stamp the actor.** Pass the session id (e.g. `CLAUDE_SESSION=<id>`) — otherwise the
> record attributes to `user@host` and you lose "which session did this".

### 2. State registry — current truth (materialized view)
A short human-readable file (`STATE.md` style) with a **"Running now"** section: each active
service/loop/job + which actor launched it + what it does + where it writes. Updated **whenever
state changes** (not a log — a snapshot). This is the at-a-glance answer the operator wants.
Keep a `Disk / Resources` block and a `Hard constraints` block so nobody relearns limits by pain.

### 3. Mechanical enforcement — a guard, not a habit
A pre-execution hook that **blocks** a mutating command on a tracked shared resource when the
command does not call the journal (and carries no explicit bypass). See
[`hooks/activity-journal-guard.py`](../hooks/activity-journal-guard.py) — config-driven
(targets + journal marker + mutating patterns), fail-open on parse error, read-only passes,
bypass via `# claude-bypass: journal`. Advisory reminders are not enough: they lose to
task-completion priority under context pressure (Compliance Decay). Mechanical invariants win.

## Two scopes

| Scope | Where the journal + registry live | Trigger |
|---|---|---|
| **Per-project** | in the repo / `.claude/` — handoffs ([session-handoff](session-handoff.md)) + a project `STATE.md` / running-jobs registry + `PROBLEMS.md` | any project with background jobs or >1 session |
| **Shared resource** | **on the resource** (or a shared path all sessions reach) so every session sees the same truth | a server / GPU host / DB touched by multiple sessions or an automated keeper |

For a single project worked by one session at a time, the [session-handoff](session-handoff.md)
file + `PROBLEMS.md` already are the journal+state. Add the shared on-resource journal + the
enforcing hook only once a **shared resource** is touched by more than one actor.

## How to apply (any project / resource)

1. **Pick the location.** Per-project → repo `.claude/`. Shared resource → a dir on it (e.g.
   `<resource>/ops/`) with `journal.<ext>` (append-only), `STATE.md`, `locks/`.
2. **Add a tiny journal CLI** (or just `echo`/`jq` append): `log <scope> "action" "detail"`,
   optional `lock/unlock/heartbeat <res>` for exclusive resources (see principle 18).
3. **Seed `STATE.md`** with the current "Running now" + constraints.
4. **Wire the enforcing hook** ([`hooks/activity-journal-guard.py`](../hooks/activity-journal-guard.py))
   with this resource's targets + journal marker. Now a mutating command without a log is denied.
5. **Discipline becomes free**: the hook forces the log; the log keeps `STATE.md` honest; any
   session/operator runs one read to see everything.

## Anti-patterns

- ❌ **Advisory-only reminder** for logging → decays; make it blocking.
- ❌ **Journal without a state registry** → you can reconstruct history but not answer "what is
  running NOW" at a glance. Keep both (log = history, STATE = snapshot).
- ❌ **Stale `STATE.md`** → the at-a-glance view lies; that *is* the "unclear what's running" pain.
  Update it on every state change (the hook + the habit of logging keep it fresh).
- ❌ **Unstamped records** (`user@host`) → cannot tell which session/agent acted.
- ❌ **Mutable journal** (editing past lines) → audit trail broken; append-only only.
- ❌ **One shared mutable table for everything** → concurrent writes race (principle 18). Journal
  is append-only (conflict-free); the registry is small + last-writer-wins-tolerant.

## Concrete instances

- **Per-project**: this repo's [session-handoff](session-handoff.md) (append-only handoffs +
  INDEX) is the project-scope journal; a project `STATE.md`/`feature_list.json` is the registry.
- **Shared GPU host**: a private `<host>/ops/` (journal.jsonl + STATE.md + locks/) with the
  enforcing hook — every session logs server mutations, `STATE.md` lists running jobs + who.

## Related
- [principle 18 — multi-session coordination](../principles/18-multi-session-coordination.md) (append-only vs mutable shared state, locks)
- [principle 19 — inter-agent communication](../principles/19-inter-agent-communication.md) (directed messaging)
- [principle 25 — coordination primitives mapping](../principles/25-coordination-primitives-mapping.md) (WAL / materialized-view / lease analogs)
- [session-handoff.md](session-handoff.md) — per-session handoff (the per-project journal)
- [file-organization-cohesion.md](file-organization-cohesion.md) — durable artifacts in the right home
- [`hooks/activity-journal-guard.py`](../hooks/activity-journal-guard.py) — the enforcing guard
