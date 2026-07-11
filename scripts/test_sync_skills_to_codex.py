#!/usr/bin/env python3
"""Unit tests for sync_skills_to_codex.py."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("sync_skills_to_codex.py")
SPEC = importlib.util.spec_from_file_location("sync_skills_to_codex", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SyncSkillsToCodexTests(unittest.TestCase):
    def test_apply_updates_source_files_and_preserves_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            skill = source / "development" / "demo-skill"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo-skill\ndescription: demo\n---\n", encoding="utf-8")
            (skill / "references" / "guide.md").write_text("fresh", encoding="utf-8")

            target = base / "active"
            old = target / "demo-skill"
            old.mkdir(parents=True)
            (old / "SKILL.md").write_text("old", encoding="utf-8")
            backups = base / "backups"

            changes, errors = MODULE.sync(source, target, backups, apply=False)
            self.assertEqual(errors, [])
            self.assertIn("demo-skill", changes)

            residual, errors = MODULE.sync(source, target, backups, apply=True)
            self.assertEqual(errors, [])
            self.assertEqual(residual, {})
            self.assertEqual((target / "demo-skill" / "references" / "guide.md").read_text(encoding="utf-8"), "fresh")
            backup_files = list(backups.rglob("SKILL.md"))
            self.assertEqual(len(backup_files), 1)
            self.assertEqual(backup_files[0].read_text(encoding="utf-8"), "old")

    def test_duplicate_names_fail_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            for category in ("a", "b"):
                path = source / category / "same" / "SKILL.md"
                path.parent.mkdir(parents=True)
                path.write_text("x", encoding="utf-8")
            changes, errors = MODULE.sync(source, Path(tmp) / "target", Path(tmp) / "backups", apply=True)
            self.assertEqual(changes, {})
            self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
