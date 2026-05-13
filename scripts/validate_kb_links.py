#!/usr/bin/env python3
"""SessionStart hook: lightweight scan of project's docs/layers/ tree.

Goal: surface obvious KB drift in the first 200ms of a session, so the
agent reads a fresh status before touching code. Heavy validation (full
graph, backlinks, cross-reference integrity) lives in
`scripts/build_kb_graph.py` and runs manually or in CI.

Exits 0 always. Output goes to stdout and is injected into agent context
by the Claude Code harness.

Checks performed (cheap, no recursive parsing):
  1. Does `docs/layers/` exist? If not, exit silently (project does not
     use the feature-layer architecture yet -- skip).
  2. List layers (top-level subdirs, excluding `_*` templates).
  3. Per layer: count features in `features/feat-*.md`.
  4. Cross-check `feature_list.json` (if exists) feature count matches
     the on-disk count.
  5. Detect layers whose README still has the `<layer-name>` placeholder
     (sign of incomplete scaffolding).

Reference: principle 28 -- Feature-Layer Architecture.
https://github.com/AnastasiyaW/claude-code-config/blob/main/principles/28-feature-layer-architecture.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FEATURE_FILE_RE = re.compile(r"^feat-(\d{3,})-([a-z0-9][a-z0-9-]*)\.md$")
PLACEHOLDER_TOKENS = ("<layer-name>", "<Layer name>", "TODO")


def main() -> int:
    cwd = Path.cwd()
    layers_root = cwd / "docs" / "layers"
    if not layers_root.is_dir():
        return 0

    layers: list[tuple[str, Path]] = []
    for child in sorted(layers_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        if child.name == "_graph":
            continue
        layers.append((child.name, child))

    if not layers:
        return 0

    notes: list[str] = []
    notes.append(f"[KB] feature-layer architecture detected ({len(layers)} layer(s))")

    total_features = 0
    on_disk_ids: set[int] = set()
    drift_layers: list[str] = []

    for name, path in layers:
        features_dir = path / "features"
        feats: list[tuple[int, Path]] = []
        if features_dir.is_dir():
            for f in features_dir.iterdir():
                if f.is_file() and f.suffix == ".md":
                    m = FEATURE_FILE_RE.match(f.name)
                    if m:
                        num = int(m.group(1))
                        feats.append((num, f))
                        on_disk_ids.add(num)

        total_features += len(feats)
        readme = path / "README.md"
        placeholder_in_readme = False
        if readme.is_file():
            try:
                rtext = readme.read_text(encoding="utf-8")
            except OSError:
                rtext = ""
            if any(tok in rtext for tok in PLACEHOLDER_TOKENS):
                placeholder_in_readme = True
                drift_layers.append(name)

        status_summary = ""
        if feats:
            statuses = _scan_statuses([p for _, p in sorted(feats)])
            status_summary = f" [{_format_statuses(statuses)}]"

        warn = " (README has placeholders)" if placeholder_in_readme else ""
        notes.append(f"  L-{name}: {len(feats)} feature(s){status_summary}{warn}")

    # Cross-check feature_list.json if present
    feature_list_json = cwd / "feature_list.json"
    if feature_list_json.is_file():
        try:
            with feature_list_json.open(encoding="utf-8") as fp:
                fl = json.load(fp)
        except (OSError, json.JSONDecodeError) as e:
            notes.append(f"[KB warn] cannot parse feature_list.json: {e}")
            fl = None
        if fl and isinstance(fl, dict) and "features" in fl:
            json_ids: set[int] = set()
            for item in fl["features"]:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    m = re.match(r"^F-(\d+)$", item["id"])
                    if m:
                        json_ids.add(int(m.group(1)))
            only_in_json = json_ids - on_disk_ids
            only_in_docs = on_disk_ids - json_ids
            if only_in_json:
                ids = ", ".join(f"F-{i:03d}" for i in sorted(only_in_json))
                notes.append(f"[KB warn] feature_list.json has {ids} with no on-disk doc")
            if only_in_docs:
                ids = ", ".join(f"F-{i:03d}" for i in sorted(only_in_docs))
                notes.append(f"[KB warn] {ids} on disk but missing from feature_list.json")

    if total_features:
        notes.append(f"[KB] total features: {total_features} across {len(layers)} layer(s)")
    notes.append("[KB] full graph: `python scripts/build_kb_graph.py` (writes docs/_graph/)")

    # Output as one block, harness will inject into agent context
    print("\n".join(notes))
    return 0


def _scan_statuses(paths: list[Path]) -> dict[str, int]:
    """Cheap status scan: read only first ~30 lines per file to find Status field."""
    counts: dict[str, int] = {}
    for p in paths:
        try:
            with p.open(encoding="utf-8") as fp:
                head = fp.read(1500)  # first ~30 lines
        except OSError:
            continue
        m = re.search(r"^\s*\*\*Status:\*\*\s+([a-z-]+)\s*$", head, re.M)
        status = m.group(1) if m else "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def _format_statuses(counts: dict[str, int]) -> str:
    if not counts:
        return ""
    order = ["done", "executing", "reviewing", "planning", "design", "blocked", "not-started", "unknown"]
    parts: list[str] = []
    for s in order:
        if s in counts:
            parts.append(f"{s}: {counts[s]}")
    for s in sorted(counts):
        if s not in order:
            parts.append(f"{s}: {counts[s]}")
    return ", ".join(parts)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # SessionStart hook MUST NOT block. Swallow any unexpected error
        # so a malformed docs/layers/ tree never breaks session startup.
        sys.exit(0)
