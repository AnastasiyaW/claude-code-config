#!/usr/bin/env python3
"""PreToolUse: prevent reading or exposing secret files.

Blocks Read/Edit/Write on .env, *.key, *.pem, ~/.ssh/id_*, ~/.secrets/*.
Blocks Bash reads (cat/less/head/tail/grep) on same paths.
Bypass: CLAUDE_ALLOW_SECRETS=1.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import (  # noqa: E402
    allow,
    bash_command,
    block,
    bypass_env,
    file_path,
    log,
    read_event,
)

SECRET_PATH_REGEX = re.compile(
    r"(?:^|/|\\)("
    r"\.env(?:\.[a-z0-9]+)?"          # .env, .env.local, .env.production
    r"|\.envrc"
    r"|[^/\\]*\.key"                    # *.key (file tail)
    r"|[^/\\]*\.pem"                    # *.pem
    r"|id_(?:rsa|ed25519|ecdsa|dsa)(?:\.pub)?"  # ssh keys
    r"|credentials(?:\.json)?"
    r"|secrets?\.(?:json|yaml|yml|toml)"
    r")(?:$|/|\\)",
    re.IGNORECASE,
)

SECRET_DIR_REGEX = re.compile(
    r"(?:^|/|\\)(\.secrets?|\.aws|\.ssh)(?:$|/|\\)",
    re.IGNORECASE,
)

BASH_READ_VERBS = re.compile(
    r"\b(cat|less|more|head|tail|grep|rg|ripgrep|bat|xxd|hexdump|source|\.)\s+\S",
    re.IGNORECASE,
)


def path_is_secret(path: str) -> str | None:
    if not path:
        return None
    m = SECRET_PATH_REGEX.search(path)
    if m:
        return m.group(1)
    m = SECRET_DIR_REGEX.search(path)
    if m:
        return m.group(1) + "/"
    return None


def bash_touches_secret(cmd: str) -> str | None:
    """Detect reads/prints of secret-like paths inside a Bash command."""
    if not cmd:
        return None
    # Split on common separators to test each token that looks path-ish.
    tokens = re.split(r"[\s;&|<>()`]+", cmd)
    for tok in tokens:
        tok = tok.strip("\"'")
        if not tok or tok.startswith("-"):
            continue
        hit = path_is_secret(tok)
        if hit:
            # Only block if the command seems to read/print, not edit via protected editor
            if BASH_READ_VERBS.search(cmd) or "echo" in cmd.lower() or "printenv" in cmd.lower():
                return hit
            # Reading via redirection like `< .env` also leaks
            if re.search(r"<\s*\S*" + re.escape(tok), cmd):
                return hit
    return None


def main() -> None:
    event = read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    hit: str | None = None
    target = ""

    if tool_name in {"Read", "Edit", "Write", "NotebookEdit"}:
        target = file_path(tool_input)
        hit = path_is_secret(target)
    elif tool_name == "Bash":
        target = bash_command(tool_input)
        hit = bash_touches_secret(target)
    elif tool_name == "Grep":
        # Grep takes a path; both path and pattern can touch secrets
        gpath = str(tool_input.get("path", ""))
        target = gpath
        hit = path_is_secret(gpath)

    if not hit:
        allow()

    if bypass_env("CLAUDE_ALLOW_SECRETS"):
        log("WARN", "block_secrets", "bypass", hit, target)
        allow()

    log("BLOCK", "block_secrets", "deny", hit, target)
    block(
        f"Secret file access blocked: {hit!r}.\n"
        "Причина: секреты (.env, ключи, ~/.ssh/id_*, ~/.secrets/*) не читать без явной\n"
        "пользовательской просьбы. Даже чтение для 'проверить' рискует утечкой в логи/контекст.\n"
        "Если действительно нужно:\n"
        "  1) подтверди у пользователя что именно и зачем\n"
        "  2) запусти команду с CLAUDE_ALLOW_SECRETS=1\n"
        "  3) после чтения не печатай содержимое в output"
    )


if __name__ == "__main__":
    main()
