#!/usr/bin/env python3
"""PreToolUse hook: warn before destructive commands.

Intercepts Bash tool calls and blocks dangerous patterns:
- rm -rf (recursive force delete)
- git push --force / git push -f
- git reset --hard
- git checkout . / git restore .
- DROP TABLE / DROP DATABASE
- kubectl delete
- docker system prune

Returns {"decision": "block", "reason": "..."} for destructive commands.
Returns nothing (empty) for safe commands.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python path/to/destructive-command-guard.py",
        "statusMessage": "Safety check..."
      }]
    }]
  }
}

The hook receives tool input via stdin as JSON.
"""

import json
import re
import sys

# Patterns that indicate destructive commands
# Each tuple: (compiled regex, human-readable description)
DESTRUCTIVE_PATTERNS = [
    (re.compile(r'\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f'), "Recursive force delete (rm -rf)"),
    (re.compile(r'\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*r'), "Recursive force delete (rm -fr)"),
    (re.compile(r'\bgit\s+push\s+.*--force'), "Force push (git push --force)"),
    (re.compile(r'\bgit\s+push\s+.*-f\b'), "Force push (git push -f)"),
    (re.compile(r'\bgit\s+reset\s+--hard'), "Hard reset (git reset --hard)"),
    (re.compile(r'\bgit\s+checkout\s+\.\s*$'), "Discard all changes (git checkout .)"),
    (re.compile(r'\bgit\s+restore\s+\.\s*$'), "Discard all changes (git restore .)"),
    (re.compile(r'\bgit\s+clean\s+.*-f'), "Force clean untracked files (git clean -f)"),
    (re.compile(r'\bgit\s+branch\s+.*-D\b'), "Force delete branch (git branch -D)"),
    (re.compile(r'\bDROP\s+(TABLE|DATABASE)\b', re.IGNORECASE), "SQL destructive (DROP TABLE/DATABASE)"),
    (re.compile(r'\bTRUNCATE\s+TABLE\b', re.IGNORECASE), "SQL destructive (TRUNCATE TABLE)"),
    (re.compile(r'\bkubectl\s+delete\b'), "Kubernetes delete (kubectl delete)"),
    (re.compile(r'\bdocker\s+system\s+prune'), "Docker system prune"),
    (re.compile(r'\bdocker\s+rm\s+.*-f'), "Docker force remove"),
    (re.compile(r'\bsudo\s+rm\b'), "Elevated delete (sudo rm)"),
    (re.compile(r'\b>\s*/dev/null\s*2>&1\s*&\s*$'), "Background with suppressed output"),
]


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any destructive pattern.

    Returns (is_destructive, reason).
    """
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, description
    return False, ""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Can't parse input, allow by default
        return

    # Extract command from tool input
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return

    is_destructive, reason = check_command(command)

    if is_destructive:
        result = {
            "decision": "block",
            "reason": f"Destructive command detected: {reason}. "
                      f"Command: {command[:100]}... "
                      f"Ask the user for explicit confirmation before proceeding."
        }
        print(json.dumps(result))


if __name__ == "__main__":
    main()
