#!/usr/bin/env python3
"""PreToolUse: ENFORCE the shared activity journal when mutating a tracked shared resource.

General, config-driven version of the "force journaling" pattern (see
rules/activity-journal-and-state-registry.md). When a Bash/PowerShell command reaches a
configured shared resource (ssh/scp/rsync to one of its targets) and MUTATES state, and the
command does NOT call that resource's journal and carries no `# claude-bypass: journal` marker,
the command is BLOCKED until a journal call is added.

Why: discipline decays under context pressure; an append-only journal + state registry only
work if every mutation is logged. A mechanical guard keeps the journal complete so that
"what is running, who started it, why" is always answerable.

Config (so this is reusable, not tied to any one host) — first match wins:
    ~/.claude/activity-journal.config.json
    {
      "resources": [
        {
          "name": "mygpu",                       # shown in the block message
          "targets": ["myhost", "10.0.0.5"],     # ssh/scp destinations that mean "this resource"
          "journal_marker": "journal.py",        # substring proving the cmd logs (regex-free)
          "log_hint": "ssh myhost 'journal.py log <proj> \"what\" \"detail\"; <cmd>'"
        }
      ]
    }

INERT BY DEFAULT: with no config file (or empty `resources`), this hook allows everything —
shipping it in a shared config never blocks anyone who has not opted in. Concrete hardcoded
instance for a specific host: see `mashinki-journal-reminder.py` (same pattern, fixed targets).

Bypass: `# claude-bypass: journal` in the command, or CLAUDE_ALLOW_NO_JOURNAL=1.
Fail-OPEN on any error (a hook bug must never block every command).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import allow, bash_command, block, bypass, read_event  # noqa: E402

CONFIG_PATH = Path.home() / ".claude" / "activity-journal.config.json"

SSH_TOKEN_RE = re.compile(r"(?<![a-z])(ssh|scp|rsync)(?![a-z])", re.IGNORECASE)

# Tokens that indicate the remote/shared command CHANGES state (worth logging).
MUTATING_RE = re.compile(
    r"\b(docker\s+(stop|start|restart|rm|run|kill|update|compose)|"
    r"rm\s|rmdir|pkill|killall|\bkill\s|mv\s|nohup|setsid|systemctl\s+(start|stop|restart|disable|enable)|"
    r"sed\s+-i|tee\b|chmod|chown|crontab|cryptsetup|mkfs|dd\s+if=|truncate|"
    r"createdb|dropdb|psql|mysql|>\s*/|>>\s*/)",
    re.IGNORECASE,
)


def _load_resources() -> list[dict]:
    try:
        if not CONFIG_PATH.exists():
            return []
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        res = data.get("resources", [])
        return res if isinstance(res, list) else []
    except (OSError, json.JSONDecodeError, ValueError):
        return []


def main() -> None:
    if os.environ.get("CLAUDE_ALLOW_NO_JOURNAL") == "1":
        allow()

    resources = _load_resources()
    if not resources:
        allow()  # inert until configured

    event = read_event()
    if event.get("tool_name") not in ("Bash", "PowerShell"):
        allow()

    cmd = bash_command(event.get("tool_input", {}))
    if not cmd or not SSH_TOKEN_RE.search(cmd):
        allow()

    low = cmd.lower()

    # Find which configured resource this command targets (first match wins).
    hit = None
    for r in resources:
        targets = [str(t).lower() for t in r.get("targets", []) if t]
        if any(t in low for t in targets):
            hit = r
            break
    if hit is None:
        allow()  # not a tracked resource

    marker = str(hit.get("journal_marker", "journal.py")).lower()
    if marker and marker in low:
        allow()  # already journaling
    if bypass("journal", cmd):
        allow()

    if not MUTATING_RE.search(cmd):
        allow()  # read-only, no need to log

    name = hit.get("name", "shared resource")
    hint = hit.get("log_hint", "add a journal log call in the same command")
    block(
        f"📓 activity journal — BLOCKED: state-changing command on '{name}' with no journal entry.\n"
        f"The shared journal + state registry are how anyone sees what is running / who started it.\n"
        f"Add the journal call to THIS command, e.g.:\n  {hint}\n"
        f"Read-only commands pass. One-off / not worth logging → bypass: "
        f"`# claude-bypass: journal` + `# Reason: ...`. (rules/activity-journal-and-state-registry.md)"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail-open: never let a guard bug block every command.
        allow()
