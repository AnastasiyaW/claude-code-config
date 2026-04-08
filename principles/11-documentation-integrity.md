# 11 - Documentation Integrity: Prevent Config Drift for AI Agents

## The Problem

Documentation drift - where high-level docs stay updated but their details rot - is a nuisance for humans but *catastrophic* for AI agents.

A human reading "see the auth flow in `foo/handler.py:42`" notices the file was renamed last month, mentally corrects, finds the new location. An agent follows the stale reference, reads the wrong file (or nothing), produces a confidently wrong answer, and commits it.

Classic failure modes:

- `CLAUDE.md` says "use the `deploy.sh` script" but the script was renamed to `release.sh`
- A principle cites `src/models/user.py` but the model was split into three files
- A skill references `.claude/scripts/setup.py` but the script was deleted in a refactor
- A rule tells the agent to check `config.yaml` but the project switched to `config.toml`

The agent has no "smell test" for this. It will obey the stale instruction and fail silently.

## The Paradigm

**Validate references at session start, not after failure.** This is analogous to how Rust's type system prevents memory errors at compile time rather than catching them at runtime. Instead of waiting for the agent to trip over a broken reference, verify every reference before the session begins. If something is broken, the agent knows immediately - and can either fix it, warn the user, or refuse to act on the stale section.

Drift is not a documentation problem. It is a **correctness** problem, and it should be treated like a failing test.

## The Mechanism: SessionStart Validator Hook

A Python script, registered as a `SessionStart` hook, scans `CLAUDE.md` and all `.claude/rules/*.md` files for file path references. For each reference, it checks whether the target still exists. Findings are printed to stdout, which the harness injects into the agent's initial context.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/scripts/validate_config.py",
            "statusMessage": "Checking config drift..."
          }
        ]
      }
    ]
  }
}
```

The agent sees something like:

```
[config-validator] DRIFT DETECTED: 3 broken references
  - CLAUDE.md: broken ref -> src/models/user.py
  - .claude/rules/deploy.md: broken ref -> scripts/release.sh
  - .claude/rules/tests.md: broken ref -> tests/legacy/
```

and can proactively warn the user: "I noticed 3 broken references in your config. Want me to fix them first?"

## Reference Detection: Precision Over Recall

The challenge is distinguishing **real references** (files the agent should actually find) from **examples and concepts** (`foo.py` as a placeholder, `README.md` as a generic term).

The validator uses structural rules to identify "real" references:

- Absolute paths: `C:\Users\...`, `/home/...`
- Home-relative: `~/.claude/...`
- Explicit relative: `./foo`, `../foo`
- Multi-segment: `foo/bar/baz.ext` (must contain at least one slash)

Bare filenames (`foo.py`, `README.md`) are skipped - they are almost always used as concepts or examples. This trades some recall for much higher precision. A noisy validator that cries wolf every session gets ignored.

Additional skip patterns filter out obvious placeholders:

```python
SKIP_PATTERNS = [
    "path/to/", "foo/", "bar/", "example.",
    "your-", "my-", "<", "$", "{",
    "0N", "...",  # template placeholders
]
```

## Contextual Path Resolution

A reference in `~/.claude/CLAUDE.md` that says `claude-code-config/alternatives/session-handoff.md` is not relative to `~/.claude/` - it is a project suffix that the user expects the agent to find somewhere in their workspace.

The validator tries multiple resolution strategies:

1. Expand `~` to home directory
2. Absolute path check
3. Relative to the file containing the reference
4. Relative to current working directory
5. **Contextual lookup**: check under common workspace roots (`~/Desktop`, `~`)

If any strategy finds the file, the reference is valid. Only if all strategies fail is the reference flagged as drift.

## Beyond Path Validation

Path validation is the minimum. More sophisticated validators can check:

**Semantic references** - the doc says "use the `auth_middleware` function in this file." Validator greps the file for the symbol.

**Command freshness** - the doc says "run `npm run deploy`." Validator parses `package.json` and verifies the script exists.

**API signatures** - the doc has a code snippet calling `client.generate(prompt=...)`. Validator runs the snippet through a type checker.

**Freshness metadata** - each doc carries a `last_verified: YYYY-MM-DD` frontmatter field. Validator warns if older than N days.

Each layer adds confidence but also maintenance cost. Start with path validation; add semantic checks only where the payoff is clear.

## Why a Hook, Not a Rule

A `.claude/rules/` file saying "check all references at session start" is an *instruction of hope*. The agent has the rule in its system prompt but only follows it when:

1. It remembers the rule exists
2. It knows "now is session start"
3. It chooses to apply it

Under context pressure, any of these can fail. The agent skips the check, reads a stale reference three hours later, and produces garbage.

A hook is different. It is a shell process that runs **unconditionally** at the correct moment. It does not care about context windows or attention allocation. When SessionStart fires, the validator runs - every time, no exceptions.

This distinction - rule (instruction) vs hook (mechanism) - is the core lesson: **automated behaviors require hooks, not rules.** If you want something to happen *every time* X occurs, the harness must enforce it. The agent cannot be trusted to enforce it on itself.

## Related to Other Principles

- **Principle 02 (Proof Loop)**: both use fresh, independent verification instead of self-reporting
- **Principle 04 (Deterministic Orchestration)**: Shell Bypass principle - mechanical tasks should not go through the LLM. Reference checking is mechanical.
- **Principle 07 (Codified Context)**: context is infrastructure, not documentation. Broken references = broken infrastructure.
- **Principle 10 (Agent Security)**: stale references are an injection vector - an attacker who knows your docs reference `old_file.py` can create a malicious `old_file.py` that the agent will read.

## Starter Implementation

The full validator script is at [scripts/validate_config.py](../scripts/validate_config.py) in this repo. To wire it up:

1. Copy `validate_config.py` to `~/.claude/scripts/`
2. Register the hook in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/scripts/validate_config.py",
            "statusMessage": "Checking config drift..."
          }
        ]
      }
    ]
  }
}
```

3. Test it: `python ~/.claude/scripts/validate_config.py` from a project directory. You should see either `OK` or a list of broken references.

On your next Claude Code session start, the agent will see the drift report automatically and can act on it before touching any code.

## Sources

- Fiberplane, [Documentation drift linting](https://fiberplane.com/blog/drift-documentation-linter/)
- Redis, [Context rot in LLMs](https://redis.io/blog/context-rot/)
- Hugging Face, [Runnable documentation examples](https://huggingface.co/blog/huggingface/runnable-examples)
- lychee, [Fast async link checker in Rust](https://github.com/lycheeverse/lychee)
- Qt, [Architecture-as-code with static analysis](https://www.qt.io/quality-assurance/blog/real-world-lessons-with-static-analysis-and-the-architecture-as-code-approach)
