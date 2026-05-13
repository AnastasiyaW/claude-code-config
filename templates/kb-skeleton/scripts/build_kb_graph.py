#!/usr/bin/env python3
"""Build the feature/layer cross-reference graph for a project.

Scans `docs/layers/**` and `feature_list.json`, extracts hyperlinks
between layers, features, invariants, decisions, and global KB
references, then generates:

  docs/_graph/tree.md         -- Mermaid graph for human navigation
  docs/_graph/backlinks.json  -- machine-readable reverse index
  docs/_graph/health.md       -- broken-link and consistency report

Run from project root, or with `--repo <path>` to point at a specific
repo. Stdlib only; runs in <2 seconds on a 100-feature project.

ASCII-only output so Windows cp1252 consoles do not choke.

See principle 28 for the architecture this script supports:
https://github.com/AnastasiyaW/claude-code-config/blob/main/principles/28-feature-layer-architecture.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

# Feature filename: feat-NNN-slug.md
FEATURE_FILE_RE = re.compile(r"^feat-(\d{3,})-([a-z0-9][a-z0-9-]*)\.md$")

# YAML-ish front-matter fields inside a feature doc body (markdown bold)
STATUS_RE = re.compile(r"^\s*\*\*Status:\*\*\s+([a-z-]+)\s*$", re.M)
BRANCH_RE = re.compile(r"^\s*\*\*Branch:\*\*\s+(\S+)\s*$", re.M)
LAYER_LINK_RE = re.compile(r"^\s*\*\*Layer:\*\*\s+\[([\w-]+)\]")
STARTED_RE = re.compile(r"^\s*\*\*Started:\*\*\s+(\d{4}-\d{2}-\d{2})", re.M)
OWNER_RE = re.compile(r"^\s*\*\*Owner:\*\*\s+(.+?)\s*$", re.M)

# H1 title line: `# F-NNN: title`
H1_TITLE_RE = re.compile(r"^#\s+F-(\d+):\s+(.+?)\s*$", re.M)

# Cross-references inside markdown bodies
F_REF_RE = re.compile(r"\bF-(\d{3,})\b")
IV_REF_RE = re.compile(r"\bIV-(\d+)\b")
D_REF_RE = re.compile(r"\bD-(\d+)\b")
G_REF_RE = re.compile(r"\bG-(\d+)\b")
PT_REF_RE = re.compile(r"\bPT-(\d+)\b")
P_GLOBAL_RE = re.compile(r"\bP-(\d{2})\b")
R_GLOBAL_RE = re.compile(r"\bR-([\w-]+)\b")
A_GLOBAL_RE = re.compile(r"\bA-([\w-]+)\b")

# Relative markdown links: [text](path.md)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------


class Feature:
    __slots__ = (
        "id", "slug", "layer", "title", "status", "branch",
        "started", "owner", "path", "refs_features", "refs_invariants",
        "refs_decisions", "refs_gotchas", "refs_patterns",
        "refs_global_principles", "links_out", "raw_body",
    )

    def __init__(self, *, id: str, slug: str, layer: str, path: Path) -> None:
        self.id = id            # "F-042"
        self.slug = slug        # "api-key-rotation"
        self.layer = layer      # "security"
        self.title = ""
        self.status = ""
        self.branch = ""
        self.started = ""
        self.owner = ""
        self.path = path
        self.refs_features: set[str] = set()
        self.refs_invariants: set[str] = set()        # "IV-3"
        self.refs_decisions: set[str] = set()          # "D-7"
        self.refs_gotchas: set[str] = set()            # "G-3"
        self.refs_patterns: set[str] = set()           # "PT-1"
        self.refs_global_principles: set[str] = set()  # e.g. "P-28"
        self.links_out: list[tuple[str, str]] = []     # (text, target)
        self.raw_body = ""


class Layer:
    __slots__ = ("name", "path", "features", "purpose", "principles_linked")

    def __init__(self, *, name: str, path: Path) -> None:
        self.name = name
        self.path = path
        self.features: list[Feature] = []
        self.purpose = ""
        self.principles_linked: set[str] = set()


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def find_repo_root(start: Path) -> Path | None:
    """Walk up until we find a git repo or a docs/layers/ directory."""
    cur = start.resolve()
    for _ in range(20):
        if (cur / ".git").exists() or (cur / "docs" / "layers").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def discover_layers(layers_root: Path) -> list[Layer]:
    layers: list[Layer] = []
    if not layers_root.is_dir():
        return layers
    for child in sorted(layers_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        if child.name == "_graph":
            continue
        layers.append(Layer(name=child.name, path=child))
    return layers


def discover_features(layer: Layer) -> None:
    features_dir = layer.path / "features"
    if not features_dir.is_dir():
        return
    for f in sorted(features_dir.iterdir()):
        if not f.is_file() or f.suffix != ".md":
            continue
        m = FEATURE_FILE_RE.match(f.name)
        if not m:
            continue
        num = int(m.group(1))
        feature = Feature(
            id=f"F-{num:03d}",
            slug=m.group(2),
            layer=layer.name,
            path=f,
        )
        layer.features.append(feature)


# --------------------------------------------------------------------------
# Parsing a single feature doc
# --------------------------------------------------------------------------


def parse_feature(feat: Feature) -> None:
    try:
        text = feat.path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  [WARN] cannot read {feat.path}: {e}", file=sys.stderr)
        return
    feat.raw_body = text

    if m := H1_TITLE_RE.search(text):
        feat.title = m.group(2).strip()

    if m := STATUS_RE.search(text):
        feat.status = m.group(1).strip()

    if m := BRANCH_RE.search(text):
        feat.branch = m.group(1).strip()

    if m := STARTED_RE.search(text):
        feat.started = m.group(1).strip()

    if m := OWNER_RE.search(text):
        feat.owner = m.group(1).strip()

    feat.refs_features = {f"F-{int(n):03d}" for n in F_REF_RE.findall(text)
                          if f"F-{int(n):03d}" != feat.id}
    feat.refs_invariants = {f"IV-{n}" for n in IV_REF_RE.findall(text)}
    feat.refs_decisions = {f"D-{n}" for n in D_REF_RE.findall(text)}
    feat.refs_gotchas = {f"G-{n}" for n in G_REF_RE.findall(text)}
    feat.refs_patterns = {f"PT-{n}" for n in PT_REF_RE.findall(text)}
    feat.refs_global_principles = {f"P-{n}" for n in P_GLOBAL_RE.findall(text)}

    for m_text, m_target in MD_LINK_RE.findall(text):
        feat.links_out.append((m_text, m_target))


def parse_layer_readme(layer: Layer) -> None:
    readme = layer.path / "README.md"
    if not readme.is_file():
        return
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError:
        return
    if m := re.search(r"\*\*Purpose:\*\*\s+(.+?)$", text, re.M):
        layer.purpose = m.group(1).strip()
    layer.principles_linked = {f"P-{n}" for n in P_GLOBAL_RE.findall(text)}


# --------------------------------------------------------------------------
# Graph generation
# --------------------------------------------------------------------------


def gen_tree_md(layers: list[Layer]) -> str:
    lines: list[str] = [
        "# Feature graph (auto-generated)",
        "",
        "Generated by `scripts/build_kb_graph.py`. **Do not edit manually**;",
        "rerun the script to refresh.",
        "",
        "See [principle 28](https://github.com/AnastasiyaW/claude-code-config/blob/main/principles/28-feature-layer-architecture.md)",
        "for the architecture this graph represents.",
        "",
        "## Layer x feature overview",
        "",
        "```mermaid",
        "graph LR",
    ]

    # Nodes
    for layer in layers:
        node_id = f"L_{_safe(layer.name)}"
        purpose_short = (layer.purpose[:40] + "...") if len(layer.purpose) > 43 else layer.purpose
        label = f"L-{layer.name}<br/>{_escape_mermaid(purpose_short)}"
        lines.append(f"  {node_id}[\"{label}\"]")
        for feat in layer.features:
            fnode = f"F_{int(feat.id.split('-')[1]):03d}"
            status_marker = _status_marker(feat.status)
            title_short = (feat.title[:30] + "...") if len(feat.title) > 33 else feat.title
            flabel = f"{feat.id}<br/>{_escape_mermaid(title_short)}<br/>{status_marker}"
            lines.append(f"  {fnode}[\"{flabel}\"]")
            lines.append(f"  {node_id} --> {fnode}")

    # Feature -> feature dependency edges
    for layer in layers:
        for feat in layer.features:
            fnode = f"F_{int(feat.id.split('-')[1]):03d}"
            for ref in sorted(feat.refs_features):
                tnode = f"F_{int(ref.split('-')[1]):03d}"
                lines.append(f"  {fnode} -.depends.-> {tnode}")

    lines.append("```")
    lines.append("")

    # Detailed per-layer breakdown
    lines.append("## Per-layer detail")
    lines.append("")
    for layer in layers:
        lines.append(f"### L-{layer.name}")
        lines.append("")
        if layer.purpose:
            lines.append(f"**Purpose:** {layer.purpose}")
            lines.append("")
        if layer.principles_linked:
            principles = ", ".join(sorted(layer.principles_linked))
            lines.append(f"**Governing principles:** {principles}")
            lines.append("")
        if layer.features:
            lines.append("| ID | Title | Status | Branch | Started | Owner |")
            lines.append("|----|-------|--------|--------|---------|-------|")
            for feat in sorted(layer.features, key=lambda f: f.id):
                try:
                    rel = feat.path.relative_to(layer.path.parent.parent).as_posix()
                except ValueError:
                    # Path doesn't share the expected prefix (symlink, worktree,
                    # case-sensitivity quirk on Windows). Fall back to filename.
                    rel = feat.path.name
                lines.append(
                    f"| [{feat.id}]({rel}) | {feat.title or '_(missing title)_'} | "
                    f"{feat.status or '_(unset)_'} | {feat.branch or '-'} | "
                    f"{feat.started or '-'} | {feat.owner or '-'} |"
                )
        else:
            lines.append("_No features yet._")
        lines.append("")

    return "\n".join(lines) + "\n"


def gen_backlinks(layers: list[Layer]) -> dict[str, Any]:
    """Build reverse index: for each feature/invariant/decision, who references it."""
    backlinks: dict[str, list[str]] = defaultdict(list)
    all_features = {f.id: f for layer in layers for f in layer.features}

    for layer in layers:
        for feat in layer.features:
            for ref in feat.refs_features:
                backlinks[ref].append(feat.id)
            for ref in feat.refs_invariants:
                backlinks[f"{layer.name}/{ref}"].append(feat.id)
            for ref in feat.refs_decisions:
                backlinks[f"{layer.name}/{ref}"].append(feat.id)
            for ref in feat.refs_gotchas:
                backlinks[f"{layer.name}/{ref}"].append(feat.id)
            for ref in feat.refs_patterns:
                backlinks[f"{layer.name}/{ref}"].append(feat.id)
            for ref in feat.refs_global_principles:
                backlinks[ref].append(feat.id)

    return {
        "generated_by": "scripts/build_kb_graph.py",
        "features_known": sorted(all_features),
        "backlinks": {k: sorted(set(v)) for k, v in sorted(backlinks.items())},
    }


def gen_health_report(
    layers: list[Layer],
    feature_list_json_path: Path | None,
) -> tuple[str, int]:
    """Check consistency. Returns (markdown_report, error_count)."""
    lines: list[str] = [
        "# KB graph health (auto-generated)",
        "",
        "Generated by `scripts/build_kb_graph.py`. Rerun to refresh.",
        "",
    ]
    errors = 0
    warnings = 0
    all_features = {f.id: f for layer in layers for f in layer.features}

    # Check 1: feature_list.json sync
    if feature_list_json_path and feature_list_json_path.is_file():
        try:
            with feature_list_json_path.open(encoding="utf-8") as f:
                fl = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            lines.append(f"- [ERROR] cannot parse {feature_list_json_path}: {e}")
            errors += 1
            fl = None

        if fl and isinstance(fl, dict) and "features" in fl:
            json_ids = {item.get("id") for item in fl["features"] if isinstance(item, dict)}
            doc_ids = set(all_features)
            only_in_json = json_ids - doc_ids - {None}
            only_in_docs = doc_ids - json_ids
            for fid in sorted(only_in_json):
                lines.append(f"- [ERROR] feature_list.json has `{fid}` but no docs/layers/*/features/feat-*.md file found")
                errors += 1
            for fid in sorted(only_in_docs):
                lines.append(f"- [WARN] {fid} has a doc but is missing from feature_list.json")
                warnings += 1
    else:
        lines.append("- [INFO] no feature_list.json at repo root; skipping sync check")

    # Check 2: dangling F-NNN references
    for layer in layers:
        for feat in layer.features:
            for ref in feat.refs_features:
                if ref not in all_features:
                    lines.append(
                        f"- [ERROR] {feat.id} references `{ref}` but no such feature exists"
                    )
                    errors += 1

    # Check 3: feature without status, title, or layer link
    for layer in layers:
        for feat in layer.features:
            if not feat.title:
                lines.append(f"- [WARN] {feat.id} has no H1 title line `# F-NNN: <title>`")
                warnings += 1
            if not feat.status:
                lines.append(f"- [WARN] {feat.id} has no `**Status:**` field")
                warnings += 1

    # Check 4: layer name <-> directory drift
    for layer in layers:
        readme_text = ""
        if (layer.path / "README.md").is_file():
            readme_text = (layer.path / "README.md").read_text(encoding="utf-8")
        first_line_match = re.match(r"#\s+Layer:\s+(.+?)\s*$", readme_text, re.M)
        if first_line_match:
            declared = first_line_match.group(1).strip()
            if declared.lower() != layer.name.lower() and declared not in {"<layer-name>", "<layer name>"}:
                lines.append(
                    f"- [WARN] layer dir is `{layer.name}/` but README says `Layer: {declared}`"
                )
                warnings += 1

    # Summary
    if errors == 0 and warnings == 0:
        lines.append("All checks passed.")
    else:
        lines.append("")
        lines.append(f"Total: {errors} error(s), {warnings} warning(s).")

    return "\n".join(lines) + "\n", errors


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def _escape_mermaid(text: str) -> str:
    # Mermaid label syntax breaks on: closing bracket, pipe (subgraph delim),
    # semicolon (statement separator), backticks (code escape). Parentheses
    # are OK inside quoted labels. Newlines become spaces.
    return (
        text.replace('"', "'")
        .replace("\n", " ")
        .replace("]", ")")
        .replace("|", "/")
        .replace(";", ",")
        .replace("`", "'")
    )


def _status_marker(status: str) -> str:
    return {
        "design": "(design)",
        "planning": "(plan)",
        "executing": "(WIP)",
        "reviewing": "(review)",
        "done": "DONE",
        "blocked": "BLOCKED",
        "not-started": "(todo)",
    }.get(status, "")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    # __doc__ is None under `python -OO` (docstrings stripped). Fall back to a
    # one-liner so the parser still constructs.
    desc = (__doc__ or "Build feature-layer KB graph.").split("\n\n")[0]
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(),
        help="Repository root (default: current dir, walks up to find one)",
    )
    parser.add_argument(
        "--check-only", action="store_true",
        help="Run health check, do not write _graph/ files. Exit nonzero on errors.",
    )
    args = parser.parse_args(argv)

    repo = find_repo_root(args.repo)
    if repo is None:
        print("[ERROR] could not locate a git repo or docs/layers/ from", args.repo, file=sys.stderr)
        return 2

    layers_root = repo / "docs" / "layers"
    if not layers_root.is_dir():
        print(f"[INFO] no docs/layers/ in {repo} -- nothing to do")
        return 0

    layers = discover_layers(layers_root)
    if not layers:
        print(f"[INFO] no layer directories under {layers_root}")
        return 0

    for layer in layers:
        discover_features(layer)
        parse_layer_readme(layer)
        for feat in layer.features:
            parse_feature(feat)

    feature_list_json = repo / "feature_list.json"
    health_md, error_count = gen_health_report(
        layers, feature_list_json if feature_list_json.exists() else None,
    )

    if args.check_only:
        print(health_md)
        return 1 if error_count else 0

    graph_dir = repo / "docs" / "_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)

    (graph_dir / "tree.md").write_text(gen_tree_md(layers), encoding="utf-8")
    (graph_dir / "backlinks.json").write_text(
        json.dumps(gen_backlinks(layers), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (graph_dir / "health.md").write_text(health_md, encoding="utf-8")

    n_features = sum(len(layer.features) for layer in layers)
    print(f"[OK] graph built: {len(layers)} layer(s), {n_features} feature(s)")
    print(f"     wrote: {graph_dir.relative_to(repo).as_posix()}/tree.md")
    print(f"     wrote: {graph_dir.relative_to(repo).as_posix()}/backlinks.json")
    print(f"     wrote: {graph_dir.relative_to(repo).as_posix()}/health.md")
    if error_count:
        print(f"[WARN] health report flagged {error_count} error(s); see health.md")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
