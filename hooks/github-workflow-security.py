#!/usr/bin/env python3
"""
GitHub Actions workflow security reminder.

Triggers on Write/Edit/MultiEdit of files under .github/workflows/*.yml(.yaml)
and prints a security checklist about command injection from untrusted
GitHub event inputs (issue titles, PR bodies, head_ref, commit messages, etc).

Behavior:
- Blocks the first matching edit per (file, session) with exit code 2 so the
  reminder is forced into context.
- Subsequent matches on the same file in the same session are advisory only
  (printed to stderr) — they do NOT block.
- Disable with env var ENABLE_GH_WORKFLOW_SECURITY=0.

Extracted from anthropics/claude-plugins-official security-guidance plugin
(original is plugin's `github_actions_workflow` rule). The rest of that
plugin's patterns (eval/innerHTML/pickle/exec()/etc) are intentionally
NOT included here because the existing ~/.claude/hooks/ already covers
secrets/destructive/injection, and `exec(` would false-positive on
regex.exec() in JS/TS codebases.
"""

import json
import os
import sys
from datetime import datetime

REMINDER = """⚠️  GitHub Actions workflow security checklist

You are editing a GitHub Actions workflow file. Untrusted GitHub event
inputs can lead to command injection when interpolated directly into
run: blocks. Before merging this edit, verify:

1. NO direct ${{ ... }} interpolation of attacker-controllable inputs
   inside `run:` blocks. Examples of attacker-controllable inputs:
     - github.event.issue.title / .body
     - github.event.pull_request.title / .body
     - github.event.comment.body
     - github.event.review.body / .review_comment.body
     - github.event.pages.*.page_name
     - github.event.commits.*.message
     - github.event.head_commit.message
     - github.event.head_commit.author.name / .author.email
     - github.event.commits.*.author.name / .author.email
     - github.event.pull_request.head.ref / .head.label
     - github.event.pull_request.head.repo.default_branch
     - github.head_ref

2. Pass through env: with proper quoting instead:
     env:
       TITLE: ${{ github.event.issue.title }}
     run: echo "$TITLE"

3. Background:
   https://github.blog/security/vulnerability-research/how-to-catch-github-actions-workflow-injections-before-attackers-do/

This is the first edit of this workflow file in the current session — the
hook is blocking once so you read the checklist. Re-run the same Edit/Write
call and it will proceed. Further edits of this file in this session will
print this reminder as advisory only.
"""


def state_file(session_id: str) -> str:
    return os.path.join(
        os.path.expanduser("~/.claude"), "logs",
        f"github_workflow_warnings_{session_id}.json",
    )


def load_shown(session_id: str) -> set:
    p = state_file(session_id)
    if not os.path.exists(p):
        return set()
    try:
        with open(p, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (OSError, json.JSONDecodeError):
        return set()


def save_shown(session_id: str, shown: set) -> None:
    p = state_file(session_id)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(sorted(shown), f)
    except OSError:
        pass


def is_workflow_path(path: str) -> bool:
    if not path:
        return False
    # Normalize slashes; works on both Windows and POSIX paths.
    norm = path.replace("\\", "/").lstrip("/")
    if ".github/workflows/" not in norm:
        return False
    lower = norm.lower()
    return lower.endswith(".yml") or lower.endswith(".yaml")


def cleanup_old_state() -> None:
    """Remove session state files older than 30 days."""
    try:
        d = os.path.join(os.path.expanduser("~/.claude"), "logs")
        if not os.path.isdir(d):
            return
        cutoff = datetime.now().timestamp() - 30 * 24 * 3600
        for name in os.listdir(d):
            if name.startswith("github_workflow_warnings_") and name.endswith(".json"):
                full = os.path.join(d, name)
                try:
                    if os.path.getmtime(full) < cutoff:
                        os.remove(full)
                except OSError:
                    pass
    except OSError:
        pass


def main() -> int:
    if os.environ.get("ENABLE_GH_WORKFLOW_SECURITY", "1") == "0":
        return 0

    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0  # don't block on malformed input

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0

    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not is_workflow_path(file_path):
        return 0

    # 10% chance to clean up stale state files.
    import random
    if random.random() < 0.1:
        cleanup_old_state()

    session_id = str(data.get("session_id", "default"))
    key = file_path.replace("\\", "/").lower()
    shown = load_shown(session_id)

    if key in shown:
        # Already shown once this session — advisory only, do not block.
        print(REMINDER, file=sys.stderr)
        return 0

    shown.add(key)
    save_shown(session_id, shown)
    print(REMINDER, file=sys.stderr)
    return 2  # block once so the reminder lands in context


if __name__ == "__main__":
    sys.exit(main())
