# Per-Subsystem Checklist

Concrete binary checks for each of the five subsystems. Use these to produce a defensible score, not a guess.

---

## 1. Instructions (How the agent knows what to do)

### Hard checks

- [ ] `CLAUDE.md` exists in project root (or `AGENTS.md`)
- [ ] Root instruction file is **under 200 lines** (else: instruction bloat, see principle 11)
- [ ] Project has `.claude/rules/` directory with at least one rule file
- [ ] At least one rule names a **hard constraint** ("NEVER do X") with consequences spelled out
- [ ] If user is in a fork/branch context: `~/.claude/CLAUDE.md` (global) is acknowledged or extended, not duplicated
- [ ] Hard rules are visually distinct from soft preferences (bold/heading/section, not buried in prose)

### Soft checks

- [ ] Project has `REVIEW.md` for code-review-specific guidance (only required for repos with PRs)
- [ ] Routing/entry doc explains what to read in what order ("Startup Workflow" section in CLAUDE.md)
- [ ] No contradictions between root CLAUDE.md and `.claude/rules/*` (manual scan, look for opposing claims)
- [ ] No stale references — file paths and function names mentioned in rules actually exist (sample 3 references)

### Scoring

- **5**: All hard checks pass + 3-4 soft checks pass. CLAUDE.md is the right size, modular rules, clear hierarchy.
- **4**: All hard checks pass + 1-2 soft checks pass.
- **3**: CLAUDE.md exists and is reasonable but no `.claude/rules/`, or has 500+ line monolithic file.
- **2**: CLAUDE.md exists but is mostly project-description, not agent-guidance. No constraints.
- **1**: No CLAUDE.md, no AGENTS.md, no rules anywhere. Agent has nothing to orient on.

---

## 2. State (What the project knows about itself)

### Hard checks

- [ ] `PROBLEMS.md` exists in project root
- [ ] `PROBLEMS.md` has at least one entry (not just a header — empty file = same as missing)
- [ ] `feature_list.json` exists in project root
- [ ] `feature_list.json` validates against the JSON Schema (at least: features array, each with id/name/status)
- [ ] `.claude/handoffs/` directory exists
- [ ] `.claude/handoffs/` has recent activity (at least one file from last 14 days, or `INDEX.md` shows recent entries)

### Soft checks

- [ ] `.claude/chronicles/{slug}.md` exists for the project (only required for `[LONG-RUN]` projects, otherwise skip)
- [ ] `feature_list.json` has at most **one** feature with `status: "in-progress"` (WIP=1 check)
- [ ] Features marked `done` have non-empty `evidence` field
- [ ] PROBLEMS.md entries have Status field (OPEN / RESOLVED / WORKAROUND / BLOCKED-ON-X)
- [ ] Handoffs follow naming convention `YYYY-MM-DD_HH-MM_<sessid>.md`

### Scoring

- **5**: All hard + all soft. PROBLEMS.md is rich, feature_list reflects real scope, handoffs flow.
- **4**: All hard + 3-4 soft. Maybe missing chronicles or evidence is sparse.
- **3**: Has handoffs but missing PROBLEMS.md OR missing feature_list.json (not both).
- **2**: Has handoffs only. No PROBLEMS.md, no feature_list.json. State is in free-form notes.
- **1**: No handoffs, no PROBLEMS.md, no feature_list.json. Nothing survives sessions.

---

## 3. Verification (How does the project know it works)

### Hard checks

- [ ] `init.sh` exists in project root and is executable
- [ ] `init.sh` runs **dependency install + L1 (lint/types) + L2 (tests)** at minimum (read the file)
- [ ] Test runner is configured (`pytest.ini`, `vitest.config`, `Cargo.toml [dev-dependencies]`, etc.)
- [ ] At least one test exists and is not skipped/disabled
- [ ] CLAUDE.md mentions the 3-Layer Validation Gate (L1/L2/L3) OR references principle 02 (Proof Loop) OR similar staged verification

### Soft checks

