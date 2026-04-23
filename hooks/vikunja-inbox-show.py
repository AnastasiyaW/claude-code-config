#!/usr/bin/env python3
"""SessionStart hook: surface Vikunja inbox at the start of a Claude session.

Companion to a Vikunja inbox poller that writes task snapshots into
`.claude/vikunja-inbox/<task-id>.json`.

When a Claude session opens, this hook reads `.claude/vikunja-inbox/`
in the current project and prints a compact summary. The agent sees it
in its initial context and can decide whether to pick up one of the
pending tasks.

Output format (shown to the agent):

    [vikunja-inbox] 2 tasks pending assignment:
      #1247 P3 [ai-ready runtime/claude] Fix auth race condition
      #1252 P2 [ai-ready] Add payment tests

    Claim one via Vikunja UI or `mclaude vikunja claim 1247`.

Zero output when inbox is empty or missing - do not clutter sessions
that do not use the Vikunja integration.

Setup in .claude/settings.json:

    {
      "hooks": {
        "SessionStart": [{
          "hooks": [{
            "type": "command",
            "command": "python hooks/vikunja-inbox-show.py"
          }]
        }]
      }
    }
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _find_inbox() -> Path | None:
    """Look for .claude/vikunja-inbox in cwd and up to 3 parents."""
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents[:3]):
        p = candidate / ".claude" / "vikunja-inbox"
        if p.is_dir():
            return p
    return None


def _priority_label(p: int) -> str:
    if p <= 0:
        return "P0"
    return f"P{min(p, 5)}"


def main() -> int:
    inbox = _find_inbox()
    if inbox is None:
        return 0  # no inbox configured for this project, stay silent

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
        priority = int(data.get("priority") or 0)
        entries.append((priority, tid, title, labels))

    if not entries:
        return 0

    # Highest priority first
    entries.sort(key=lambda e: (-e[0], e[1]))

    print(f"[vikunja-inbox] {len(entries)} task(s) pending:")
    for priority, tid, title, labels in entries[:10]:
        label_part = f" [{' '.join(labels)}]" if labels else ""
        print(f"  #{tid} {_priority_label(priority)}{label_part} {title}")
    if len(entries) > 10:
        print(f"  ... and {len(entries) - 10} more")
    print()
    print("  Claim in Vikunja UI, or use mclaude vikunja bridge to take a lock first.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
