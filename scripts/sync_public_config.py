#!/usr/bin/env python3
"""sync_public_config.py - keep a PUBLIC config repo in sync with the ACTIVE ~/.claude.

Problem this solves: the active config (~/.claude) evolves daily; the public repo
(this one) goes stale silently. Blind copying is dangerous the other way: the active
config contains machine-specific rules/hooks (server names, IPs, local paths) that
must never reach a public repo.

Solution: manifest-driven one-way sync (active -> repo clone) with three safeguards:
  1. Only categories listed in sync-manifest.json are touched.
  2. "common" mode updates ONLY files already present in the repo; new active-only
     files are REPORTED as candidates, never auto-copied (a human promotes them by
     adding to "add" or copying manually).
  3. Every file written is scanned for privacy markers (machine names, IPs, user
     paths from the manifest); a hit skips the file and fails the run in --strict.

Usage:
  python scripts/sync_public_config.py              # dry-run report (default)
  python scripts/sync_public_config.py --apply      # actually copy
  python scripts/sync_public_config.py --scan-repo  # only scan the whole repo for markers
  python scripts/sync_public_config.py --strict     # non-zero exit on any marker hit

Comparison is EOL-normalized (CRLF==LF) so a git-clone on Windows does not produce
thousands of false "differs".
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "sync-manifest.json"

SKIP_SUFFIXES = {".pyc", ".pyo"}
SKIP_DIRS = {"__pycache__", ".git"}


def norm_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return None


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if p.suffix in SKIP_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def marker_hits(text: str, markers: list[str]) -> list[str]:
    hits = []
    for m in markers:
        try:
            if re.search(m, text, re.IGNORECASE):
                hits.append(m)
        except re.error:
            if m.lower() in text.lower():
                hits.append(m)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any privacy-marker hit")
    ap.add_argument("--scan-repo", action="store_true", help="only scan repo tree for markers")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"ERROR: manifest not found: {MANIFEST}", file=sys.stderr)
        return 2
    cfg = json.loads(MANIFEST.read_text(encoding="utf-8"))
    markers: list[str] = cfg.get("privacy_markers", [])
    active_root = Path(cfg["active_root"]).expanduser()

    any_marker_hit = False

    if args.scan_repo:
        print(f"== privacy scan of repo tree: {REPO_ROOT}")
        for f in iter_files(REPO_ROOT):
            if f == MANIFEST or f.resolve() == Path(__file__).resolve():
                continue  # manifest/scanner legitimately contain the marker strings
            text = norm_text(f)
            if text is None:
                continue
            hits = marker_hits(text, markers)
            if hits:
                any_marker_hit = True
                print(f"  MARKER {f.relative_to(REPO_ROOT)} :: {', '.join(hits)}")
        if not any_marker_hit:
            print("  clean - no privacy markers found")
        return 1 if (any_marker_hit and args.strict) else 0

    if not active_root.exists():
        print(f"ERROR: active root not found: {active_root}", file=sys.stderr)
        return 2

    updated, candidates, stale, skipped_private = [], [], [], []

    for mapping in cfg["mappings"]:
        src_dir = active_root / mapping["from"]
        dst_dir = REPO_ROOT / mapping["to"]
        deny = set(mapping.get("deny", []))
        add = set(mapping.get("add", []))
        if not src_dir.exists():
            print(f"  WARN: source missing, skipping mapping: {src_dir}")
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)

        src_files = {p.relative_to(src_dir).as_posix(): p for p in iter_files(src_dir)}
        dst_files = {p.relative_to(dst_dir).as_posix(): p for p in iter_files(dst_dir)}

        for rel, sp in src_files.items():
            if rel in deny:
                continue
            in_repo = rel in dst_files
            promote = rel in add
            if not in_repo and not promote:
                candidates.append(f"{mapping['from']}/{rel}")
                continue
            s_text = norm_text(sp)
            if s_text is None:
                continue
            d_text = norm_text(dst_files[rel]) if in_repo else None
            if in_repo and s_text == d_text:
                continue
            hits = marker_hits(s_text, markers)
            if hits:
                any_marker_hit = True
                skipped_private.append(f"{mapping['from']}/{rel} :: {', '.join(hits)}")
                continue
            updated.append(f"{mapping['to']}/{rel}")
            if args.apply:
                target = dst_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sp, target)

        for rel in dst_files:
            if rel not in src_files:
                stale.append(f"{mapping['to']}/{rel}")

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"== sync report ({mode}) active={active_root} -> repo={REPO_ROOT}")
    print(f"-- updated ({len(updated)}):")
    for x in updated:
        print(f"   {x}")
    print(f"-- active-only candidates, NOT copied - promote manually ({len(candidates)}):")
    for x in candidates:
        print(f"   {x}")
    print(f"-- repo-only (in repo, absent in active - maybe genericized fork, review) ({len(stale)}):")
    for x in stale:
        print(f"   {x}")
    print(f"-- SKIPPED, privacy markers ({len(skipped_private)}):")
    for x in skipped_private:
        print(f"   {x}")

    if any_marker_hit and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
