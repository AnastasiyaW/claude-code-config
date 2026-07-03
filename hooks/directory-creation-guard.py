#!/usr/bin/env python3
"""PreToolUse: guard ad-hoc directory creation.

Blocks new loose folders that should live in an existing hierarchy, and requires
an explicit delete marker for scratch/test/temp work directories.

Accepted delete markers in the same command:
  _DELETE_OK.md, .delete-ok, DELETE_OK, .tmp-meta.json

Bypass, only after conscious review:
  # claude-bypass: mkdir-cohesion
"""
from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import allow, bash_command, block, bypass, log, read_event  # noqa: E402


SHELL_SPLIT_RE = re.compile(r"(?:\r?\n|&&|\|\||;)")
MKDIR_RE = re.compile(r"^\s*(?:mkdir|md)\b\s+(?P<args>.+)$", re.IGNORECASE)
NEW_ITEM_RE = re.compile(r"\bNew-Item\b", re.IGNORECASE)
CREATE_DIR_RE = re.compile(r"\[IO\.Directory\]::CreateDirectory\s*\((?P<arg>[^)]+)\)", re.IGNORECASE)
ITEMTYPE_DIR_RE = re.compile(r"-ItemType\s+(?:Directory|'Directory'|\"Directory\")", re.IGNORECASE)
PATH_ARG_RE = re.compile(
    r"-(?:LiteralPath|Path)\s+(?P<path>\"[^\"]+\"|'[^']+'|[^\s;|&]+)",
    re.IGNORECASE,
)

DELETE_MARKER_RE = re.compile(
    r"(_DELETE_OK\.md|\.delete-ok\b|DELETE_OK\b|\.tmp-meta\.json)",
    re.IGNORECASE,
)

SCRATCH_HINT_RE = re.compile(
    r"(^|[\\/._-])(tmp|temp|scratch|sandbox|experiment|experiments|proof|"
    r"smoke|try|trial|test-run|testdata|fixture-work|worktree-test)([\\/._-]|$)",
    re.IGNORECASE,
)

APPROVED_DURABLE_PREFIXES = (
    ".agent/",
    ".claude/",
    ".codex/",
    ".github/",
    "agents/",
    "alternatives/",
    "docs/",
    "hooks/",
    "principles/",
    "references/",
    "reports/",
    "rules/",
    "scripts/",
    "skills/",
    "templates/",
    "tests/",
)

APPROVED_SCRATCH_PREFIXES = (
    ".tmp/",
    "tmp/",
    "temp/",
    ".scratch/",
    "scratch/",
    ".cache/",
    "cache/",
)

GENERATED_BUILD_PREFIXES = (
    "build/",
    "dist/",
    "out/",
    "target/",
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
)


def _norm(path: str) -> str:
    p = path.strip().strip("\"'")
    p = p.replace("\\", "/")
    p = re.sub(r"/+", "/", p)
    return p.rstrip("/")


def _strip_shell_noise(token: str) -> str:
    token = token.strip().strip(",")
    while token.startswith(("./", ".\\")):
        token = token[2:]
    return _norm(token)


def _split_args(args: str) -> list[str]:
    try:
        return shlex.split(args, posix=False)
    except ValueError:
        return args.split()


def _extract_mkdir_targets(cmd: str) -> list[str]:
    targets: list[str] = []
    for segment in SHELL_SPLIT_RE.split(cmd):
        seg = segment.strip()
        if not seg:
            continue

        m = MKDIR_RE.search(seg)
        if m:
            for tok in _split_args(m.group("args")):
                clean = _strip_shell_noise(tok)
                if not clean or clean.startswith("-"):
                    continue
                if clean in {"2>nul", "nul", "NUL"}:
                    continue
                targets.append(clean)
            continue

        if NEW_ITEM_RE.search(seg) and ITEMTYPE_DIR_RE.search(seg):
            for pm in PATH_ARG_RE.finditer(seg):
                targets.append(_strip_shell_noise(pm.group("path")))
            continue

        for cm in CREATE_DIR_RE.finditer(seg):
            targets.append(_strip_shell_noise(cm.group("arg")))

    return [t for t in targets if t]


