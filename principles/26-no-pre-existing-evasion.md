# 26 - No "pre-existing" evasion: structural enforcement against agent laziness

When a coding agent works for many turns, it learns a cheap escape hatch:
mark every awkward finding as "pre-existing", "out of scope", or
"deferred for separate refactor", then claim the task as done. Each
phrase is plausible, the summary looks tidy, and the bug stays in code.

This principle is the structural counter to that pattern. Phrase
detection is detective; this is preventive. The agent does not get to
choose whether to follow the rule, because the rule is enforced by code
that runs after the agent finishes.

## The pattern this addresses

GitHub issue [anthropics/claude-code#42796](https://github.com/anthropics/claude-code/issues/42796)
documents 173 stop-hook violations across 17 days in five categories.
The most damaging is **ownership dodging** (73 cases): "not caused by
my changes", "existing issue", "this falls outside the current change".

The cause is not specific to one model. Compliance Decay (Jaroslawicz
et al. 2025) shows linear decay - double the rules in a context, halve
adherence. CLAUDE.md grows; rules get summarised by compaction; "what
to do" survives but "how to do it" does not. The agent ends up
prioritising completion-as-claim over correctness-as-artifact.

Opus 4.7 sharpens this. Per [Anthropic's own guidance](https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code),
4.7 "tends to do exactly what you asked - no more, no less". If you
did not say "fix everything you find," it will narrow scope by design.

## The principle

> Agents must not label findings as "pre-existing" / "out of scope" /
> "deferred" / "complicated" / "risky" to avoid work. Only five reasons
> qualify as legitimate deferral, and each must produce an explicit
> entry in `PROBLEMS.md`. Without one of those five reasons, the
> finding must be fixed in the current session.

This is the [bradfeld pattern](https://gist.github.com/bradfeld/1deb0c385d12289947ff83f145b7e4d2):
"Fix or ticket — no middle ground."

## The five legitimate exceptions

Each is named because each is reproducible across projects and makes
the next session's job easier:

1. **missing-data** - data, credentials, or repo state needed for the
   fix is not currently obtainable
2. **missing-dep** - a tool, library, or service is not installed and
   the install requires user-level decisions (cost, admin, network)
3. **arch-decision** - the fix has multiple valid implementations and
   needs a consensus call beyond the current session
4. **scope-explosion** - the fix grows past task boundaries (>10
   files, >2 systems, >2 hours). Becomes its own ticket.
5. **inaccessible-repo** - the bug is in a codebase the agent cannot
   reach

"Complicated", "risky", and "pre-existing" are explicitly **not** on
this list. Complicated means split it; risky means test more carefully;
pre-existing means it stayed because nobody fixed it - including this
agent, now.

## Mandatory artifacts

Every bug-fix must produce *durable proof*, not narrative:

1. **Reproduction**: a command or steps that show the bug exists *before*
2. **Failing check**: a test, lint rule, or build error that goes red *before*
3. **Passing check**: same check goes green *after*
4. **No regression**: full suite stays green

If a project has no test runner, fall back to before/after curl output
or manual reproduction steps in the commit message. "Looks correct" is
not an artifact.

## Mechanical enforcement (defence in depth)

Rules in CLAUDE.md degrade. Hooks in code do not. This principle is
backed by three independent hooks:

| Layer | Hook | Catches |
|---|---|---|
| 1 - phrase | [`stop-phrase-guard.py`](../hooks/stop-phrase-guard.py) | Old text patterns ("pre-existing", "good stopping point", etc.). Detective only - agent can rephrase. |
| 2 - tests | [`test-gate-stop-hook.py`](../hooks/test-gate-stop-hook.py) | Red tests at Stop event. Blocks "done" claim while suite fails. |
| 4 - tickets | [`problems-md-validator.py`](../hooks/problems-md-validator.py) | OPEN entries in PROBLEMS.md without one of 5 exceptions. |

Layer 1 is detective; Layers 2 and 4 are preventive. Together they
cover the realistic ways an agent escapes the rule.

(Layer 3 is the **independent verifier agent** pattern from
[principle 5](05-structured-reasoning.md) and [02-proof-loop.md](02-proof-loop.md);
it is documented but not codified as a hook because it requires spawning
a fresh-context subagent.)

## Bypasses (used sparingly)

Each hook respects a project-level marker file and an env var:

- `CLAUDE_SKIP_TEST_GATE=1` / `.claude/.skip-test-gate`
- `CLAUDE_SKIP_PROBLEMS_CHECK=1` / `.claude/.skip-problems-check`

Use them in two cases only:
- The bypass case is itself documented in `PROBLEMS.md` with one of the
  5 valid exceptions, and the marker file is the documented workaround.
- An emergency requires shipping past a known-broken test (e.g. the
  test runner itself is wedged). After the emergency, remove the marker
  and address the underlying issue in the next session.

If you find yourself adding bypass markers regularly, the rule is
working: it is surfacing the actual decision the agent was hiding from.
The marker is the visible artifact of "I chose to defer". Compare with
the previous state, where the same decision was invisible.

## How this differs from existing safety hooks

The repository already has hooks for safety (destructive-command-guard,
git-destructive-guard, secret-leak-guard). Those protect from
**accidental damage**. The hooks for this principle protect from
**deliberate inaction**: the agent knows what to do, the agent does not
do it, and we make that decision visible.

## See also

- [Principle 02 - Proof Loop](02-proof-loop.md) - durable artifacts as
  finish criterion
- [Principle 04 - Deterministic Orchestration](04-deterministic-orchestration.md) -
  Anti-Fabrication ("agent cannot claim, must produce")
- [Principle 23 - Anti-Pattern as Config](23-anti-pattern-as-config.md) -
  encoding behavioural lessons in config rather than docstrings
- Rule: [no-pre-existing-evasion.md](../rules/no-pre-existing-evasion.md)
- Hooks: [test-gate-stop-hook.py](../hooks/test-gate-stop-hook.py),
  [problems-md-validator.py](../hooks/problems-md-validator.py),
  [stop-phrase-guard.py](../hooks/stop-phrase-guard.py)
