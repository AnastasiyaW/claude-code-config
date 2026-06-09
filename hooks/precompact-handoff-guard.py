#!/usr/bin/env python3
"""PreCompact hook: ensure a handoff exists across the compaction boundary.

Fires right before context compaction (Claude Code `PreCompact` event),
which is exactly the "context overflow" moment. Auto-compaction summarizes
the conversation and discards raw detail — if no fresh handoff was written,
nuanced state (paths, decisions, what-did-NOT-work) is lost.

What it does:
  - On `auto` (and `manual`) compaction, check for a FRESH handoff in
    <cwd>/.claude/handoffs/*.md (written within HANDOFF_FRESH_MINUTES).
  - If a fresh handoff exists -> print a short OK note, exit 0.
  - If NOT -> drop a marker file <cwd>/.claude/.precompact-handoff-needed
    AND print a strong reminder to stdout (added to the compaction context),
    so the post-compact turn writes a handoff immediately.

The marker is surfaced again by session-handoff-check.py at the next
SessionStart (which also runs with source=compact right after auto-compact),
giving belt-and-suspenders coverage regardless of how a given Claude Code
version forwards PreCompact stdout.

Non-blocking by design: compaction cannot/should not be vetoed — the goal is
to guarantee the handoff gets written around it, not to stop it.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/precompact-handoff-guard.py",
        "statusMessage": "Ensuring handoff before context compaction..."
      }]
    }]
  }
}
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# A handoff written within this window counts as "fresh" for this compaction.
HANDOFF_FRESH_MINUTES = 25
MARKER_NAME = ".precompact-handoff-needed"


def read_event() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def newest_handoff_age_minutes(handoffs_dir: Path, handoff_old: Path) -> float | None:
    """Minutes since the most recent handoff was written, or None if none."""
    now = time.time()
    best: float | None = None
    if handoffs_dir.exists():
        for p in handoffs_dir.glob("*.md"):
            if p.name == "INDEX.md":
                continue
            age = (now - p.stat().st_mtime) / 60
            if best is None or age < best:
                best = age
    if handoff_old.exists():
        age = (now - handoff_old.stat().st_mtime) / 60
        if best is None or age < best:
            best = age
    return best


def main() -> int:
    event = read_event()
    trigger = str(event.get("trigger", "auto"))

    cwd = Path(event.get("cwd") or ".").expanduser()
    claude_dir = cwd / ".claude"
    if not claude_dir.exists():
        return 0  # not a Claude Code project

    handoffs_dir = claude_dir / "handoffs"
    handoff_old = claude_dir / "HANDOFF.md"
    marker = claude_dir / MARKER_NAME

    age = newest_handoff_age_minutes(handoffs_dir, handoff_old)
    fresh = age is not None and age < HANDOFF_FRESH_MINUTES

    if fresh:
        # Good — a handoff already captures current state. Clear any stale marker.
        try:
            if marker.exists():
                marker.unlink()
        except Exception:
            pass
        print(
            f"[precompact] OK: fresh handoff exists ({int(age)} min old). "
            f"State preserved across compaction."
        )
        return 0

    # No fresh handoff at the overflow moment — record it and shout.
    try:
        marker.write_text(
            json.dumps(
                {
                    "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "trigger": trigger,
                    "newest_handoff_min": None if age is None else int(age),
                },
            ),
            encoding="utf-8",
        )
    except Exception:
        pass

    print(
        "=" * 60 + "\n"
        "[precompact] CONTEXT IS BEING COMPACTED — NO FRESH HANDOFF.\n"
        + "=" * 60 + "\n"
        f"Trigger: {trigger}. The raw conversation detail is about to be "
        "summarized away.\n"
        "IMMEDIATELY after compaction, before any other work, write a handoff "
        "to .claude/handoffs/YYYY-MM-DD_HH-MM_<session-short-id>.md "
        "(format: .claude/rules/session-handoff.md; <=1500 tokens; goal / done / "
        "what did NOT work / current state / key decisions / single next step) "
        "and append one line to .claude/handoffs/INDEX.md. "
        "This is the near-overflow exception in finish-the-task.md.\n"
        + "=" * 60
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
