#!/usr/bin/env python3
"""PreToolUse hook: block writes that would introduce secrets into tracked files.

Scans Write and Edit tool calls for patterns that look like secrets:
- API keys (sk-*, AKIA*, ghp_*, etc.)
- Passwords in config files
- Private keys
- Connection strings with credentials
- Bearer tokens

Returns {"decision": "block", "reason": "..."} when a secret is detected.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "python path/to/secret-leak-guard.py",
        "statusMessage": "Checking for secrets..."
      }]
    }]
  }
}
"""

import json
import re
import sys

# Secret patterns: (regex, description)
SECRET_PATTERNS = [
    # API keys with known prefixes
    (re.compile(r'\bsk-[a-zA-Z0-9]{20,}'), "OpenAI/Stripe API key (sk-...)"),
    (re.compile(r'\bAKIA[A-Z0-9]{16}'), "AWS Access Key (AKIA...)"),
    (re.compile(r'\bghp_[a-zA-Z0-9]{36}'), "GitHub Personal Access Token (ghp_...)"),
    (re.compile(r'\bgho_[a-zA-Z0-9]{36}'), "GitHub OAuth Token (gho_...)"),
    (re.compile(r'\bghs_[a-zA-Z0-9]{36}'), "GitHub App Token (ghs_...)"),
    (re.compile(r'\bglpat-[a-zA-Z0-9\-]{20,}'), "GitLab Personal Access Token"),
    (re.compile(r'\bnpm_[a-zA-Z0-9]{36}'), "npm token"),
    (re.compile(r'\bpypi-[a-zA-Z0-9]{50,}'), "PyPI token"),
    (re.compile(r'\bxox[bpars]-[a-zA-Z0-9\-]{10,}'), "Slack token"),
    (re.compile(r'\bsq0[a-z]{3}-[a-zA-Z0-9\-]{22,}'), "Square token"),

    # Private keys
    (re.compile(r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----'), "Private key"),
    (re.compile(r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----'), "EC private key"),

    # Generic patterns
    (re.compile(r'(?i)password\s*[=:]\s*["\'][^"\']{8,}["\']'), "Hardcoded password"),
    (re.compile(r'(?i)api[_-]?key\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']'), "Hardcoded API key"),
    (re.compile(r'(?i)secret\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']'), "Hardcoded secret"),
    (re.compile(r'(?i)bearer\s+[a-zA-Z0-9\-_.]{20,}'), "Bearer token"),

    # Connection strings with credentials
    (re.compile(r'://[^:]+:[^@]{8,}@'), "Connection string with embedded password"),
]

# Files where secrets are expected (don't flag these)
ALLOWED_FILES = [
    ".env.example",
    ".env.template",
    ".env.sample",
    "docker-compose.example.yml",
]


def check_for_secrets(content: str) -> list[str]:
    """Check content for secret patterns. Returns list of descriptions."""
    found = []
    for pattern, description in SECRET_PATTERNS:
        if pattern.search(content):
            found.append(description)
    return found


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    tool_input = input_data.get("tool_input", {})
    tool_name = input_data.get("tool_name", "")

    # Get content to check
    content = ""
    file_path = ""

    if tool_name == "Write":
        content = tool_input.get("content", "")
        file_path = tool_input.get("file_path", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
        file_path = tool_input.get("file_path", "")

    if not content:
        return

    # Skip allowed files
    import os
    basename = os.path.basename(file_path)
    if basename in ALLOWED_FILES:
        return

    secrets = check_for_secrets(content)

    if secrets:
        result = {
            "decision": "block",
            "reason": (
                f"Potential secret(s) detected in {file_path}: "
                f"{', '.join(secrets)}. "
                f"Use environment variables or a secrets manager instead. "
                f"If this is intentional (e.g., test fixtures), "
                f"ask the user to confirm."
            )
        }
        print(json.dumps(result))


if __name__ == "__main__":
    main()
