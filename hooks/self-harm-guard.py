#!/usr/bin/env python3
"""PreToolUse: block commands that can cut off the agent itself.

Covers:
 - edits to /etc/ssh/sshd_config and AuthorizedKeysFile
 - systemctl restart/stop sshd and sshd daemon kill
 - pkill/killall across Claude Code's runtime (node/bun/python) - harakiri
 - iptables/ufw rules that could drop agent's own connectivity

Bypass: CLAUDE_ALLOW_SELF_HARM=1.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import (  # noqa: E402
    allow,
    any_match,
    bash_command,
    block,
    bypass_env,
    file_path,
    log,
    read_event,
)

SSH_CONFIG_PATHS = [
    r"/etc/ssh/sshd_config",
    r"/etc/ssh/sshd_config\.d/",
    r"~/.ssh/authorized_keys$",
    r"/root/.ssh/authorized_keys$",
]

BASH_PATTERNS = [
    # SSH daemon lifecycle
    r"\bsystemctl\s+(restart|stop|disable|mask)\s+sshd?\b",
    r"\bservice\s+sshd?\s+(restart|stop)\b",
    r"\b/etc/init\.d/sshd?\s+(restart|stop)\b",
    r"\bpkill\s+.*sshd\b",
    r"\bkill(all)?\s+.*sshd\b",

    # Self-harakiri: Claude Code runs on node/bun
    r"\bkillall\s+(node|bun|python|claude)\b",
    r"\bpkill\s+-f\s+.*(\bclaude\b|@anthropic|claude-code)",
    r"\bpkill\s+.*\b(node|bun)\b(?!.*--parent)",

    # Firewall self-block
    r"\biptables\s+.*-A\s+(INPUT|OUTPUT).*-j\s+DROP(?!.*--sport)",
    r"\bufw\s+(deny|reject)\s+(incoming|outgoing|all)",
    r"\bufw\s+default\s+deny\s+(incoming|outgoing)",

    # sshd_config edits via sed (bypasses Edit tool)
    r"\bsed\s+-i\s+.*\b(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|Port)\s+.*/etc/ssh/sshd_config",
    r">\s*/etc/ssh/sshd_config",
    r">>\s*/etc/ssh/authorized_keys",  # append alone is not always bad but worth flagging

    # Reboot without handoff
    r"\b(shutdown|reboot|halt|poweroff)\s+(-[a-z]*|now)?",
]


def main() -> None:
    event = read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    hit: str | None = None
    target = ""

    if tool_name == "Bash":
        target = bash_command(tool_input)
        hit = any_match(target, BASH_PATTERNS)
    elif tool_name in {"Edit", "Write"}:
        target = file_path(tool_input)
        hit = any_match(target, SSH_CONFIG_PATHS)

    if not hit:
        allow()

    if bypass_env("CLAUDE_ALLOW_SELF_HARM"):
        log("WARN", "block_self_harm", "bypass", hit, target)
        allow()

    log("BLOCK", "block_self_harm", "deny", hit, target)
    block(
        f"Self-harm pattern blocked: /{hit}/.\n"
        "Это команды которые могут:\n"
        "  - отрезать SSH доступ (sshd edits/restart без backup подключения)\n"
        "  - убить сам Claude Code (pkill node/bun/python)\n"
        "  - заблокировать свою сетевую связь (iptables/ufw default deny)\n"
        "  - перезагрузить хост без готового handoff\n"
        "Если нужно:\n"
        "  1) убедись что есть альтернативная сессия / backup путь на хост\n"
        "  2) подтверди у пользователя\n"
        "  3) запусти с CLAUDE_ALLOW_SELF_HARM=1\n"
        "Известный инцидент: fail2ban ban после перезапуска sshd без сохранённого ключа."
    )


if __name__ == "__main__":
    main()
