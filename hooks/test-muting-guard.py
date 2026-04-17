#!/usr/bin/env python3
"""PreToolUse: flag test-muting edits before they land.

Watches Edit/Write/NotebookEdit on test files. If the new content adds
a skip/xfail/disable pattern, block with guidance to fix instead of mute.

Why: "muted failing test" is how bugs ship. Pattern from real incidents:
 - adding @pytest.mark.skip to hide a recently broken test
 - .only() left over from debugging - silently runs 1 test of 100
 - it.skip() replacing it() after a merge conflict

Bypass: CLAUDE_ALLOW_TEST_MUTING=1.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import (  # noqa: E402
    allow,
    block,
    bypass,
    log,
    read_event,
)

TEST_PATH_REGEX = re.compile(
    r"(?:^|/|\\)("
    r"tests?|__tests__|spec|specs"
    r")(?:/|\\)"
    r"|"
    r"(?:^|/|\\)[^/\\]*"
    r"(?:_test|_spec|\.test|\.spec)"
    r"\.[a-z]+$",
    re.IGNORECASE,
)

# Regexes that indicate a test is being silenced.
MUTE_PATTERNS = [
    # pytest
    r"@pytest\.mark\.skip\b",
    r"@pytest\.mark\.xfail\b",
    r"pytest\.skip\s*\(",
    # unittest
    r"@unittest\.skip\b",
    r"@unittest\.expectedFailure\b",
    # JS: jest/mocha/vitest
    r"\b(it|test|describe|context)\.skip\s*\(",
    r"\bx(it|test|describe|context)\s*\(",
    r"\.todo\s*\(",
    # JS .only leaves other tests silently skipped in the suite
    r"\b(it|test|describe|context|suite)\.only\s*\(",
    # Java/JUnit
    r"@Ignore\b",
    r"@Disabled\b",
    # Go
    r"\bt\.Skip\s*\(",
    r"\bt\.Skipf\s*\(",
    # Rust
    r"#\[ignore\]",
    # RSpec
    r"\bskip\s+['\"]\w",
    r"\bxdescribe\b|\bxcontext\b|\bxit\b",
    # Generic "return early" muting
    r"^\s*return;?\s*//\s*(skip|todo|fixme|disable)",
]


def is_test_file(path: str) -> bool:
    return bool(TEST_PATH_REGEX.search(path))


def find_added_mute(old: str, new: str) -> str | None:
    """Return the first mute pattern that appears in `new` but not in `old`."""
    if not new:
        return None
    for pat in MUTE_PATTERNS:
        in_new = re.search(pat, new, re.IGNORECASE | re.MULTILINE)
        if not in_new:
            continue
        # For Edit: only flag if pattern wasn't already in old_string
        in_old = re.search(pat, old or "", re.IGNORECASE | re.MULTILINE)
        if not in_old:
            return pat
    return None


def main() -> None:
    event = read_event()
    tool_name = event.get("tool_name", "")
    if tool_name not in {"Edit", "Write", "NotebookEdit"}:
        allow()

    tool_input = event.get("tool_input", {})
    path = str(tool_input.get("file_path", tool_input.get("notebook_path", "")))
    if not is_test_file(path):
        allow()

    if tool_name == "Edit":
        old = str(tool_input.get("old_string", ""))
        new = str(tool_input.get("new_string", ""))
    else:  # Write or NotebookEdit
        old = ""
        new = str(tool_input.get("content", tool_input.get("new_source", "")))

    hit = find_added_mute(old, new)
    if not hit:
        allow()

    if bypass("test-muting", new, env_name="CLAUDE_ALLOW_TEST_MUTING"):
        log("WARN", "block_test_muting", "bypass", hit, path)
        allow()

    log("BLOCK", "block_test_muting", "deny", hit, path)
    block(
        f"Test mute pattern added in {path}: /{hit}/.\n"
        "'Заткнуть падающий тест' - главный способ выпустить баг в прод.\n"
        "Частые реальные инциденты:\n"
        "  - @pytest.mark.skip добавлен чтобы скрыть недавно сломанный тест\n"
        "  - .only() забытый после дебага → suite молча гоняет 1 из 100 тестов\n"
        "  - it.skip() заменил it() после merge conflict\n"
        "Что делать:\n"
        "  1) Чинить тест или код который он проверяет\n"
        "  2) Если тест устарел (testing deprecated feature) - удалить целиком, не mute\n"
        "  3) Если действительно flaky и нет времени чинить - @skip с reason='...' + linked issue\n"
        "  4) Если намеренно и все знают - CLAUDE_ALLOW_TEST_MUTING=1 + коммит-объяснение"
    )


if __name__ == "__main__":
    main()
