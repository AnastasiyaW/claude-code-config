#!/usr/bin/env python3
"""PreToolUse: auto-create backup branch before destructive git commands.

Unlike block_* hooks that deny, this one wraps: creates a safety branch
before allowing the destructive operation. The destructive operation itself
is still separately protected by block_git_destructive - this hook only runs
when bypass has been granted.

Triggers on:
  git reset --hard
  git clean -fdx (creates backup of working tree via stash)
  git checkout -- .

Backup format:
  git reset --hard  ->  branch claude-backup-{unix_timestamp}
  git clean -fdx    ->  git stash push -u -m 'claude-pre-clean-{ts}'

Runs only if CLAUDE_ALLOW_GIT_DESTRUCTIVE is set (i.e., user already bypassed
the main gate). If set, we still enforce a safety net.

Silent if not in git repo.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import (  # noqa: E402
    allow,
    bash_command,
    bypass_env,
    log,
    read_event,
)

RESET_HARD_RE = re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE)
CLEAN_FDX_RE = re.compile(r"\bgit\s+clean\s+-[fdx]{2,}", re.IGNORECASE)
CHECKOUT_DOT_RE = re.compile(r"\bgit\s+checkout\s+--\s+\.", re.IGNORECASE)


def in_git_repo(cwd: str | None = None) -> bool:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, cwd=cwd, timeout=5,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return False


def make_branch_backup(cwd: str | None, ts: int) -> str | None:
    """Create branch pointing at HEAD before the destructive op. Returns name or None."""
    name = f"claude-backup-{ts}"
    try:
        r = subprocess.run(
            ["git", "branch", name],
            capture_output=True, text=True, cwd=cwd, timeout=5,
        )
        if r.returncode == 0:
            return name
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def make_stash_backup(cwd: str | None, ts: int) -> str | None:
    """Stash working tree incl. untracked, so clean -fdx is reversible."""
    msg = f"claude-pre-clean-{ts}"
    try:
        r = subprocess.run(
            ["git", "stash", "push", "-u", "-m", msg],
            capture_output=True, text=True, cwd=cwd, timeout=10,
        )
        if r.returncode == 0 and "No local changes" not in r.stdout:
            return msg
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def main() -> None:
    event = read_event()
    if event.get("tool_name") != "Bash":
        allow()

    cmd = bash_command(event.get("tool_input", {}))
    if not cmd:
        allow()

    needs_branch = bool(RESET_HARD_RE.search(cmd) or CHECKOUT_DOT_RE.search(cmd))
    needs_stash = bool(CLEAN_FDX_RE.search(cmd))

    if not (needs_branch or needs_stash):
        allow()

    # This hook is the safety net - it only runs when the main git guard
    # has been bypassed. If bypass isn't set, the main guard already blocked.
    if not bypass_env("CLAUDE_ALLOW_GIT_DESTRUCTIVE"):
        allow()

    cwd = event.get("cwd") or os.getcwd()
    if not in_git_repo(cwd):
        allow()

    ts = int(time.time())

    if needs_branch:
        branch = make_branch_backup(cwd, ts)
        if branch:
            log("INFO", "auto_backup_git", "branch_created", branch, cmd)
            # Emit a user-visible message via stderr (still allow the op)
            sys.stderr.write(
                f"[auto-backup] Created safety branch {branch} before destructive op.\n"
                f"Recover: git checkout {branch}\n"
            )
        else:
            log("WARN", "auto_backup_git", "branch_failed", "", cmd)
            sys.stderr.write(
                "[auto-backup] WARNING: failed to create safety branch. "
                "Consider aborting and backing up manually.\n"
            )

    if needs_stash:
        stash = make_stash_backup(cwd, ts)
        if stash:
            log("INFO", "auto_backup_git", "stash_created", stash, cmd)
            sys.stderr.write(
                f"[auto-backup] Stashed working tree as '{stash}' before clean.\n"
                "Recover: git stash list && git stash pop stash@{N}\n"
            )
        else:
            log("WARN", "auto_backup_git", "stash_failed_or_empty", "", cmd)

    allow()


if __name__ == "__main__":
    main()