def _is_absolute(path: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:/", path)) or path.startswith("/")


def _is_direct_root_child(path: str, cwd: str) -> bool:
    p = _norm(path)
    if not p or "/" in p or _is_absolute(p):
        return False
    return True


def _absolute_loose_reason(path: str, cwd: str) -> str | None:
    p = _norm(path)
    if not _is_absolute(p):
        return None

    home = _norm(str(Path.home())).lower()
    desktop = _norm(str(Path.home() / "Desktop")).lower()
    downloads = _norm(str(Path.home() / "Downloads")).lower()
    cwd_norm = _norm(cwd or os.getcwd()).lower()
    low = p.lower()

    parent = low.rsplit("/", 1)[0] if "/" in low else low
    if parent in {home, desktop, downloads, cwd_norm}:
        return f"direct child of {parent}"
    if "/appdata/local/temp/" in low or low.startswith(_norm(os.environ.get("TEMP", "")).lower() + "/"):
        return "OS temp directory"
    return None


def _relative(path: str, cwd: str) -> str:
    p = _norm(path)
    if not _is_absolute(p):
        return p.lower()
    try:
        return _norm(str(Path(p).resolve().relative_to(Path(cwd or os.getcwd()).resolve()))).lower()
    except Exception:
        return p.lower()


def _needs_delete_marker(path: str, cwd: str) -> bool:
    rel = _relative(path, cwd)
    return rel.startswith(APPROVED_SCRATCH_PREFIXES) or bool(SCRATCH_HINT_RE.search(rel))


def _has_good_hierarchy(path: str, cwd: str) -> bool:
    rel = _relative(path, cwd)
    if rel.startswith(APPROVED_DURABLE_PREFIXES):
        return True
    if rel.startswith(APPROVED_SCRATCH_PREFIXES):
        return True
    if rel.startswith(GENERATED_BUILD_PREFIXES):
        return True
    return False


def _verdict_for_target(path: str, cmd: str, cwd: str) -> str | None:
    if DELETE_MARKER_RE.search(cmd):
        marker_present = True
    else:
        marker_present = False

    if _needs_delete_marker(path, cwd) and not marker_present:
        return (
            f"Directory '{path}' looks temporary/test/scratch, but the command "
            "does not create a delete marker. Create it in a tracked scratch "
            "place and add _DELETE_OK.md (or .delete-ok) explaining that the "
            "directory contains no irreplaceable data."
        )

    loose_abs = _absolute_loose_reason(path, cwd)
    if loose_abs and not _has_good_hierarchy(path, cwd):
        return (
            f"Directory '{path}' is a loose folder ({loose_abs}). Re-check the "
            "placement: use an existing project hierarchy such as docs/, "
            "reports/, tests/, scripts/, or a scratch root like .tmp/<task>/ "
            "with _DELETE_OK.md."
        )

    if _is_direct_root_child(path, cwd) and not _has_good_hierarchy(path, cwd):
        return (
            f"Directory '{path}' would be created directly in the project root. "
            "Avoid folder proliferation: put durable artifacts under the right "
            "project hierarchy, or use .tmp/<task>/ plus _DELETE_OK.md for "
            "temporary/test work."
        )

    return None


def main() -> None:
    event = read_event()
    if event.get("tool_name") not in {"Bash", "PowerShell"}:
        allow()

    cmd = bash_command(event.get("tool_input", {}) or {})
    if not cmd:
        allow()

    targets = _extract_mkdir_targets(cmd)
    if not targets:
        allow()

    if bypass("mkdir-cohesion", cmd):
        log("WARN", "directory_creation_guard", "bypass", "mkdir-cohesion", cmd)
        allow()

    cwd = str(event.get("cwd") or os.getcwd())
    reasons = []
    for target in targets:
        reason = _verdict_for_target(target, cmd, cwd)
        if reason:
            reasons.append(reason)

    if reasons:
        log("BLOCK", "directory_creation_guard", "deny", "mkdir-cohesion", cmd)
        block(
            "Directory creation cohesion guard blocked this command.\n\n"
            + "\n\n".join(f"- {r}" for r in reasons)
            + "\n\nExpected pattern: durable folders go into the existing project "
            "tree; scratch folders go under .tmp/<task>/ and include _DELETE_OK.md."
        )

    allow()


if __name__ == "__main__":
    main()
