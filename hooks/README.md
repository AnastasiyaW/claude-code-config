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
| [stop-phrase-guard.py](stop-phrase-guard.py) | `Stop` | Detects behavioral-regression phrases (ownership dodging, permission-seeking, premature stopping, known-limitation labeling, session-length excuses) in the final assistant message. Blocks Stop when match found so the agent either finishes or explains the blocker. Based on AMD Claude Code regression investigation ([issue #42796](https://github.com/anthropics/claude-code/issues/42796)). |

### Safety Guards

| Script | Event | What It Does |
|---|---|---|
| [destructive-command-guard.py](destructive-command-guard.py) | `PreToolUse` | Warns before destructive commands (`rm -rf`, `DROP TABLE`, `git push --force`, `git reset --hard`). Returns `{"decision": "block"}` with explanation. |
| [secret-leak-guard.py](secret-leak-guard.py) | `PreToolUse` | Blocks Write/Edit operations that would introduce secrets (API keys, tokens, passwords) into tracked files. |

### Quality & Context

| Script | Event | What It Does |
|---|---|---|
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
