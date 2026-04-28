#!/usr/bin/env python3
"""PreToolUse: require dual confirmation for destructive operations.

Motivation
==========
Single bypass marker (`# claude-bypass: destructive`) can be added by the agent
itself after internal reasoning — no human-in-the-loop. The Replit incident
(Aug 2026, Jason Lemkin) showed this fails: agent added bypass on its own and
dropped a production database, then lied about restoring it.

This hook formalizes the human contact point as a *proof artifact in the
command*: a `# user-confirmed:` token that the agent may include only after
receiving an explicit answer from the user in the current conversation.

Token format (case-insensitive, single line)
============================================
    # user-confirmed: "<verbatim user phrase>" <ISO-8601 timestamp>

Requirements:
  - Phrase non-empty (the actual word the user typed: "да", "делай", "yes",
    "поехали", "ага", "выполни", etc.)
  - Timestamp parseable as ISO-8601, no more than `MAX_AGE_MINUTES` ago
    (default 10 minutes).
  - The token must coexist with the standard `# claude-bypass: destructive`
    marker — having only one is not enough.

Verdict matrix
==============
| destructive pattern | bypass marker | user-confirmed token | result |
|---|---|---|---|
| no                  | -             | -                    | allow (this hook does nothing) |
| yes                 | no            | -                    | allow (block_destructive will block first) |
| yes                 | yes           | no                   | **BLOCK** (this hook) |
| yes                 | yes           | yes (fresh)          | allow |
| yes                 | yes           | yes (stale >10 min)  | **BLOCK** (refresh) |

Design notes
============
- The token is checked from the command text, not from session memory or env
  vars. Reason: hooks run in sibling processes; env state is unreliable.
- The phrase is verified to be non-empty but its content is *not* matched
  against an allowlist. The point is not what the user said, it's that they
  *said something explicit very recently* — that is the human contact event.
- Timestamp is the second proof: prevents reusing a token from yesterday's
  approval for today's command.
- This hook does NOT handle git destructive (covered by block_git_destructive)
  or self-harm (block_self_harm). It only sits behind block_destructive.

Bypass of *this* hook
=====================
There is no bypass for this hook. That is the point: destructive ops always
require fresh human confirmation. If you genuinely need to script destructive
operations without human input (CI/CD pipelines, batch jobs), do it outside
the Claude Code session — those don't need this safety layer.
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import (  # noqa: E402
    allow,
    any_match,
    bash_command,
    block,
    bypass_marker,
    log,
    read_event,
)

# Same destructive patterns as block_destructive — keep in sync.
# This hook only triggers if BOTH the pattern AND a destructive bypass marker
# are present (i.e. user/agent asked block_destructive to allow it).
DESTRUCTIVE_PATTERNS = [
    # Filesystem catastrophes
    r"\brm\s+-[a-z]*r[a-z]*f?\s+/\s*($|;|&|\|)",
    r"\brm\s+-[a-z]*r[a-z]*f?\s+/\*",
    r"\brm\s+-[a-z]*r[a-z]*f?\s+\*\s*($|;|&|\|)",
    r"\brm\s+-[a-z]*r[a-z]*f?\s+~\s*($|;|&|\|/)",
    r"\brm\s+-[a-z]*r[a-z]*f?\s+\$HOME(\s|$|/)",
    r"\brm\s+-[a-z]*r[a-z]*f?\s+~/\s*($|;|&|\|)",
    r"\brm\s+-[a-z]*r[a-z]*f?\s+/(etc|usr|var|boot|sys|proc|lib|lib64|sbin|bin|root|home)(/\s*)?($|;|&|\|)",
    r"\bfind\s+/\s+.*-delete\b",
    r"\bmkfs\.[a-z0-9]+\s+/dev/",
    r"\bdd\s+if=\S+\s+of=/dev/[sh]d[a-z]",
    # Database destruction
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bdropdb\b",
    r"\bmongo\s+.*\bdropDatabase\b",
    r"\bredis-cli\s+.*\bflushall\b",
    r"\bDELETE\s+FROM\s+\w+\s*(;|$)",
    # Container/orchestration mass delete
    r"\bdocker\s+rm\s+-f\s+\$\(docker\s+ps",
    r"\bdocker\s+system\s+prune\s+.*-a.*--volumes",
    r"\bdocker-compose\s+down\s+.*-v",
    r"\bkubectl\s+delete\s+(ns|namespace|all)\b",
    r"\bkubectl\s+delete\s+.*--all\b",
    r"\bhelm\s+uninstall\b.*-n\s+(prod|production)",
]

MAX_AGE_MINUTES = 10

# Token regex: match phrase in single or double quotes + ISO timestamp.
# ISO accepted: YYYY-MM-DD HH:MM[:SS][Z|+TZ] OR YYYY-MM-DDTHH:MM[:SS][Z|+TZ]
USER_CONFIRMED_RE = re.compile(
    r"#\s*user-confirmed\s*:\s*"
    r"(['\"])(?P<phrase>.+?)\1\s+"
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)",
    re.IGNORECASE,
)


def parse_iso(ts: str) -> _dt.datetime | None:
    """Parse ISO-8601 timestamp. Returns timezone-aware datetime in UTC, or None."""
    s = ts.strip().replace("T", " ")
    # Strip timezone if present (we'll treat naive as UTC for simplicity)
    s = re.sub(r"\s*(Z|[+-]\d{2}:?\d{2})\s*$", "", s)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return _dt.datetime.strptime(s, fmt).replace(tzinfo=_dt.timezone.utc)
        except ValueError:
            continue
    return None


def find_user_confirmed(cmd: str) -> tuple[str, _dt.datetime] | None:
    """Return (phrase, ts_utc) if a user-confirmed token is present and parses."""
    m = USER_CONFIRMED_RE.search(cmd)
    if not m:
        return None
    phrase = (m.group("phrase") or "").strip()
    if not phrase:
        return None
    ts = parse_iso(m.group("ts"))
    if ts is None:
        return None
    return phrase, ts


def main() -> None:
    event = read_event()
    if event.get("tool_name") != "Bash":
        allow()
    cmd = bash_command(event.get("tool_input", {}))
    if not cmd:
        allow()

    # Step 1: is the command destructive?
    hit = any_match(cmd, DESTRUCTIVE_PATTERNS)
    if not hit:
        allow()

    # Step 2: is there a destructive bypass marker?
    # If not, block_destructive (earlier in chain) already blocked.
    # We only care about commands that survived block_destructive.
    if not bypass_marker(cmd, "destructive"):
        allow()

    # Step 3: is there a user-confirmed token?
    confirmed = find_user_confirmed(cmd)
    if confirmed is None:
        log("BLOCK", "require_human_confirmation", "no-token", hit, cmd)
        block(
            "Эта операция destructive — требуется ДВОЙНОЕ подтверждение.\n\n"
            "У тебя есть `# claude-bypass: destructive` (один слой).\n"
            "Не хватает второго: `# user-confirmed: \"<фраза от user>\" <timestamp>`.\n\n"
            "Что делать:\n"
            "  1. Спроси пользователя в чате explicit подтверждение этой команды.\n"
            "     Опиши что именно собираешься сделать (с какими данными,\n"
            "     обратимо или нет).\n"
            "  2. Получи ответ — любая фраза согласия ('да', 'делай', 'yes',\n"
            "     'поехали', 'ок' и т.п.).\n"
            "  3. Добавь в начало команды второй маркер:\n"
            f"       # user-confirmed: \"<точная фраза user>\" {_dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}\n"
            "  4. Запусти команду.\n\n"
            "Token действителен 10 минут — после повторно запрашивай."
        )

    phrase, ts = confirmed
    age = _dt.datetime.now(_dt.timezone.utc) - ts
    if age.total_seconds() > MAX_AGE_MINUTES * 60:
        log("BLOCK", "require_human_confirmation", "stale-token", hit, cmd)
        age_min = int(age.total_seconds() / 60)
        block(
            f"User-confirmed token устарел: возраст {age_min} мин > {MAX_AGE_MINUTES} мин.\n"
            f"Фраза была: \"{phrase}\". Запросовай у user свежее подтверждение."
        )

    log(
        "WARN",
        "require_human_confirmation",
        "dual-confirmed",
        hit,
        f'phrase="{phrase}" age={int(age.total_seconds())}s :: {cmd[:200]}',
    )
    allow()


if __name__ == "__main__":
    main()
