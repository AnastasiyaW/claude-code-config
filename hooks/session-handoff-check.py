#!/usr/bin/env python3
"""SessionStart hook: check for handoffs from previous sessions.

Runs at the start of every Claude Code session. If recent handoff files
exist, prints them so the agent sees them and can offer to continue.

Supports both old (.claude/HANDOFF.md) and new (.claude/handoffs/*.md) formats.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/session-handoff-check.py",
        "statusMessage": "Checking for handoffs..."
      }]
    }]
  }
}
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# How many recent handoffs to show (by mtime)
MAX_HANDOFFS = 3
# Only show handoffs newer than this (hours)
MAX_AGE_HOURS = 168  # 7 days


def main() -> int:
    cwd = Path.cwd()
    claude_dir = cwd / ".claude"

    # Reset per-session markers (so Stop hook can remind again this session)
    if claude_dir.exists():
        for marker in (".handoff-reminded", ".session-start"):
            m = claude_dir / marker
            if m.exists():
                m.unlink()
        # Re-create session-start marker with current time
        (claude_dir / ".session-start").touch()

    lines: list[str] = []

    # Check for handoffs - new multi-session format first
    handoffs_dir = claude_dir / "handoffs"
    handoff_old = claude_dir / "HANDOFF.md"
    found_handoffs: list[tuple[float, Path]] = []

    now = time.time()

    if handoffs_dir.exists():
        for p in handoffs_dir.glob("*.md"):
            if p.name == "INDEX.md":
                continue
            age_hours = (now - p.stat().st_mtime) / 3600
            if age_hours <= MAX_AGE_HOURS:
                found_handoffs.append((p.stat().st_mtime, p))

    # Fallback: old single HANDOFF.md
    if not found_handoffs and handoff_old.exists():
        age_hours = (now - handoff_old.stat().st_mtime) / 3600
        if age_hours <= MAX_AGE_HOURS:
            found_handoffs.append((handoff_old.stat().st_mtime, handoff_old))

    if found_handoffs:
        # Sort by mtime descending (newest first), take top N
        found_handoffs.sort(key=lambda x: x[0], reverse=True)
        recent = found_handoffs[:MAX_HANDOFFS]

        lines.append("=" * 60)
        lines.append(
            f"SESSION HANDOFF(S) - {len(found_handoffs)} found, "
            f"showing {len(recent)} most recent"
        )
        lines.append("=" * 60)

        for mtime, path in recent:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines.append(f"\n--- {path.name} ---")
            lines.append(content)

        lines.append("=" * 60)
        lines.append("")
        lines.append(
            "INSTRUCTION: List the handoff(s) briefly to the user "
            "(timestamp, session ID, topic). Ask if they want to continue "
            "one of them or start fresh."
        )
        lines.append("")

    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
