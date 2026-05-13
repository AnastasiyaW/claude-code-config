#!/usr/bin/env python3
"""PreToolUse: block git commits and gh PR/issue commands that carry
Claude/Anthropic attribution footers.

Why this exists
---------------
Claude Code's default system prompt instructs the assistant to add
`Co-Authored-By: Claude <noreply@anthropic.com>` to commits and
"🤖 Generated with [Claude Code]" to PR descriptions. Two problems:

  1. **Harness-detection surface.** Issue #53262 (HERMES.md) showed that
     Claude Code's harness-detection logic pattern-matches strings pulled
     from git status into the system prompt — a match can silently switch
     billing from your Pro/Max subscription to pay-as-you-go API charges.
     A Co-Authored-By footer in git history is the same class of input.
     Minimising AI-related fingerprints in commit metadata reduces the
     surface area for similar false-positives in future updates.

  2. **Footprint pollution.** `git blame`, ML training datasets, audit
     logs, and GitHub Insights stats all carry these footers forward
     forever. For commercial / B2B work the trail is usually unwanted.

This rule OVERRIDEs the default Claude Code instruction. Because rules
declared in `~/.claude/CLAUDE.md` (and project CLAUDE.md) have higher
priority than the base system prompt, the assistant respects this hook
without needing the upstream prompt to change.

Triggers
--------
The hook only inspects Bash commands that touch git/GitHub:
  - git commit / git commit --amend
  - gh pr create | edit | comment
  - gh pr merge (squash-merge bodies may carry attribution)
  - gh issue create | comment

All other Bash commands pass through.

Bypass
------
For the rare case where attribution is intentional (e.g. a maintainer
who explicitly wants to credit the tool in their personal repo):

    # claude-bypass: attribution
    git commit -m "..."

Or environment variable: `CLAUDE_ALLOW_ATTRIBUTION=1`.

Related
-------
- See `rules/safety-billing.md` for the HERMES.md / ANTHROPIC_API_KEY
  background.
- See `rules/no-claude-attribution.md` for the full policy and a
  project-level pre-commit hook template.
- Pair this PreToolUse hook with `pre-push-claude-attribution.py`
  (git-level) for defence-in-depth: this catches commits before they
  are made, the pre-push hook catches anything that slipped through
  before it reaches the remote.
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
    bypass,
    log,
    read_event,
)

# Bash commands that produce git/GitHub artifacts and so are worth
# inspecting. Other commands pass through untouched.
GIT_TRIGGER_PATTERNS = [
    r"\bgit\s+commit\b",
    r"\bgit\s+commit\s+--amend\b",
    r"\bgh\s+(pr|issue)\s+(create|edit|comment)\b",
    r"\bgh\s+pr\s+merge\b",
]

# Forbidden attribution strings. Case-insensitive matching.
ATTRIBUTION_PATTERNS = [
    r"Co-Authored-By:\s*Claude\b",
    r"Co-Authored-By:\s*[Aa]nthropic\b",
    r"Co-Authored-By:[^,\n]*?<noreply@anthropic\.com>",
    r"\bnoreply@anthropic\.com\b",
    r"🤖\s+Generated\s+with\s+(\[?Claude\s+Code\]?|claude\.ai)",
    r"Generated\s+with\s+claude\.ai/code",
    r"Generated\s+with\s+Anthropic",
    r"Authored\s+by\s+Claude\b",
    r"Made\s+with\s+Claude\b",
]


def is_git_attribution_context(command: str) -> bool:
    for pat in GIT_TRIGGER_PATTERNS:
        if re.search(pat, command, re.IGNORECASE):
            return True
    return False


def find_attribution(command: str) -> str | None:
    for pat in ATTRIBUTION_PATTERNS:
        m = re.search(pat, command, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def main() -> None:
    event = read_event()
    if event.get("tool_name", "") != "Bash":
        allow()

    command = bash_command(event.get("tool_input", {}))
    if not command:
        allow()

    if not is_git_attribution_context(command):
        allow()

    hit = find_attribution(command)
    if not hit:
        allow()

    if bypass("attribution", command, env_name="CLAUDE_ALLOW_ATTRIBUTION"):
        log("WARN", "claude-attribution-guard", "bypass", hit, command[:120])
        allow()

    log("BLOCK", "claude-attribution-guard", "deny", hit, command[:120])
    block(
        "Forbidden Claude/Anthropic attribution in a git or GitHub command.\n"
        f"Match: {hit!r}\n\n"
        "Policy (see rules/no-claude-attribution.md) forbids:\n"
        "  - Co-Authored-By: Claude / Anthropic / AI\n"
        "  - <noreply@anthropic.com>\n"
        "  - 🤖 Generated with Claude Code / Anthropic\n"
        "  - Any AI-authorship footer in commits, PRs, issues, or merge bodies.\n\n"
        "Two reasons:\n"
        "  1. Harness-detection regexes (see Issue #53262 HERMES.md case)\n"
        "     can match attribution strings and silently flip billing\n"
        "     from your subscription to pay-as-you-go API charges.\n"
        "  2. Footprint pollution in git blame, ML training data, audit logs.\n\n"
        "What to do:\n"
        "  - Drop the footer line from this commit message / PR body / issue body.\n"
        "  - Mentions of Claude as *content* are fine (repo name, file name,\n"
        "    bug report about Claude Code itself) — only attribution is blocked.\n"
        "  - For an intentional exception: add the bypass marker\n"
        "      # claude-bypass: attribution\n"
        "    or export CLAUDE_ALLOW_ATTRIBUTION=1 for the session."
    )


if __name__ == "__main__":
    main()
