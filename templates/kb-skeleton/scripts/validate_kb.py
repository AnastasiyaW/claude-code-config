#!/usr/bin/env python3
"""Validate the knowledge base in `docs/kb/` against the real codebase.

Drop-in starter. Configure the constants in the CONFIG block below to
match your project layout. Stdlib only; runs in <1 second.

Fails the CI when:
  - A source area `<SOURCE_ROOT>/<area>/` has no `docs/kb/modules/<area>.md`.
  - A `docs/kb/modules/*.md` references a file path that no longer exists.
  - `docs/kb/INVARIANTS.md` references a test via `path::name` that is missing.
  - `AGENTS.md` claims a `docs/kb/*.md` file exists that is missing.

ASCII-only output so Windows cp1252 consoles do not choke.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# CONFIG -- edit these to match your project.
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
KB = REPO_ROOT / "docs" / "kb"
MODULES = KB / "modules"

# Where your source lives. `SOURCE_ROOT / <area>` will be checked for
# matching `MODULES / <area>.md` coverage. Add or remove roots per layout.
SOURCE_ROOTS = [
    REPO_ROOT / "src",          # common for Python projects
    REPO_ROOT,                  # fallback if your code sits at repo root
]

# Explicit <area>: <source_path> mapping -- use when your areas do not
# map 1:1 to directory names (e.g. a single file instead of a package).
# Empty by default.
EXPECTED_MODULE_DOCS: dict[str, Path] = {
    # "config": REPO_ROOT / "src" / "myapp" / "config.py",
    # "api":    REPO_ROOT / "src" / "myapp" / "api",
}

# If a referenced path contains any of these markers in the 40 chars
# after the backtick-close, it is treated as forward-looking and
# ignored. Useful for `foo.py (future)` style notes.
FUTURE_MARKERS = ("(future)", "(planned)", "(TODO)", "(not yet)")

# Extensions we consider "a path reference". Adjust if your repo uses
# other kinds of files you want tracked.
PATH_EXTENSIONS = ("py", "md", "yml", "yaml", "sh", "toml", "json", "ini",
                   "cfg", "ts", "js", "go", "rs")

# --------------------------------------------------------------------------
# END CONFIG
# --------------------------------------------------------------------------


errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def _discover_areas() -> dict[str, Path]:
    """Return {area_name: source_path} for every direct subdir of every
    SOURCE_ROOT plus every entry in EXPECTED_MODULE_DOCS."""
    mapping: dict[str, Path] = {**EXPECTED_MODULE_DOCS}
    for root in SOURCE_ROOTS:
        if not root.exists():
            continue
        for child in root.iterdir():
            # Skip hidden, skip common non-source dirs.
            if child.name.startswith(".") or child.name in {
                "__pycache__", "node_modules", "venv", ".venv", "dist",
                "build", "docs", "tests", "test", "scripts",
            }:
                continue
            if child.is_dir() and child.name not in mapping:
                mapping[child.name] = child
    return mapping


def check_module_coverage(areas: dict[str, Path]) -> None:
    for area, source_path in areas.items():
        doc = MODULES / f"{area}.md"
        if not source_path.exists():
            warn(f"mapped area '{area}' missing source at {source_path}")
            continue
        if not doc.exists():
            err(f"missing kb doc: {doc.relative_to(REPO_ROOT).as_posix()} (source: {source_path.relative_to(REPO_ROOT).as_posix()})")


_PATH_REF_RE = re.compile(
    r"`([\w./\-]+\.(?:" + "|".join(PATH_EXTENSIONS) + r"))(?::[\d\-]+)?`"
)


def _resolve_path(path_part: str, doc: Path, areas: dict[str, Path]) -> Path | None:
    """Try to resolve a short path reference against several plausible
    roots. kb docs use short refs like `session.py`; we accept a
    reference as valid if it exists under any reasonable root."""
    candidates: list[Path] = [REPO_ROOT / path_part]

    # If doc is kb/modules/<area>.md, try under the area's source path.
    if doc.parent.name == "modules" and doc.parent.parent.name == "kb":
        area = doc.stem
        if area in areas:
            candidates.append(areas[area] / path_part)

    for root in SOURCE_ROOTS:
        candidates.append(root / path_part)
        candidates.append(root / ".." / path_part)

    candidates.extend([
        KB / path_part,
        REPO_ROOT / "docs" / path_part,
        doc.parent / path_part,
    ])

    for c in candidates:
        if c.exists():
            return c

    # Last resort: walk each SOURCE_ROOT for a file whose rel-path ends
    # with path_part (so nested files like `migrations/versions/0001_initial.py`
    # are resolved).
    target_name = Path(path_part).name
    suffix = "/" + path_part if not path_part.startswith("/") else path_part
    for root in SOURCE_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob(target_name):
            rel = p.relative_to(REPO_ROOT).as_posix()
            if rel.endswith(suffix) or rel.endswith("/" + path_part):
                return p
    return None


def _check_paths_in(doc: Path, areas: dict[str, Path]) -> None:
    text = doc.read_text(encoding="utf-8")
    seen: set[str] = set()
    for m in _PATH_REF_RE.finditer(text):
        path_part = m.group(1)
        if path_part in seen:
            continue
        seen.add(path_part)
        if path_part.startswith("http"):
            continue

        tail = text[m.end(): m.end() + 40].lower()
        if any(marker in tail for marker in FUTURE_MARKERS):
            continue

        if _resolve_path(path_part, doc, areas) is None:
            err(f"{doc.relative_to(REPO_ROOT).as_posix()}: references missing path `{path_part}`")


def check_kb_references(areas: dict[str, Path]) -> None:
    for doc in sorted(MODULES.glob("*.md")):
        _check_paths_in(doc, areas)


def check_invariants_test_refs() -> None:
    inv = KB / "INVARIANTS.md"
    if not inv.exists():
        err("missing docs/kb/INVARIANTS.md")
        return
    text = inv.read_text(encoding="utf-8")
    # Pattern: `<path>.py::<test_name>` inside backticks.
    refs = re.findall(r"`([\w./\-]+\.py)::([\w]+)`", text)
    seen: set[tuple[str, str]] = set()
    for rel_path, test_name in refs:
        key = (rel_path, test_name)
        if key in seen:
            continue
        seen.add(key)
        candidates = [REPO_ROOT / rel_path]
        for root in SOURCE_ROOTS:
            candidates.append(root / rel_path)
            candidates.append(root / ".." / rel_path)
        resolved = next((c for c in candidates if c.exists()), None)
        if resolved is None:
            err(f"INVARIANTS.md: missing test file `{rel_path}`")
            continue
        src = resolved.read_text(encoding="utf-8")
        if re.search(rf"def\s+{re.escape(test_name)}\b", src) is None:
            err(f"INVARIANTS.md: `{rel_path}::{test_name}` not found in source")


def check_agents_pointers() -> None:
    agents = REPO_ROOT / "AGENTS.md"
    if not agents.exists():
        warn("AGENTS.md missing at repo root -- create from the skeleton")
        return
    text = agents.read_text(encoding="utf-8")
    for m in re.finditer(r"`(docs/kb/[\w./\-]+\.md)`", text):
        rel = m.group(1)
        if not (REPO_ROOT / rel).exists():
            err(f"AGENTS.md: dead kb pointer `{rel}`")


def main() -> int:
    if not KB.exists():
        err("missing docs/kb/ -- run from repo root or copy from kb-skeleton")
        print("\n".join(errors), file=sys.stderr)
        return 2

    areas = _discover_areas()
    check_module_coverage(areas)
    check_kb_references(areas)
    check_invariants_test_refs()
    check_agents_pointers()

    if warnings:
        print("KB warnings:", file=sys.stderr)
        for w in warnings:
            print(f"  [WARN] {w}", file=sys.stderr)

    if errors:
        print("\nKB validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  [ERR]  {e}", file=sys.stderr)
        print(
            f"\n{len(errors)} error(s). The knowledge base must stay in "
            "sync with code; fix the kb or the code reference.",
            file=sys.stderr,
        )
        return 1

    print(f"[OK] KB consistent. {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
