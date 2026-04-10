#!/usr/bin/env python3
"""Stop hook: remind to write a handoff when closing a long session.

Blocks the agent from ending a turn (via JSON response) if the session
has been running long enough and no fresh handoff exists. Only reminds
once per session to avoid infinite loops.

Supports both old (.claude/HANDOFF.md) and new (.claude/handoffs/*.md) formats.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/session-handoff-reminder.py",
        "statusMessage": "Checking handoff state..."
      }]
    }]
  }
}
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Tunables
SESSION_MIN_MINUTES = 15          # don't remind on short sessions
HANDOFF_STALE_MINUTES = 30        # consider stale after this
REMINDER_MARKER_NAME = ".handoff-reminded"


def session_age_minutes(marker: Path) -> float:
    """Estimate session age by looking at SessionStart marker mtime."""
    if marker.exists():
        age_sec = time.time() - marker.stat().st_mtime
        return age_sec / 60
    return 0


def main() -> int:
    cwd = Path.cwd()
    claude_dir = cwd / ".claude"
    if not claude_dir.exists():
        return 0  # not a Claude Code project

    # Support both old (HANDOFF.md) and new (handoffs/*.md) formats
    handoff_old = claude_dir / "HANDOFF.md"
    handoffs_dir = claude_dir / "handoffs"
    reminder = claude_dir / REMINDER_MARKER_NAME
    session_marker = claude_dir / ".session-start"

    # Skip if we already reminded this session
    if reminder.exists():
        return 0

    # Create session marker if not present (first Stop of session)
    if not session_marker.exists():
        session_marker.touch()

    age = session_age_minutes(session_marker)
    if age < SESSION_MIN_MINUTES:
        return 0  # short session, no handoff needed

    # Check if handoff is fresh - either format counts
    fresh = False
    # Old format: single HANDOFF.md
    if handoff_old.exists():
        if (time.time() - handoff_old.stat().st_mtime) / 60 < HANDOFF_STALE_MINUTES:
            fresh = True
    # New format: any .md in handoffs/ (except INDEX.md)
    if not fresh and handoffs_dir.exists():
        for p in handoffs_dir.glob("*.md"):
            if p.name == "INDEX.md":
                continue
            if (time.time() - p.stat().st_mtime) / 60 < HANDOFF_STALE_MINUTES:
                fresh = True
                break
    if fresh:
        return 0  # already recent

    # Mark that we've reminded so we don't loop
    reminder.touch()

    # Block the stop and ask Claude to write handoff
    response = {
        "decision": "block",
        "reason": (
            f"This session has been active for ~{int(age)} minutes and no fresh "
            f"handoff exists. Before ending, please write a handoff file in "
            f".claude/handoffs/ following the format in .claude/rules/session-handoff.md. "
            f"File name: YYYY-MM-DD_HH-MM_<session-short-id>.md. "
            f"Keep it under 1500 tokens. Must include: goal, what was done, "
            f"what did NOT work (with reasons), current state, key decisions, "
            f"single next step. Update .claude/handoffs/INDEX.md (append). "
            f"After writing, you may end the session normally."
        ),
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
