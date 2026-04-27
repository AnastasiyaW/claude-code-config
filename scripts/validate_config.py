#!/usr/bin/env python3
"""
Config Drift Validator for Claude Code.

Scans CLAUDE.md and .claude/rules/*.md for file path references,
checks which ones still exist, and reports drift.

Philosophy: structurally prevent drift like Rust's type system prevents
memory errors - validate references at session start, not after failure.

Runs on SessionStart hook. Fast (should complete in <500ms).

Customization (env vars):
    CLAUDE_WORKSPACE_ROOTS - colon-sep (Unix) or semicolon-sep (Windows)
        list of EXTRA roots to search for unresolved relative paths.
        Useful when your monorepo lives outside ~/Desktop.
        Example (bash): export CLAUDE_WORKSPACE_ROOTS=~/code:/d/projects

Exit codes:
    0 = always (advice layer; warnings don't block session start)

Output: writes report to ~/.claude/drift-report.md (always - even when clean,
        so stale reports from prior dirty runs don't mislead readers),
        prints summary to stdout for hook to show in session context.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Patterns that look like REAL file path references in markdown.
# We only check paths that are structurally unambiguous:
#   - Windows absolute:  C:\Users\...  or  C:/Users/...
#   - Unix absolute:     /home/..., /etc/...
#   - Home-relative:     ~/.claude/...
#   - Explicit relative: ./foo, ../foo
#   - Multi-segment:     foo/bar/baz.ext  (has at least one slash)
#
# We DO NOT check bare filenames (e.g. `README.md`, `foo.py`) because
# they are almost always used as concepts/examples, not as verifiable refs.
PATH_PATTERN = re.compile(
    r"`("
    r"[A-Za-z]:[\\/][^\s`]+?"          # C:\... or C:/...
    r"|~[/\\][^\s`]+?"                  # ~/...
    r"|/[A-Za-z][^\s`]*?/[^\s`]+?"      # /usr/bin/... (avoid lone /)
    r"|\.{1,2}[/\\][^\s`]+?"            # ./foo, ../foo
    r"|[\w\-]+[/\\][\w\-/\\\.]+?"       # foo/bar/baz.ext (must have /)
    r")`"
)

# Skip these even if they match the pattern (known placeholders/examples).
# Substring match - if the path *contains* any of these, skip.
SKIP_PATTERNS = [
    "path/to/",
    "foo/",
    "bar/",
    "example.",
    "your-",
    "my-",
    "<",   # <placeholder>
    "$",   # $VAR
    "{",   # {template}
    "ds_",  # ds_id in SQL examples
    "0N",   # placeholder like 0N-name.md
    "...",  # placeholder like foo/.../bar
    "{{",   # template variable
    "*",   # glob pattern (e.g. id_*, block_*.py, ~/.secrets/*, /proc/*/environ)
    "/api/",   # URL endpoints (e.g. /api/v1/projects/7/tasks)
    "docker/login-action",  # GitHub Actions ref, not a file path
    "./script.sh",  # generic script placeholder
    "cat/less/",    # tool list (cat/less/head/tail/grep/bat/xxd)
    "YYYY-",        # date placeholder in template paths
]

# Linux/macOS-only system paths - skip on Windows (validator can't resolve them
# locally but rule files reference them as concepts for SSH/system config docs).
LINUX_SYSTEM_PREFIXES = ("/etc/", "/proc/", "/opt/", "/var/", "/usr/", "/dev/")

# Cross-machine references - paths that live on a *different host* than this
# Claude session (Hyper-V VMs, remote build hosts, container mount points).
#
# Default: empty. Extend in your fork if rule files mention paths on remote
# hosts. Example:
#   CROSS_MACHINE_PREFIXES = ("C:\\BuildVM\\", "/mnt/buildbot/")
CROSS_MACHINE_PREFIXES: tuple[str, ...] = ()


def extract_paths(content: str) -> set[str]:
    """Extract file path references from markdown text.

    Filters out:
      - SKIP_PATTERNS substrings (placeholders, glob `*`, URL paths)
      - LINUX_SYSTEM_PREFIXES on Windows (we can't resolve /etc/, /proc/ here)
      - CROSS_MACHINE_PREFIXES (remote-only refs, opt-in via fork)
    """
    is_windows = sys.platform == "win32"
    matches = PATH_PATTERN.findall(content)
    paths = set()
    for match in matches:
        path = match[0] if isinstance(match, tuple) else match
        if any(skip in path for skip in SKIP_PATTERNS):
            continue
        if is_windows and path.startswith(LINUX_SYSTEM_PREFIXES):
            continue
        if CROSS_MACHINE_PREFIXES and path.startswith(CROSS_MACHINE_PREFIXES):
            continue
        paths.add(path)
    return paths


def _build_workspace_roots() -> list[Path]:
    """Compose ordered list of candidate roots for contextual lookup.

    Order:
      1. CLAUDE_WORKSPACE_ROOTS env var entries (user-specified primary
         monorepo paths - most likely to hit, checked first).
      2. ~/Desktop, ~ (legacy fallbacks for refs without explicit prefix).
      3. ~/.claude/projects/*/  (Claude Code memory dirs - for `memory/<file>`
         refs that target the session-scoped memory store).

    Perf: claude_projects iteration is filtered to dirs with a `memory/`
    subdir (skips empty project records that wouldn't match anyway).
    """
    roots: list[Path] = []

    # 1. User-specified roots via env var (colon-sep on Unix, semicolon on Win)
    env_roots = os.environ.get("CLAUDE_WORKSPACE_ROOTS", "")
    if env_roots:
        sep = ";" if sys.platform == "win32" else ":"
        for entry in env_roots.split(sep):
            entry = entry.strip()
            if entry:
                roots.append(Path(entry).expanduser())

    # 2. Generic fallbacks
    roots.append(Path.home() / "Desktop")
    roots.append(Path.home())

    # 3. Claude Code project memory dirs (filtered by has-memory-subdir)
    claude_projects = Path.home() / ".claude" / "projects"
    if claude_projects.exists():
        for proj in claude_projects.iterdir():
            if proj.is_dir() and (proj / "memory").is_dir():
                roots.append(proj)

    return roots


def check_path(path_str: str, base: Path) -> tuple[bool, str]:
    """Check if a path exists. Returns (exists, resolved_path_str).

    Tries (in order): expand ~, absolute, relative to base, relative to cwd,
    then contextual lookup under workspace roots (see _build_workspace_roots).
    """
    # Expand home directory (~/foo)
    if path_str.startswith("~"):
        expanded = Path(path_str).expanduser()
        return expanded.exists(), str(expanded)

    p = Path(path_str)

    if p.is_absolute():
        return p.exists(), str(p)

    # Relative to base (the file containing the reference)
    rel_to_base = base / path_str
    if rel_to_base.exists():
        return True, str(rel_to_base)

    # Relative to cwd
    if Path(path_str).exists():
        return True, path_str

    # Contextual lookup under workspace roots
    for root in _build_workspace_roots():
        if not root.exists():
            continue
        candidate = root / path_str
        if candidate.exists():
            return True, str(candidate)

    return False, path_str


def validate_file(md_file: Path) -> list[str]:
    """Validate all path references in a markdown file. Returns list of drift issues."""
    if not md_file.exists():
        return [f"MISSING FILE: {md_file}"]

    content = md_file.read_text(encoding="utf-8", errors="replace")
    paths = extract_paths(content)
    issues = []

    for path_ref in paths:
        exists, _ = check_path(path_ref, md_file.parent)
        if not exists:
            issues.append(f"{md_file.name}: broken ref -> {path_ref}")

    return issues


def main() -> int:
    # Force UTF-8 output on Windows - broken refs may contain Cyrillic /
    # non-ASCII path components, default cp1252 stdout crashes on print.
    if (
        sys.platform == "win32"
        and sys.stdout.encoding
        and sys.stdout.encoding.lower() != "utf-8"
    ):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass  # Older Python or non-tty stdout - best effort

    claude_dir = Path.home() / ".claude"
    cwd = Path.cwd()

    # Files to validate
    targets = []

    # Global config
    global_claude_md = claude_dir / "CLAUDE.md"
    if global_claude_md.exists():
        targets.append(global_claude_md)

    # Global rules
    global_rules = claude_dir / "rules"
    if global_rules.exists():
        targets.extend(global_rules.glob("*.md"))

    # Project config
    project_claude_md = cwd / "CLAUDE.md"
    if project_claude_md.exists():
        targets.append(project_claude_md)

    project_rules = cwd / ".claude" / "rules"
    if project_rules.exists():
        targets.extend(project_rules.glob("*.md"))

    # Validate
    all_issues = []
    for target in targets:
        issues = validate_file(target)
        all_issues.extend(issues)

    # Report - always write report (even on clean run) so file-based readers
    # (incl. verifier agents) consistently see current state. Without this, a
    # stale drifted report from a prior session persists and misleads anyone
    # who reads the file directly.
    report_path = claude_dir / "drift-report.md"
    if not all_issues:
        print(f"[config-validator] OK: {len(targets)} files, no drift detected")
        report_path.write_text(
            "# Config Drift Report\n\n"
            f"Last run: clean - scanned {len(targets)} files, "
            "no broken references.\n",
            encoding="utf-8",
        )
        return 0

    print(f"[config-validator] DRIFT DETECTED: {len(all_issues)} broken references")
    print(f"[config-validator] Files scanned: {len(targets)}")
    for issue in all_issues[:10]:
        print(f"  - {issue}")
    if len(all_issues) > 10:
        print(f"  ... and {len(all_issues) - 10} more")

    report_path.write_text(
        "# Config Drift Report\n\n"
        f"Scanned {len(targets)} files, found {len(all_issues)} broken references.\n\n"
        + "\n".join(f"- {i}" for i in all_issues)
        + "\n",
        encoding="utf-8",
    )
    print(f"[config-validator] Full report: {report_path}")

    # Warnings don't block - return 0 so session still starts
    return 0


if __name__ == "__main__":
    sys.exit(main())
