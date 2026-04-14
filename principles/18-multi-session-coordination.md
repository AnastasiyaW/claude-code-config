# Multi-Session Coordination — shared state between parallel Claude sessions

## The problem

You run **several Claude Code sessions simultaneously** in the same workspace. Each session reads/writes the same files. Conflicts emerge:

- Two sessions grab the same GPU / container / port
- Two sessions edit the same config file, one overwrites the other
- A new session has no idea what other active sessions are doing right now
- A session crashes leaving "in-progress" markers that block new work forever

Memory files + CLAUDE.md solve **persistent** state (across time). They don't solve **concurrent** state (across parallel processes). This is a classic distributed-systems problem in new clothing.

## Two fundamentally different types of shared state

Do not build one mechanism for both — they have opposite requirements.

### Type 1: Append-only state (conflict-free)

**Examples:** session handoffs, operation logs, findings, journal entries.

**Properties:** each session writes **its own file** with a unique name. No session ever reads-then-writes another session's file. An index file is append-only (dopisat new line, never edit old lines).

**Why it works:** there is no shared variable to race on. Two sessions producing two files at the same moment produce two files. Done.

**File layout:**
```
.claude/handoffs/
├── 2026-04-14_11-32_<session-id>.md   ← session 1 writes here
├── 2026-04-14_11-45_<session-id>.md   ← session 2 writes here
└── INDEX.md                            ← append-only log
```

### Type 2: Mutable shared state (requires coordination)

**Examples:** GPU allocation, port binding, container ownership, "who is running the dataset preprocessing right now".

**Properties:** exactly **one** session can hold the resource. Other sessions must see "taken" and back off.

**Why append-only doesn't work:** you cannot represent "GPU 2 is taken by session X" as `append_to_log("GPU 2 taken")` — because the next session reads the log and sees the line, but has no mechanism to know if the holder is still alive or already released it.

**Solution: lock files with heartbeats.**

## Lock-file pattern (mutable state)

### File structure

```
.claude/locks/
├── <resource-id>.lock                  ← one file per lockable resource
└── INDEX.md                             ← append-only log of TAKE/RELEASE events
```

**Resource IDs are canonical:** `gpu_host-a_3`, `port_8080`, `container_training-01`. One canonical name per resource, not variants like `gpu_3` vs `hostA_gpu3`.

### Lock file content

```yaml
---
session_id: <short-id-or-task-name>
resource: gpu_host-a_3
task: "Training LoRA step 0/5000"
started: 2026-04-14T14:20
heartbeat: 2026-04-14T14:20
expected_duration_hours: 4
---

Free-text details about what this session is doing.
```

### Take protocol

1. Read static rules (if any) — is this resource even allowed for your task? (e.g. "GPU 6 = production, never touch")
2. Check `.claude/locks/<resource-id>.lock`:
   - **No file** → resource is free, go to step 3
   - **File exists, heartbeat fresh** (< N hours) → **TAKEN**, do not proceed
   - **File exists, heartbeat stale** (> N hours) → go to step 2a
3. Write lock file (via Write tool — single atomic operation, not append-in-pieces)
4. Append to INDEX.md: `YYYY-MM-DD HH:MM | TAKE | <resource-id> | <session> | <task>`

**Step 2a (stale verification):** before reclaiming a stale lock, **verify externally** that the process is actually dead (nvidia-smi / ps / lsof on port / docker ps). A stale heartbeat might just mean the session got busy and forgot to update — not that it died. If the process is alive, do not reclaim; log `STALE-BUT-ALIVE` and ask the user.

### Heartbeat

For any task running longer than 2× your stale-threshold, **update the `heartbeat` field** every 30–60 min. This prevents "session crashed, lock lives forever" pathology.

Edit the lock file in-place (Edit tool, change one line). No need to re-log every heartbeat in INDEX.md — only TAKE / RELEASE / STALE-RECLAIM events matter for the human-readable log.

### Release protocol

1. `rm .claude/locks/<resource-id>.lock`
2. **Verify it's gone** (`ls` — no such file). Do not claim "released" without this check. The `rm` may silently fail on permissions, locked files, wrong path.
3. Append to INDEX.md: `YYYY-MM-DD HH:MM | RELEASE | <resource-id> | <session> | <result summary>`

## Convention over automation — start here, add hooks later

A common trap is writing a `PreToolUse` hook that parses tool commands to auto-manage locks. This fails because:

