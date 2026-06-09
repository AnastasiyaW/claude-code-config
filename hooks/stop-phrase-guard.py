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
    (
        "deferral_via_next_step_question",
        [
            # Ending the turn by asking "what next" / offering a menu of options /
            # asking permission, instead of just doing the planned work in order.
            # User directive 2026-06-07: "не откладываем, делаем всё по очереди".
            r"что (дальше|делаем дальше|теперь делаем|по плану дальше)\b",
            r"что (приоритетн|важнее|выбираешь|предпочитаешь)",
            r"что из (этого|них|трёх|двух|перечисленн|предложенн)",
            r"скаж(ешь|и)[^.?!\n]{0,40}(сделаю|продолжу|заведу|подниму|пройд|починю|дам команду|возьмусь)",
            r"хочешь[^.?!\n]{0,40}(сделаю|сделать|продолжу|заведу|подниму|починю|возьмусь)",
            r"по любому из (этих|трёх|двух|них|пунктов)",
            r"\bили (всё ок|отдыхаем|ждём|двигаемся дальше)\b",
            r"what (would you like|next|should i (do|tackle))\b",
            r"\bsay the word\b",
            r"let me know (which|if you|what you)\b",
            r"pick (one|an option|which)\b",
        ],
    ),
    (
        "offer_and_defer",
        [
            # Offering to do remaining work "later / if you say so" instead of doing it NOW.
            # User directive 2026-06-09: "доделывай нормально ... всегда всё доделываем до конца".
            r"осталось( бы)? (доделать|сделать|починить|доводить|закрыть)",
            r"по[- ]хорошему[^.?!\n]{0,80}(скаж|если|можно|надо|стоит|сделать|доделать)",
            r"не срочно[^.?!\n]{0,40}(скаж|сделаю|если|можно|потом)",
            r"могу[^.?!\n]{0,50}если[^.?!\n]{0,30}(скаж|захочешь|нужно|надо)",
            r"если (захочешь|нужно|надо|пожелаешь)[^.?!\n]{0,40}(сделаю|починю|подниму|заведу|могу)",
            r"оставля[ею] (на потом|на будущее|как есть)",
            r"\(не срочно",
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
    "finish-the-task",
    "next-step-guard",
    "deferral_via_next_step",
    "не откладыва",
]

# Strong meta markers: naming THIS guard or its categories means the message is ABOUT the
# hook (documenting it / quoting example trigger phrases), not an actual deferral. Their
# presence ANYWHERE suppresses the whole message — avoids the guard tripping on its own docs.
STRONG_META_MARKERS = [
    "stop-phrase-guard",
    "offer_and_defer",
    "deferral_via_next_step",
    "regression phrase guard",
    "phrase guard",
    "regression phrase",
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
    # Whole-message meta suppression: a message that names the guard/its categories is
    # documenting it, not deferring. (Fixes the guard firing on its own description.)
    if any(sm in lower for sm in STRONG_META_MARKERS):
        return []
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

    # Counter marker: keep enforcing repeated deferrals (up to MAX_FIRES) instead of
    # giving up after the first block — but cap it so a truly unavoidable phrase can't
    # hard-deadlock the session. (User 2026-06-09: "всегда всё доделываем до конца".)
    MAX_FIRES = 3
    cwd = Path.cwd()
    marker = cwd / ".claude" / ".stop-phrase-guard-fired"
    fires = 0
    if marker.exists():
        try:
            fires = int((marker.read_text(encoding="utf-8").strip() or "0"))
        except (ValueError, OSError):
            fires = 0
    if fires >= MAX_FIRES:
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

    # Increment the fire counter (block now; allow up to MAX_FIRES blocks per session)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(fires + 1), encoding="utf-8")

    response = {
        "decision": "block",
        "reason": (
            f"Regression phrase guard: the final message contains "
            f"behavioral tells that signal degraded reasoning ({details}). "
            f"Before ending, either (a) actually finish the work, or (b) "
            f"explicitly explain what is blocking and what concrete next "
            f"step is needed. Per rules/finish-the-task.md: do NOT end by asking "
            f"'что дальше?' or offering a menu of options while planned work "
            f"remains — keep doing it in order; the ONLY legitimate stop is a real "
            f"external blocker (name it explicitly, not as a 'shall I?') or context "
            f"overflow (write a handoff). After a genuine conclusion, you may end."
        ),
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
