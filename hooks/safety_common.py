"""Shared safety hook utilities.

Reads PreToolUse JSON from stdin, exposes helpers for logging and blocking.
Exit conventions:
  - exit 0 + empty stdout: allow (silent pass-through)
  - exit 0 + JSON {"decision": "block", "reason": "..."} on stdout: block
  - exit 2 + message on stderr: block with user-visible reason

See docs: https://docs.anthropic.com/en/docs/claude-code/hooks
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

# Windows default stdout is cp1252 which chokes on Cyrillic in block reasons.
# Reconfigure to utf-8 before any print. No-op on platforms that already use utf-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

LOG_PATH = Path.home() / ".claude" / "logs" / "safety.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def read_event() -> dict:
    """Parse PreToolUse event from stdin. Returns empty dict on failure."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


def log(level: str, hook: str, verdict: str, pattern: str, target: str) -> None:
    """Append an audit line. One JSONL record per event."""
    try:
        record = {
            "ts": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": level,
            "hook": hook,
            "verdict": verdict,
            "pattern": pattern,
            "target": target[:400],
        }
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def block(reason: str) -> None:
    """Emit a structured block verdict and exit."""
    msg = {"decision": "block", "reason": reason}
    print(json.dumps(msg, ensure_ascii=False))
    sys.exit(0)


def allow() -> None:
    """Pass-through: no output, exit 0."""
    sys.exit(0)


def bypass_env(name: str) -> bool:
    """Check CLAUDE_ALLOW_* override. Accepts 1/true/yes."""
    val = os.environ.get(name, "").strip().lower()
    return val in {"1", "true", "yes", "on"}


def bash_command(tool_input: dict) -> str:
    """Extract command string from Bash tool input."""
    return str(tool_input.get("command", ""))


def file_path(tool_input: dict) -> str:
    """Extract file path from Read/Edit/Write tool input."""
    return str(tool_input.get("file_path", ""))


def any_match(text: str, patterns: list[str]) -> str | None:
    """Return the first matching regex (string form) or None. Case-insensitive."""
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return pat
    return None