- Commands are diverse (`ssh ...`, `docker exec ...`, raw scripts, piped chains)
- A regex-based parser produces false positives and false negatives equally
- Every project has different resource types (GPUs, ports, queues, locks on things that don't even live on disk)

**Correct evolution:**

1. **Convention first.** Document the protocol in `.claude/rules/<coordination-name>-protocol.md`. Train yourself to follow it. Observe which steps you skip.
2. **Pattern observation.** After a few weeks, see which concrete operations (always `docker run` with `--gpus device=N`? always `uvicorn --port X`?) are stable enough to auto-detect.
3. **Hook only the stable cases.** A `PreToolUse` hook that matches one concrete pattern and warns "resource X appears taken by another session" is valuable. A hook that tries to understand all SSH semantics is a tarpit.

## Session identity

Sessions need **something** to identify themselves in locks and logs. Options:

- **Claude Code session ID** — if available in your environment (some harnesses expose it via env var)
- **Short task name** — `face-beauty-train`, `dataset-prep` (user-supplied at session start)
- **Timestamp + random suffix** — `2026-04-14_14-20_7f3a`

A short 6–8 char identifier is enough. The point is making "which session holds this lock" human-debuggable, not globally unique.

## Patterns to avoid

1. **Shared mutable table in memory/** — e.g. `memory/active_allocations.md` edited by all sessions. Race conditions. Losses. Use lock files instead.
2. **Deleting someone else's lock** because it "looks stale" — always verify the process is dead before reclaiming.
3. **Silent release** — `rm` without verify. The log will say RELEASED but the file may still exist.
4. **Locks named after task, not resource** — `.claude/locks/my-training.lock` can't tell you which GPU is taken. Name locks after the **resource** (`gpu_3.lock`), put task inside.
5. **INDEX editing** — if you need to "correct" an earlier log line, don't edit it. Append a new line with correction. The log is history, not state.

## Example: full lifecycle

```
[session face-beauty at 14:20]
1. read memory/gpu_static_rules.md           # GPU 3 is in "training OK" pool
2. ls .claude/locks/gpu_host-a_3.lock       # No such file
3. write .claude/locks/gpu_host-a_3.lock    # atomic
4. append INDEX.md                           # "14:20 | TAKE | gpu_host-a_3 | face-beauty | LoRA step 0/5000"
5. start training via SSH

[session face-beauty at 15:30]
6. edit .claude/locks/gpu_host-a_3.lock     # heartbeat: 15:30

[session dataset-prep at 15:45]
7. ls .claude/locks/gpu_host-a_3.lock       # File exists, heartbeat 15min ago — TAKEN
8. try gpu_4 instead

[session face-beauty at 19:40, done]
9. rm .claude/locks/gpu_host-a_3.lock
10. ls .claude/locks/gpu_host-a_3.lock      # No such file ✓
11. append INDEX.md                          # "19:40 | RELEASE | gpu_host-a_3 | face-beauty | Done, loss 0.19"
```

## Prior art (as of 2026-04)

The space around parallel Claude sessions is growing fast, but the solutions cluster around **isolation**, not **shared-state coordination**. A real gap remains for live resource locks across sessions.

| Solution | Approach | What it solves | What it doesn't |
|---|---|---|---|
| [Anthropic Agent Teams](https://code.claude.com/docs/en/agent-teams) | Shared TASKS.md, claim-by-identifier | Workers picking from a task queue | Arbitrary resource locks (GPU, port, container) |
| [claude_code_agent_farm](https://github.com/Dicklesworthstone/claude_code_agent_farm) | File-based locks, tmux monitoring, 20+ parallel agents | Orchestration-first, closest to lock pattern | Interactive single-user multi-chat workflows |
| [parallel-cc](https://github.com/frankbria/parallel-cc) | Git worktrees + E2B sandboxes | Full isolation - no shared state exists | When you actually need shared resources |
| [Kmux](https://www.kmux.dev/) | Per-agent worktrees + port sub-allocation, injected env | Infra-level separation | File-level coordination |
| [mclaude](https://github.com/aydensmith/mclaude) | Multi-session chat collaboration, hooks | Communicating between chats | Resource ownership |
| [Issue #19364](https://github.com/anthropics/claude-code/issues/19364) | Proposed `~/.claude/projects/{project}/{session}.lock` | Would give per-session pidfile primitive | Not implemented |
| [Mustafa Kuzey, "AI Mutex Lock", Mar 2026](https://medium.com/@mustafa_16192/how-an-ai-mutex-lock-may-look-like-keeping-your-ai-agents-from-colliding-0bdce18d3359) | CAS (Compare-And-Swap) primitives conceptually | Theoretical framing | No shipped code |

**Cautionary data:** [Issue #29217](https://github.com/anthropics/claude-code/issues/29217) documents `.claude.json` corruption from concurrent writes — 8+ reports, 315 corrupted backups in 7 days, hotfixed in v2.1.61. Even Anthropic's own first-party state file does not survive naive concurrent writes. This is why **per-resource files** (one lock = one file) matter: they make concurrent-write windows tiny and scoped, whereas one shared table multiplies the blast radius of any race.

## Related principles

- [04-deterministic-orchestration](04-deterministic-orchestration.md) — anti-fabrication requires verify-after-act (the `ls` after `rm` in release protocol)
- [07-codified-context](07-codified-context.md) — locks are codified live state, not documentation
- [16-project-chronicles](16-project-chronicles.md) — locks are tactical ("taken right now"), chronicles are strategic ("how we got here"); keep them separate

## Why this is the same problem distributed systems solved 40 years ago

Heartbeats, stale detection, lock files, append-only logs, canonical resource naming — this is Chubby (Google), ZooKeeper, and every coordination system since. AI agents sharing a workspace **are** concurrent processes. Don't invent — translate.
