#!/usr/bin/env python3
"""PreToolUse: block Bash commands containing raw non-ASCII (Cyrillic) on Windows.

Bash on Windows (MSYS/Git-Bash) passes non-ASCII bytes through the console codepage
(cp1251/cp866), not UTF-8 -> mojibake in paths/args/output. Recurring real failures:
  - Cyrillic file path truncated at the first space / garbled (FileNotFoundError 'D:\\датасеты')
  - git commit -m "кириллица" stored as mojibake
  - python script.py "путь с пробелами" -> argv mangled
  - curl --data with Cyrillic body -> '?????' stored

Fix: use the PowerShell tool (handles Unicode natively, -Encoding utf8), or write the
text/path to a UTF-8 file and pass the file. Bypass when genuinely safe (e.g. a single-
quoted UTF-8 heredoc written to a file): marker '# claude-bypass: cyrillic' or
CLAUDE_ALLOW_CYRILLIC=1.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import (  # noqa: E402
    allow,
    bash_command,
    block,
    bypass,
    log,
    read_event,
)


def main() -> None:
    event = read_event()
    if event.get("tool_name") != "Bash":
        allow()

    cmd = bash_command(event.get("tool_input", {}))
    if not cmd:
        allow()

    # raw non-ASCII chars = the codepage-boundary risk on Windows Bash
    nonascii = sorted({c for c in cmd if ord(c) > 127})
    if not nonascii:
        allow()

    if bypass("cyrillic", cmd):
        log("WARN", "cyrillic_bash_guard", "bypass", "".join(nonascii)[:20], cmd)
        allow()

    sample = "".join(nonascii)[:30]
    log("BLOCK", "cyrillic_bash_guard", "deny", sample, cmd)
    block(
        f"Bash на Windows портит не-ASCII через кодировку консоли (cp1251/cp866, не UTF-8).\n"
        f"В команде есть не-ASCII символы: {sample}\n"
        "Кириллица в путях/аргументах/git-сообщениях через Bash -> mojibake или обрезка пути\n"
        "(напр. 'D:\\датасеты в разметке\\...' обрежется до 'D:\\датасеты').\n"
        "Что делать:\n"
        "  - используй инструмент PowerShell (держит Unicode нативно; Out-File -Encoding utf8);\n"
        "  - либо запиши текст/путь в UTF-8 файл и передай файлом (Write tool);\n"
        "  - путь с пробелами+кириллицей -> Start-Process с закавыченным аргументом.\n"
        "Если точно безопасно (одинарные кавычки в UTF-8 heredoc в файл):\n"
        "  # claude-bypass: cyrillic   или   CLAUDE_ALLOW_CYRILLIC=1"
    )


if __name__ == "__main__":
    main()
