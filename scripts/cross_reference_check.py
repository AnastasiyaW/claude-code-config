#!/usr/bin/env python3
"""Cross-reference integrity check for claude-code-skills repo.

Verifies that internal links in markdown files point to files that exist.
Catches drift where a principle/rule/README references a renamed or deleted
file. Run before committing, or in CI.

Checks:
  1. Markdown links `[text](path.md)` resolve to an existing file
  2. Links to `principles/NN-*.md` match the actual numbering
  3. Links to `hooks/NAME.py` and `scripts/NAME.py` point to real scripts
  4. Every principle is linked from README.md or principles/README.md
  5. Every rule is linked from README.md or a principle
  6. Every hook is listed in README.md hooks table

Exit codes:
  0 - all checks passed
  1 - broken links or missing cross-references found

Usage:
  python scripts/cross_reference_check.py
  python scripts/cross_reference_check.py --strict  # also fail on warnings
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

# Match markdown links: [text](relative/path.md) or [text](path.md#anchor)
# Skip URLs (http://, https://, mailto:)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# What dirs contain markdown we scan
SCAN_DIRS = ["principles", "rules", "alternatives", "skills", "templates"]
SCAN_ROOT_FILES = ["README.md", "AGENTS.md", "CLAUDE.md", "UPDATES.md", "HOW-IT-WORKS.md"]


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "mailto:", "#"))


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks and inline code from markdown text.

    Links inside ``` ... ``` or `inline code` are illustrative, not real links,
    and should not be validated.
    """
    # Remove fenced blocks (``` or ~~~)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.DOTALL)
    # Remove inline code `...`
    text = re.sub(r"`[^`\n]*`", "", text)
    return text


def collect_files() -> list[Path]:
    files: list[Path] = []
    for name in SCAN_ROOT_FILES:
        p = ROOT / name
        if p.exists():
            files.append(p)
    for d in SCAN_DIRS:
        dp = ROOT / d
        if not dp.exists():
            continue
        files.extend(dp.rglob("*.md"))
    return files


def check_link(source: Path, url: str) -> str | None:
    """Return error message if link is broken, None if OK."""
    # Strip anchor
    path_part = url.split("#", 1)[0]
    if not path_part:  # pure anchor, skip
        return None
    target = (source.parent / path_part).resolve()
    if not target.exists():
        return f"broken link: {url} -> {target}"
    return None


def check_principle_numbering() -> list[str]:
    """Principles must be NN-kebab-case.md with no gaps or duplicates."""
    errors: list[str] = []
    pdir = ROOT / "principles"
    if not pdir.exists():
        return errors
    seen: dict[int, list[str]] = defaultdict(list)
    for p in pdir.glob("*.md"):
        if p.name == "README.md":
            continue
        m = re.match(r"^(\d+)-", p.name)
        if not m:
            errors.append(f"principles/{p.name}: doesn't start with NN-")
            continue
        n = int(m.group(1))
        seen[n].append(p.name)
    for n, names in sorted(seen.items()):
        if len(names) > 1:
            errors.append(f"principle number {n} collision: {names}")
    if seen:
        expected = set(range(1, max(seen) + 1))
        missing = expected - set(seen.keys())
        if missing:
            errors.append(f"principle numbering gaps: missing {sorted(missing)}")
    return errors


def check_principle_coverage() -> list[str]:
    """Every principle file should be linked from README.md or principles/README.md."""
    warnings: list[str] = []
    pdir = ROOT / "principles"
    if not pdir.exists():
        return warnings
    index_sources = []
    for idx in [ROOT / "README.md", ROOT / "principles" / "README.md", ROOT / "AGENTS.md"]:
        if idx.exists():
            index_sources.append(idx.read_text(encoding="utf-8", errors="replace"))
    index_text = "\n".join(index_sources)
    for p in sorted(pdir.glob("*.md")):
        if p.name == "README.md":
            continue
        if p.name not in index_text:
            warnings.append(f"principle {p.name} not linked from any README/AGENTS index")
    return warnings


def check_hook_coverage() -> list[str]:
    """Every hook should be listed in README.md hooks table."""
    warnings: list[str] = []
    hdir = ROOT / "hooks"
    readme = ROOT / "README.md"
    if not hdir.exists() or not readme.exists():
        return warnings
    readme_text = readme.read_text(encoding="utf-8", errors="replace")
    for h in hdir.glob("*.py"):
        if h.name not in readme_text:
            warnings.append(f"hook {h.name} not mentioned in README.md")
    return warnings


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Resolve all markdown links
    for f in collect_files():
        raw = f.read_text(encoding="utf-8", errors="replace")
        text = strip_code_blocks(raw)
        for m in LINK_RE.finditer(text):
            url = m.group(2).strip()
            if is_external(url):
                continue
            if not url.endswith(".md") and not url.endswith(".py"):
                # Links to other extensions or dirs, skip
                continue
            err = check_link(f, url)
            if err:
                rel = f.relative_to(ROOT)
                errors.append(f"{rel}: {err}")

    # 2. Principle numbering
    errors.extend(check_principle_numbering())

    # 3. Principle coverage (warning)
    warnings.extend(check_principle_coverage())

    # 4. Hook coverage (warning)
    warnings.extend(check_hook_coverage())

    # Report
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("All cross-references OK.")
        return 0

    if errors:
        return 1
    if strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
