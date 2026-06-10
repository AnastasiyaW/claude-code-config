#!/usr/bin/env python3
"""PreToolUse (Write|Edit|NotebookEdit): advisory reminder to keep files cohesive.

Non-blocking. Reminds (does NOT block) when a DURABLE file is written to a
loose/scratch location (home root, Desktop root, Downloads, temp) instead of
into an existing project / KB / storage hierarchy.

Rule: ~/.claude/rules/file-organization-cohesion.md
"""
from __future__ import annotations

import json
import os
import re
import sys


def read_event() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def file_path_of(ti: dict) -> str:
    for k in ("file_path", "path", "notebook_path"):
        v = ti.get(k)
        if v:
            return str(v)
    return ""


# Durable artifacts worth keeping organized (NOT ephemeral logs/temp).
DURABLE_EXT = {
    ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".txt", ".csv", ".tsv", ".html", ".css",
    ".sh", ".ps1", ".sql", ".rs", ".go", ".java", ".c", ".cpp", ".h",
}
EPHEMERAL_HINT = re.compile(r"(\.log$|\.tmp$|\.bak|\.cache|/temp/|\\temp\\|\.pyc$)", re.I)


def normish(p: str) -> str:
    return p.replace("\\", "/").rstrip("/")


def parent(p: str) -> str:
    p = normish(p)
    return p.rsplit("/", 1)[0] if "/" in p else p


def is_scratch_location(path: str) -> str | None:
    """Return a human reason if path's PARENT dir looks loose/scattered, else None."""
    p = normish(path)
    par = parent(p).lower()
    home = normish(os.path.expanduser("~")).lower()

    # exact home root, Desktop root, Downloads root
    if par == home:
        return "home root"
    if par == home + "/desktop":
        return "Desktop root"
    if par == home + "/downloads":
        return "Downloads"
    # OS temp dirs
    if re.search(r"(/temp$|/tmp$|/appdata/local/temp|/windows/temp)", par):
        return "a temp dir"
    return None


def main() -> None:
    ev = read_event()
    tool = ev.get("tool_name", "")
    ti = ev.get("tool_input", {}) or {}
    if tool not in {"Write", "Edit", "NotebookEdit"}:
        sys.exit(0)

    path = file_path_of(ti)
    if not path:
        sys.exit(0)

    # only care about NEW durable files (Edit on existing is fine; but path-based, keep simple)
    _, ext = os.path.splitext(path.lower())
    if ext not in DURABLE_EXT or EPHEMERAL_HINT.search(normish(path)):
        sys.exit(0)

    reason = is_scratch_location(path)
    if reason:
        # advisory only — print to stderr as additional context, allow the write
        msg = (
            f"⚠️  File-cohesion: writing a durable file into {reason} "
            f"({os.path.basename(path)}).\n"
            "Keep hierarchies + cohesion: if a project/KB/storage structure exists for this, "
            "put it THERE (related artifacts together), not scattered. "
            "See ~/.claude/rules/file-organization-cohesion.md. (advisory, not blocking)"
        )
        print(msg, file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
