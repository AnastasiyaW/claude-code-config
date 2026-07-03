#!/usr/bin/env python3
"""Audit top-level folders for lifecycle cleanup labels."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


DELETE_CANDIDATES = {"TEMP_REPRODUCIBLE", "CACHE_GENERATED", "ARTIFACT_REGENERABLE"}
CONDITIONAL_CANDIDATES = {"GIT_BACKED", "DATASET_REBUILDABLE"}
KEEP_LABELS = {"PROJECT_ROOT", "KEEP_MANUAL", "NEEDS_REVIEW"}

NAME_HINTS = {
    "temp": "TEMP_REPRODUCIBLE",
    "tmp": "TEMP_REPRODUCIBLE",
    "scratch": "TEMP_REPRODUCIBLE",
    "cache": "CACHE_GENERATED",
    "export": "ARTIFACT_REGENERABLE",
    "report": "ARTIFACT_REGENERABLE",
    "review": "NEEDS_REVIEW",
    "dataset": "DATASET_REBUILDABLE",
    "data": "DATASET_REBUILDABLE",
    "mask": "DATASET_REBUILDABLE",
}


def load_meta(folder: Path) -> dict:
    path = folder / ".folder-meta.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"label": "NEEDS_REVIEW", "meta_error": str(exc)}


def infer_label(folder: Path) -> str:
    low = folder.name.lower()
    for hint, label in NAME_HINTS.items():
        if hint in low:
            return label
    if (folder / ".git").exists():
        return "GIT_BACKED"
    return "NEEDS_REVIEW"


def classify(label: str) -> str:
    if label in DELETE_CANDIDATES:
        return "delete-candidate"
    if label in CONDITIONAL_CANDIDATES:
        return "conditional-delete"
    if label in KEEP_LABELS:
        return "keep-or-review"
    return "unknown"


def summarize_folder(folder: Path, max_children: int) -> dict:
    meta = load_meta(folder)
    label = str(meta.get("label") or "").upper()
    inferred = False
    if not label:
        label = infer_label(folder)
        inferred = True

    children_sample: list[str] = []
    child_count = 0
    try:
        for child in folder.iterdir():
            child_count += 1
            if len(children_sample) < max_children:
                children_sample.append(child.name)
    except OSError as exc:
        children_sample.append(f"<read-error: {exc}>")

    return {
        "path": str(folder),
        "name": folder.name,
        "label": label,
        "label_source": "inferred-from-name" if inferred else ".folder-meta.json",
        "action": classify(label),
        "safe_to_delete": bool(meta.get("safe_to_delete", False)),
        "source_of_truth": meta.get("source_of_truth", ""),
        "rebuild": meta.get("rebuild", ""),
        "child_count": child_count,
        "children_sample": children_sample,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.getcwd(), help="workspace root to audit")
    parser.add_argument("--out", help="write JSON report to this path")
    parser.add_argument("--max-children", type=int, default=8)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    folders = [p for p in root.iterdir() if p.is_dir()]
    records = [summarize_folder(p, args.max_children) for p in sorted(folders, key=lambda x: x.name.lower())]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "records": records,
        "counts": {
            "total": len(records),
            "delete_candidates": sum(1 for r in records if r["action"] == "delete-candidate"),
            "conditional_delete": sum(1 for r in records if r["action"] == "conditional-delete"),
            "keep_or_review": sum(1 for r in records if r["action"] == "keep-or-review"),
            "unknown": sum(1 for r in records if r["action"] == "unknown"),
        },
    }

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
