# Hook Examples

Ready-to-use hook scripts for Claude Code. Copy to your project or `~/.claude/` and register in `settings.json`.

## Quick Setup

Add any hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "EventName": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python path/to/script.py",
            "statusMessage": "Running hook..."
          }
        ]
      }
    ]
  }
}
```

## Available Hooks

### Session Management

| Script | Event | What It Does |
|---|---|---|
| [session-drift-validator.py](session-drift-validator.py) | `SessionStart` | Validates file path references in CLAUDE.md and rules/ at session start. Catches stale pointers before the agent acts on them. |
| [session-handoff-reminder.py](session-handoff-reminder.py) | `Stop` | Reminds to write a handoff file when closing a long session. Prevents context loss between sessions. |
| [session-handoff-check.py](session-handoff-check.py) | `SessionStart` | Shows recent handoffs (single-file or multi-session format) at chat open so the agent can offer to continue. |
| [task-inbox-show.py](task-inbox-show.py) | `SessionStart` | Surfaces pending tasks from `.claude/task-inbox/*.json` snapshots (provider-agnostic tracker inbox). |
| [stop-phrase-guard.py](stop-phrase-guard.py) | `Stop` | Detects behavioral-regression phrases (ownership dodging, permission-seeking, premature stopping, known-limitation labeling, session-length excuses) in the final assistant message. Blocks Stop when match found so the agent either finishes or explains the blocker. Based on AMD Claude Code regression investigation ([issue #42796](https://github.com/anthropics/claude-code/issues/42796)). |
| [session-feedback-capture.py](session-feedback-capture.py) | `Stop` | Learn-from-corrections (capture): queues finished sessions with real back-and-forth into `~/.claude/feedback/queue.jsonl` for later distillation. Non-blocking, does NO keyword judgment (a keyword detector scored F1 0.42 on held-out tests — see [rules/learn-from-corrections.md](../rules/learn-from-corrections.md)); the LLM-semantic detection happens in `/distill-feedback`. |
| [feedback-pending-show.py](feedback-pending-show.py) | `SessionStart` | Learn-from-corrections (nudge): surfaces how many sessions are queued for feedback-distill so the loop closes. Silent when the queue is empty; self-clearing as sessions are processed. |

### Safety Guards

| Script | Event | What It Does |
|---|---|---|
| [destructive-command-guard.py](destructive-command-guard.py) | `PreToolUse` | Warns before destructive commands (`rm -rf`, `DROP TABLE`, `git push --force`, `git reset --hard`). Returns `{"decision": "block"}` with explanation. |
| [human-confirmation-guard.py](human-confirmation-guard.py) | `PreToolUse` | Requires an explicit in-chat user confirmation marker before destructive commands run. |
| [db-snapshot-guard.py](db-snapshot-guard.py) | `PreToolUse` | Enforces a DB snapshot/dump before destructive database operations. |
| [git-destructive-guard.py](git-destructive-guard.py) | `PreToolUse` | Blocks history-rewriting / work-losing git commands (`reset --hard`, raw `push --force`, `clean -fdx`). Bypass: `CLAUDE_ALLOW_GIT_DESTRUCTIVE=1`. |
| [git-auto-backup.py](git-auto-backup.py) | `PreToolUse` | When the git-destructive bypass is granted, auto-creates `claude-backup-{ts}` branch or stash before the destructive git command. |
| [backup-retention-cleanup.py](backup-retention-cleanup.py) | `Stop` | Removes `claude-backup-*` branches and `claude-pre-clean-*` stashes older than 14 days. |
| [command-injection-guard.py](command-injection-guard.py) | `PreToolUse` | Flags non-trivial `$(...)`/backtick substitutions in Bash commands; hard-blocks destructive verbs inside substitutions. |
| [secret-leak-guard.py](secret-leak-guard.py) | `PreToolUse` | Blocks Read/Edit/Write and Bash reads on secret files (`.env`, keys, `~/.ssh`, `~/.aws`). Bypass: `CLAUDE_ALLOW_SECRETS=1`. |
| [api-key-leak-detector.py](api-key-leak-detector.py) | `PostToolUse` | Detective control: scans tool output (Bash/Read/Grep) for well-known API key patterns and emits a loud rotate-now warning. |
| [self-harm-guard.py](self-harm-guard.py) | `UserPromptSubmit` | Guards against agent self-lockout (sshd restarts, killall node, firewall lockout, reboot). |
| [verify-deleted-guard.py](verify-deleted-guard.py) | `PostToolUse` | After deletion commands, verifies the target is actually gone (anti-fabrication). |
| [test-muting-guard.py](test-muting-guard.py) | `PreToolUse` | Blocks edits that add skip/xfail/`.only` markers to existing tests. Bypass: `CLAUDE_ALLOW_TEST_MUTING=1`. |
| [github-workflow-security.py](github-workflow-security.py) | `PreToolUse` | On first edit of a `.github/workflows/*.yml` per session, blocks once with an Actions-injection checklist; advisory afterwards. |
| [claude-attribution-guard.py](claude-attribution-guard.py) | `PreToolUse` | Blocks `git commit` / `gh pr create` / `gh issue create` carrying `Co-Authored-By: Claude` or `🤖 Generated with Claude Code` footers. OVERRIDEs Claude Code default system-prompt instruction. See [rules/no-claude-attribution.md](../rules/no-claude-attribution.md) for the policy and [rules/safety-billing.md](../rules/safety-billing.md) for the HERMES.md / Issue #53262 background. |
| [pre-push-claude-attribution.py](pre-push-claude-attribution.py) | git `pre-push` | Final gate before commits reach the remote. Scans the push range for the same attribution patterns and blocks the push. Install via `git config --global core.hooksPath` so it catches commits made outside Claude Code sessions too. Bypass: `CLAUDE_ALLOW_PUSH_ATTRIBUTION=1`. |

### Quality & Context

| Script | Event | What It Does |
|---|---|---|
| [file-cohesion-guard.py](file-cohesion-guard.py) | `PreToolUse` | Advisory (never blocks): warns when a durable file (code, doc, config, data) is written to a scratch location — home root, Desktop, Downloads, /tmp — instead of the project structure. Policy: [rules/file-organization-cohesion.md](../rules/file-organization-cohesion.md). |
| [keyword-skill-router.py](keyword-skill-router.py) | `UserPromptSubmit` | Detects natural-language trigger phrases and suggests matching skills (non-blocking). |
| [docs-staleness-guard.py](docs-staleness-guard.py) | `SessionStart` | Checks knowledge-base / docs freshness markers at session start. |
| [kb-validate-gate.py](kb-validate-gate.py) | `Stop` | Validates knowledge-base sync state before session close. |
| [feature-list-validator.py](feature-list-validator.py) | `Stop` | Validates feature-list consistency before session close. |
| [kvcache-stats.py](../scripts/kvcache_stats.py) | Manual | Analyzes KV-cache hit rate across sessions. Not a hook but a diagnostic script. |

## Hook Events Reference (Claude Code v2.1.89+)

| Event | When It Fires | Use For |
|---|---|---|
| `SessionStart` | New session begins | Validation, context loading, drift detection |
| `Stop` | Session ends | Handoff, cleanup, learning extraction |
| `PreToolUse` | Before any tool call | Safety guards, permission checks, logging |
| `PostToolUse` | After any tool call | Logging, notifications, side effects |
| `Notification` | Agent sends notification | Custom notification routing |
| `TaskCreated` | Sub-agent task spawned | Tracking, resource allocation |

### Conditional Hooks (v2.1.89+)

Use the `if` field to run hooks only for specific patterns:

```json
{
  "event": "PreToolUse",
  "hooks": [{ "type": "command", "command": "check_git.sh" }],
  "if": "Bash(git *)"
}
```

### Hook Responses

Hooks can return JSON to control behavior:

| Response | Effect |
|---|---|
| `{"decision": "allow"}` | Proceed normally |
| `{"decision": "block", "reason": "..."}` | Block the tool call |
| `{"decision": "defer"}` | Pause headless session for human review |
| `{"retry": true}` | Retry after PermissionDenied (v2.1.89+) |

### Matcher Patterns for PreToolUse/PostToolUse

```json
{"matcher": "Bash"}           // Any Bash call
{"matcher": "Write"}          // Any file write
{"matcher": "Bash(git *)"}    // Git commands only
{"matcher": "Bash(rm *)"}     // Delete commands only
{"matcher": "mcp__*"}         // Any MCP tool call
```

## Principles

- **Hook > Rule** for guaranteed behaviors. Rules are instructions of hope; hooks execute unconditionally.
- **One concern per hook.** Don't combine drift validation with secret scanning.
- **Exit 0 always.** A crashing hook blocks the agent. Use `|| true` in settings.json as a safety net.
- **Keep hooks fast.** They run synchronously. Target <500ms per hook.
