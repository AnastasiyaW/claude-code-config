#!/usr/bin/env python3
"""Stop hook: remind to write a handoff when closing a long session.

Checks if the session has been running long enough to warrant a handoff.
Prints a reminder message that the agent sees before closing.

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

import os
import sys
import time
from pathlib import Path

# Minimum session duration (seconds) before reminding about handoff
MIN_SESSION_MINUTES = 15


def has_recent_handoff(cwd: str, max_age_minutes: int = 30) -> bool:
    """Check if a handoff file was written recently."""
    handoff_dirs = [
        os.path.join(cwd, ".claude", "handoffs"),
        os.path.join(cwd, ".claude"),
    ]

    now = time.time()

    for hdir in handoff_dirs:
        if not os.path.isdir(hdir):
            continue
        for f in os.listdir(hdir):
            if "handoff" in f.lower() and f.endswith(".md"):
                fpath = os.path.join(hdir, f)
                mtime = os.path.getmtime(fpath)
                age_minutes = (now - mtime) / 60
                if age_minutes < max_age_minutes:
                    return True

    return False


def main():
    cwd = os.getcwd()

    # Check session start time from environment or estimate
    # Claude Code doesn't expose session start time, so we check
    # if there's been significant work (proxy: many recent file changes)
    recent_changes = 0
    cutoff = time.time() - (MIN_SESSION_MINUTES * 60)

    for root, dirs, files in os.walk(cwd):
        # Skip hidden dirs and node_modules
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for f in files:
            fpath = os.path.join(root, f)
            try:
                if os.path.getmtime(fpath) > cutoff:
                    recent_changes += 1
            except OSError:
                pass
        if recent_changes > 10:
            break

    if recent_changes <= 5:
        # Short session, no reminder needed
        return

    if has_recent_handoff(cwd):
        # Already has a fresh handoff
        return

    print("[session-handoff] This looks like a substantial session.")
    print("Consider writing a handoff before closing:")
    print('  Say "prepare handoff" or "write handoff"')
    print("  This saves context for your next session.")


if __name__ == "__main__":
    main()
