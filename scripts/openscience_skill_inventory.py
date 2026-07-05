#!/usr/bin/env python3
"""Inventory and score OpenScience skills for local adoption.

The script is intentionally narrow: it reads only SKILL.md metadata and bundled
resource counts, then ranks skills against domain keywords. It does not install
or execute OpenScience dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DOMAIN_KEYWORDS = {
    "dataset": [
        "dataset",
        "data pipeline",
        "curation",
        "dedup",
        "quality",
        "eda",
        "exploratory",
    ],
    "training": [
        "training",
        "fine-tuning",
        "finetuning",
        "lora",
        "qlora",
        "trl",
        "unsloth",
        "accelerate",
        "deepspeed",
    ],
    "evaluation": [
        "evaluation",
        "benchmark",
        "metric",
        "validation",
        "data leak",
        "multi-seed",
    ],
    "inference": [
        "inference",
        "serving",
        "vllm",
        "gguf",
        "llama.cpp",
        "tensorrt",
        "quantization",
    ],
    "explainability": [
        "shap",
        "explainability",
        "interpretability",
        "feature importance",
        "bias",
    ],
    "tracking": [
        "trackio",
        "mlflow",
        "tensorboard",
        "weights and biases",
        "experiment tracking",
    ],
    "vision": [
        "vision",
        "image",
        "microscopy",
        "segmentation",
        "vlm",
        "clip",
        "blip",
    ],
}


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    meta: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta


def score_skill(row: dict[str, object]) -> dict[str, object]:
    haystack = " ".join(
        str(row.get(key, "")).lower()
        for key in ("path", "name", "description", "category")
    )
    domains: dict[str, int] = {}
    for domain, words in DOMAIN_KEYWORDS.items():
        hits = sum(1 for word in words if word in haystack)
        if hits:
            domains[domain] = hits
    resource_score = min(int(row["references"]) + int(row["scripts"]) * 2, 6)
    line_penalty = 1 if int(row["lines"]) > 800 else 0
    score = sum(domains.values()) + resource_score - line_penalty
    return {"domains": domains, "score": score}


def inventory(repo: Path) -> list[dict[str, object]]:
    skills_root = repo / "backend" / "cli" / "skills"
    if not skills_root.exists():
        raise SystemExit(f"OpenScience skills root not found: {skills_root}")

    rows: list[dict[str, object]] = []
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        skill_dir = path.parent
        row: dict[str, object] = {
            "path": path.relative_to(skills_root).as_posix(),
            "category": path.relative_to(skills_root).parts[0],
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "license": meta.get("license", ""),
            "references": len(list((skill_dir / "references").glob("*")))
            if (skill_dir / "references").exists()
            else 0,
            "scripts": len(list((skill_dir / "scripts").glob("*")))
            if (skill_dir / "scripts").exists()
            else 0,
            "lines": text.count("\n") + 1,
        }
        row.update(score_skill(row))
        rows.append(row)
    rows.sort(key=lambda row: (-int(row["score"]), str(row["path"])))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to synthetic-sciences/openscience checkout")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--top", type=int, default=80, help="Number of ranked skills to keep")
    args = parser.parse_args()

    rows = inventory(Path(args.repo))
    payload = {
        "source": "synthetic-sciences/openscience",
        "total_skills": len(rows),
        "top": rows[: args.top],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"total_skills": len(rows), "written": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
