#!/usr/bin/env python3
"""Stop hook: detect behavioral regression phrases in the final assistant message.

Based on the AMD Claude Code regression investigation (issue #42796, April 2026).
The investigator identified five phrase categories that signal a degraded agent:
ownership dodging, permission-seeking, premature stopping, known-limitation
labeling, and session-length excuses. In a healthy period these phrases never
appeared; post-regression they fired 173 times in 17 days.

When a match is found, the hook blocks the Stop event via a JSON response, forcing
the agent to either actually finish the work or explicitly explain the limitation.
This converts behavioral degradation from an invisible drift into a loud signal.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/stop-phrase-guard.py",
        "statusMessage": "Checking for regression phrases..."
      }]
    }]
  }
}

Reference: https://github.com/anthropics/claude-code/issues/42796
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Phrase categories from the AMD investigation. Lowercase-matched against the
# final assistant message. Each entry: (category_name, [patterns]).
# Patterns are regex, case-insensitive, word-boundary aware.
PHRASE_CATEGORIES: list[tuple[str, list[str]]] = [
    (
        "ownership_dodging",
        [
            r"not caused by my changes",
            r"pre[- ]existing (issue|bug|problem)",
            r"this was already (broken|failing)",
            r"existing (issue|bug|problem) (in|with) the code",
            r"not (related to|a result of) my (change|edit)",
        ],
    ),
    (
        "permission_seeking",
        [
            r"should I (continue|proceed|keep going)\??",
            r"want me to keep going\??",
            r"shall I proceed\??",
            r"do you want me to continue\??",
            r"would you like me to proceed\??",
        ],
    ),
    (
        "premature_stopping",
        [
            r"good (stopping|stop) point",
            r"natural checkpoint",
            r"reasonable place to (pause|stop)",
            r"good place to (pause|stop)",
            r"stopping (here|for now)",
        ],
    ),
    (
        "known_limitation",
        [
            r"known limitation",
            r"out of scope",
            r"future work",
            r"left (for|as) (future|follow[- ]up) work",
            r"beyond the scope of this",
        ],
    ),
    (
        "session_length_excuse",
        [
            r"continue in a new session",
            r"(session|context) is (getting (long|full)|filling up|running out)",
            r"(approaching|hitting) (context|the) limit",
            r"pick this up in a fresh session",
        ],
    ),
]

# Suppress false positives: if the agent is explicitly ACKNOWLEDGING the phrase
# as a known anti-pattern (meta-discussion), do not flag. Heuristic: if the
# message mentions "anti-pattern", "regression", "stop-phrase-guard", "#42796",
# etc. near the matched phrase, it is likely meta-discussion.
META_DISCUSSION_MARKERS = [
    "anti-pattern",
    "regression",
    "stop-phrase-guard",
    "#42796",
    "AMD investigation",
    "behavioral tell",
    "reasoning regression",
]


def get_final_assistant_message(transcript_path: str | None) -> str:
    """Read the transcript file and return the last assistant message text.

    The exact transcript location and format is not documented for Stop hooks
    at the time of writing. This function tries the Claude-Code-typical layout
    and falls back gracefully - if it can't find the transcript, return empty
    string (no false positives).
    """
    if not transcript_path:
        return ""
    p = Path(transcript_path)
    if not p.exists():
        return ""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    # Transcript is JSONL, iterate from end to find the last assistant entry
    last_content = ""
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = obj.get("role") or obj.get("message", {}).get("role")
        if role != "assistant":
            continue
        content = obj.get("content") or obj.get("message", {}).get("content")
        if isinstance(content, str):
            last_content = content
        elif isinstance(content, list):
            # Anthropic message format: list of blocks with type/text
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            last_content = "\n".join(parts)
        if last_content:
            break
    return last_content


def scan_phrases(message: str) -> list[tuple[str, str]]:
    """Return list of (category, matched_text) hits in the message."""
    lower = message.lower()
    hits: list[tuple[str, str]] = []
    for category, patterns in PHRASE_CATEGORIES:
        for pat in patterns:
            m = re.search(pat, lower, re.IGNORECASE)
            if not m:
                continue
            # Suppress if this looks like meta-discussion
            start = max(0, m.start() - 200)
            end = min(len(lower), m.end() + 200)
            context = lower[start:end]
            if any(marker.lower() in context for marker in META_DISCUSSION_MARKERS):
                continue
            hits.append((category, m.group(0)))
    return hits


def main() -> int:
    # Read Stop hook input from stdin (JSON with transcript path, session, etc)
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        event = {}

    # Transcript path field varies by Claude Code version; try common names.
    transcript_path = (
        event.get("transcript_path")
        or event.get("transcriptPath")
        or event.get("transcript")
        or os.environ.get("CLAUDE_CODE_TRANSCRIPT_PATH")
    )

    # Marker file to avoid blocking twice in same session
    cwd = Path.cwd()
    marker = cwd / ".claude" / ".stop-phrase-guard-fired"
    if marker.exists():
        return 0

    message = get_final_assistant_message(transcript_path)
    if not message:
        return 0  # no transcript, no-op

    hits = scan_phrases(message)
    if not hits:
        return 0

    # Group hits by category for readable output
    by_cat: dict[str, list[str]] = {}
    for cat, phrase in hits:
        by_cat.setdefault(cat, []).append(phrase)

    details = "; ".join(
        f"{cat}: '{by_cat[cat][0]}'"
        + (f" (+{len(by_cat[cat]) - 1} more)" if len(by_cat[cat]) > 1 else "")
        for cat in by_cat
    )

    # Touch marker so we don't block again this session
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()

    response = {
        "decision": "block",
        "reason": (
            f"Regression phrase guard: the final message contains "
            f"behavioral tells that signal degraded reasoning ({details}). "
            f"Before ending, either (a) actually finish the work, or (b) "
            f"explicitly explain what is blocking and what concrete next "
            f"step is needed. See alternatives/reasoning-regression-debugging.md "
            f"for context. After writing a genuine conclusion, you may end."
        ),
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
