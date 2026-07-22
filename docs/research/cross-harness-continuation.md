# Cross-harness continuation research

## Finding

The Claude -> Codex complaint is a real coordination failure mode, not evidence
that either model intentionally ignores the other. Both tools can inspect the
same Git checkout, but the prior agent's intent, accepted decisions, tested
invariants, and unfinished scope are not automatically part of the next agent's
control state. A fresh agent therefore sees code plus an underspecified task and
may choose a competing design.

## Evidence

- Anthropic's long-running-agent work separates initialization from incremental
  coding, keeps a progress file and Git history, asks the next session to choose
  one unfinished feature, and requires a clean state plus tests before handoff.
- OpenAI's harness engineering describes the repository as the system of record:
  a short AGENTS.md maps to structured docs, active plans, decision logs, and
  mechanical freshness/quality checks.
- The MPAC paper models cross-principal coordination with explicit intent,
  operations, conflicts, and governance rather than ad-hoc chat or silent
  overwrites.
- The CAID paper reports that centralized delegation, isolated workspaces, and
  branch/merge/test verification are the useful SWE primitives for asynchronous
  agents. It also names concurrent edit interference and synchronization as the
  failure modes.

## Adopted design

1. A shared `CONTINUITY.json` is the machine-readable contract. It stores mode,
   baseline branch/commit, pre-existing paths, scope, preserve decisions,
   do-not-redo items, and verification evidence.
2. `continuity-session-check.py` surfaces the contract to both harnesses at
   session start. Missing state is visible instead of silently guessed.
3. `continuity-contract-guard.py` protects continuation mode mechanically:
   existing tracked files cannot be overwritten with `Write`; edits outside an
   enforced scope and near-whole-file replacements are blocked.
4. An explicit process-level `AGENT_CONTINUITY_MODE=replan` plus a non-empty
   `AGENT_CONTINUITY_REASON` is the escape hatch for a deliberate redesign. The
   reason must be recorded in the handoff/decision log by the agent.
5. Parallel work still uses isolated Git worktrees and a fresh verifier. The
   contract is for serial handoff and scope protection; it is not a substitute
   for merge conflict resolution or tests.
6. If handoff state already exists but the contract is missing, ordinary code
   edits are blocked until the baseline contract is created. New/one-shot
   repositories without handoff state remain advisory rather than being
   falsely gated.

## Rejected shortcuts

- Passing the whole chat transcript as the only handoff: too large, stale, and
  difficult to validate.
- Automatically reverting the next agent's changes: destructive and unable to
  distinguish a valid improvement from a regression.
- Blocking every edit without a contract: it breaks new projects and one-shot
  fixes. The guard instead blocks only repositories that already advertise
  continuation state through handoffs.

## Sources

- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://openai.com/index/harness-engineering/
- https://arxiv.org/abs/2604.09744
- https://arxiv.org/abs/2603.21489
