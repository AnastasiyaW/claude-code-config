#!/usr/bin/env python3
"""Unit tests for generate_skills_catalog.py."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("generate_skills_catalog.py")
SPEC = importlib.util.spec_from_file_location("generate_skills_catalog", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GenerateSkillsCatalogTests(unittest.TestCase):
    def test_generates_and_detects_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "development" / "demo-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: >\n  Useful demo workflow\n  for testing.\n---\n# Demo\n",
                encoding="utf-8",
            )
            output = root / "skills" / "README.md"

            self.assertEqual(MODULE.main(["--root", str(root), "--output", str(output)]), 0)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("[demo-skill](development/demo-skill/)", rendered)
            self.assertIn("Useful demo workflow for testing.", rendered)
            self.assertEqual(MODULE.main(["--root", str(root), "--output", str(output), "--check"]), 0)

            output.write_text("stale\n", encoding="utf-8")
            self.assertEqual(MODULE.main(["--root", str(root), "--output", str(output), "--check"]), 1)

    def test_accepts_utf8_bom_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "bom-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "\ufeff---\nname: bom-skill\ndescription: Use when checking BOM parsing.\n---\n# Demo\n",
                encoding="utf-8",
            )
            self.assertIn("Use when checking BOM parsing.", MODULE.render(root))


if __name__ == "__main__":
    unittest.main(verbosity=2)
