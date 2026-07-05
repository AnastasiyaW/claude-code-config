#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "openscience_skill_inventory.py"


def write_skill(base: Path, rel: str, body: str) -> None:
    path = base / "backend" / "cli" / "skills" / rel / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_inventory_scores_ml_domains() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        write_skill(
            repo,
            "ml-training/training-data-pipeline",
            """---
name: training-data-pipeline
description: Build training datasets, data quality validation, deduplication, and fine-tuning splits.
license: MIT
---
# Training Data
""",
        )
        write_skill(
            repo,
            "writing/poems",
            """---
name: poems
description: Write poems.
---
# Poems
""",
        )
        out = repo / "out.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo), "--out", str(out), "--top", "2"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        assert "total_skills" in result.stdout
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["total_skills"] == 2
        assert payload["top"][0]["name"] == "training-data-pipeline"
        assert payload["top"][0]["score"] > payload["top"][1]["score"]
        assert "dataset" in payload["top"][0]["domains"]


if __name__ == "__main__":
    test_inventory_scores_ml_domains()
    print("ok")