- [ ] `init.sh` completes in under 3 minutes on fresh clone (target metric)
- [ ] Tests pass currently (run them — if `init.sh` is documented, sample run it; else: ask user)
- [ ] CI configuration mirrors `init.sh` (so PRs are gated by the same checks)
- [ ] Evidence field in feature_list.json references L1/L2/L3 artifacts when `done`
- [ ] `.proof/` or `.agent/tasks/` directory exists with at least one verified task (Proof Loop adoption)

### Scoring

- **5**: All hard + 4-5 soft. init.sh is fast and complete, tests pass, evidence is concrete.
- **4**: All hard + 2-3 soft.
- **3**: Tests exist but no init.sh, or init.sh exists but doesn't cover L1+L2.
- **2**: Tests are configured but rarely run / mostly skipped. No init.sh.
- **1**: No tests, no init.sh, "works on my machine" is the verification model.

---

## 4. Scope (Does the agent stay in bounds)

### Hard checks

- [ ] CLAUDE.md or rules contain a "no-pre-existing evasion" / "fix in scope" principle (search for: "pre-existing", "in scope", "WIP", "one feature at a time")
- [ ] Definition of Done is **explicit** in CLAUDE.md or a rule (not just implied)
- [ ] If feature_list.json exists: at most one feature `in-progress` (WIP=1)
- [ ] Task-deferral has named valid reasons (not freeform "I'll do it later")

### Soft checks

- [ ] PROBLEMS.md uses one of 5 valid statuses for deferred items (missing-data / missing-dep / arch-decision / scope-explosion / inaccessible-repo)
- [ ] Stop hook `check-problems-md.py` is registered (mechanical enforcement of scope)
- [ ] Recent handoffs do **not** end with "left for next session" without a registered ticket
- [ ] Recent commits don't have "WIP" or "todo: fix later" in messages (sample 10 most recent)

### Scoring

- **5**: Hard rules in place AND mechanical enforcement (hooks) AND recent history shows discipline.
- **4**: Hard rules in place, mechanical enforcement, occasional drift in history.
- **3**: Hard rules in place but no enforcement, history shows multiple "deferred" items.
- **2**: Soft conventions only, no explicit rules. Drift visible in recent work.
- **1**: No scope discipline. Agent regularly half-finishes features and moves on.

---

## 5. Lifecycle (What happens at session boundaries)

### Hard checks

- [ ] `.claude/settings.json` or `.claude/settings.local.json` exists
- [ ] At least one SessionStart hook is registered (to inject context / validate environment)
- [ ] At least one Stop hook is registered (to enforce cleanup / handoff / tests)
- [ ] `init.sh` is documented as the canonical entry point (mentioned in CLAUDE.md Startup Workflow)
- [ ] Cleanup convention is named (e.g., "don't commit if `./init.sh` is red")

### Soft checks

- [ ] `stop-test-gate.py` or equivalent hook blocks Stop on red tests
- [ ] `check-problems-md.py` or equivalent hook blocks Stop on OPEN problems without ticket
- [ ] `remind_handoff.py` or equivalent for long sessions (>30 turns or >2h)
- [ ] Auto-backup hook (`auto_backup_git.py`) is configured before destructive ops
- [ ] Backup retention runs periodically (`cleanup_backup_branches.py`)
- [ ] No half-completed sessions in handoffs (Status: ABANDONED count is < 20% of total)

### Scoring

- **5**: All hard + 4-6 soft. Hooks do the enforcement, agent's discipline is reinforced by code.
- **4**: All hard + 2-3 soft. Most enforcement is automated.
- **3**: Some hooks configured but cleanup is mostly manual.
- **2**: settings.json exists but is mostly empty. Sessions end without artifacts.
- **1**: No settings.json, no hooks. Every session ends silently with no state captured.

---

## How to Apply When Auditing

1. For each subsystem, walk through the hard checks first. Count passes/failures.
2. If hard checks are mixed (e.g., 4 of 6 pass), use the soft checks to break the tie between adjacent scores.
3. **Don't claim 5/5 unless soft checks are also strong**. 5/5 is exemplary, not "good enough".
4. **Don't claim 1/5 if there's any structure at all**. 1/5 means the project has *no* harness in this dimension.

When in doubt, score lower. A skill that gives every project 4-5/5 has no signal — the user can't tell which subsystem to fix.
