#!/usr/bin/env python3
"""PostToolUse: detect API keys in tool output.

Runs after Bash / Read / any tool that produces output. Scans the output
for well-known API key patterns. Cannot retroactively block (tool already
ran), but emits a loud warning to stderr so the user sees the leak.

Key patterns recognized:
 - Anthropic: sk-ant-*
 - OpenAI: sk-*
 - GitHub PAT: ghp_*, gho_*, ghu_*, ghs_*, ghr_*
 - AWS access key: AKIA[0-9A-Z]{16}
 - AWS secret key: 40-char base64-like after aws_secret_access_key
 - Stripe: sk_live_*, sk_test_*, pk_live_*, pk_test_*
 - Slack: xoxb-*, xoxp-*, xoxa-*, xoxr-*
 - Google: AIza[0-9A-Za-z_-]{35}
 - Private keys: -----BEGIN * PRIVATE KEY-----
 - JWT: eyJ*.eyJ*.* (three base64url segments)

This is a detective control, not preventive. Use alongside block_secrets.py
which is preventive. If this fires, secret was exposed in tool output and
is likely in context. Advise rotation.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import log, read_event  # noqa: E402

# (label, regex) pairs. Ordered by specificity (most specific first).
PATTERNS = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9\-_]{32,}")),
    ("OpenAI API key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("GitHub PAT", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("GitHub fine-grained", re.compile(r"github_pat_[A-Za-z0-9_]{80,}")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("AWS secret key",
     re.compile(r"aws[_\-\s]*secret[_\-\s]*access[_\-\s]*key[\"'\s=:]+([A-Za-z0-9/+=]{40})",
                re.IGNORECASE)),
    ("Stripe live key", re.compile(r"\b(?:sk|rk|pk)_live_[0-9a-zA-Z]{24,}")),
    ("Stripe test key", re.compile(r"\b(?:sk|rk|pk)_test_[0-9a-zA-Z]{24,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Private key block",
     re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----")),
    ("JWT token",
     re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("Generic bearer token",
     re.compile(r"\b[Bb]earer\s+[A-Za-z0-9_\-\.=]{40,}")),
]


def extract_output(event: dict) -> str:
    """Pull the tool's output from the PostToolUse event.

    Event shape varies by tool; we try common keys.
    """
    response = event.get("tool_response", {})
    if isinstance(response, str):
        return response
    if not isinstance(response, dict):
        return ""
    # Most tools put text here
    for key in ("stdout", "output", "content", "text", "result"):
        v = response.get(key)
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return "\n".join(str(x) for x in v)
    # Fallback - serialize entire response
    try:
        return json.dumps(response, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(response)


def redact_match(label: str, snippet: str) -> str:
    """Show first 8 chars + asterisks + last 4 so user sees what to rotate."""
    if len(snippet) <= 12:
        return f"[{label}] {'*' * len(snippet)}"
    return f"[{label}] {snippet[:8]}...{snippet[-4:]}"


def main() -> None:
    event = read_event()
    tool_name = event.get("tool_name", "")
    output = extract_output(event)
    if not output:
        sys.exit(0)

    hits: list[tuple[str, str]] = []
    for label, pat in PATTERNS:
        for m in pat.finditer(output):
            hits.append((label, m.group(0)))
            if len(hits) >= 5:  # don't spam, cap at 5 findings
                break
        if len(hits) >= 5:
            break

    if not hits:
        sys.exit(0)

    # Log each finding
    for label, snippet in hits:
        log("ALERT", "detect_api_key_leak", "found", label,
            f"{tool_name}: {snippet[:40]}")

    # Emit loud warning to stderr - user will see this
    lines = [
        "",
        "=" * 70,
        "[api-key-leak] WARNING: tool output contains what looks like API keys",
        "=" * 70,
        f"Tool: {tool_name}",
        f"Findings: {len(hits)}",
    ]
    for label, snippet in hits[:5]:
        lines.append(f"  {redact_match(label, snippet)}")
    lines.extend([
        "",
        "Action items:",
        "  1) The secret is now in Claude Code context. Consider the session compromised",
        "  2) Rotate the exposed key(s) in the respective service",
        "  3) Check git history / log files for the same pattern",
        "  4) If committed recently: force-push after BFG Repo-Cleaner rewrite",
        "=" * 70,
        "",
    ])
    sys.stderr.write("\n".join(lines))
    sys.exit(0)


if __name__ == "__main__":
    main()
