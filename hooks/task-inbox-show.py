#!/usr/bin/env python3
"""SessionStart hook: surface pending tasks from any tracker inbox.

Some teams run a small script on the operator's machine that polls their
task tracker (Vikunja, Linear, Jira, GitHub Projects, ...) for tasks
assigned to the agent-identity and writes snapshots into
`.claude/task-inbox/<id>.json`. This hook reads that directory at session
start and prints a compact summary so the agent can pick a task up
without the human pasting one.

The hook is **provider-agnostic**. It does not know or care which
tracker wrote the snapshots. It only needs each file to be JSON with
the fields shown below. That way a team can use any tracker; the
inbox directory is the integration boundary.

Expected snapshot format (any extra fields are ignored):

    {
      "task_id": 1247,            // int or string
      "title": "Fix auth race",   // short human title
      "priority": 3,              // 0-5, higher = more urgent
      "labels": ["ai-ready"],     // optional list
      "link": "https://..."       // optional URL
    }

Files older than any you want to keep can be deleted by the poller -
this hook does not delete or modify anything.

Setup in .claude/settings.json:

    {
      "hooks": {
        "SessionStart": [{
          "hooks": [{
            "type": "command",
            "command": "python hooks/task-inbox-show.py"
          }]
        }]
      }
    }

The hook stays silent when the inbox is empty or missing, so sessions
that do not use any tracker integration see zero output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


# Subdirectory names this hook recognises. If your poller writes
# snapshots under a different name, either rename to one of these or
# extend this list in a fork.
INBOX_DIR_NAMES = ("task-inbox", "vikunja-inbox", "linear-inbox",
                   "jira-inbox", "gh-inbox", "inbox")


def _find_inbox() -> Path | None:
    """Look for `.claude/<inbox>/` in cwd and up to 3 parents."""
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents[:3]):
        claude_dir = candidate / ".claude"
        if not claude_dir.is_dir():
            continue
        for name in INBOX_DIR_NAMES:
            p = claude_dir / name
            if p.is_dir() and any(p.glob("*.json")):
                return p
    return None


def _priority_label(p: int) -> str:
    if p <= 0:
        return "P0"
    return f"P{min(p, 5)}"


def main() -> int:
    inbox = _find_inbox()
    if inbox is None:
        return 0  # no inbox configured for this project - stay silent

    files = sorted(inbox.glob("*.json"))
    if not files:
        return 0

    entries = []
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        tid = data.get("task_id", "?")
        title = (data.get("title") or "")[:70]
        labels = data.get("labels") or []
        try:
            priority = int(data.get("priority") or 0)
        except (TypeError, ValueError):
            priority = 0
        entries.append((priority, tid, title, labels))

    if not entries:
        return 0

    # Highest priority first
    entries.sort(key=lambda e: (-e[0], str(e[1])))

    kind = inbox.name  # e.g. "linear-inbox" or "task-inbox"
    print(f"[{kind}] {len(entries)} task(s) pending:")
    for priority, tid, title, labels in entries[:10]:
        label_part = f" [{' '.join(labels)}]" if labels else ""
        print(f"  #{tid} {_priority_label(priority)}{label_part} {title}")
    if len(entries) > 10:
        print(f"  ... and {len(entries) - 10} more")
    print()
    print("  Your poller script populates this inbox; claim a task in the "
          "tracker UI or via your team's bridge before starting work.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
