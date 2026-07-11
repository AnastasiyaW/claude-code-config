#!/usr/bin/env python3
"""Unit tests for repair_codex_plugin_hook_schema.py."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("repair_codex_plugin_hook_schema.py")
SPEC = importlib.util.spec_from_file_location("repair_plugin_hooks", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RepairCodexPluginHookSchemaTests(unittest.TestCase):
    def test_description_is_repaired_with_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "vendor" / "plugin" / "1.0" / "hooks"
            cache.mkdir(parents=True)
            path = cache / "hooks.json"
            path.write_text(
                json.dumps({"description": "label", "hooks": {"Stop": []}}),
                encoding="utf-8",
            )

            findings, errors = MODULE.scan(Path(tmp))
            self.assertEqual(errors, [])
            self.assertEqual(len(findings), 1)
            self.assertTrue(findings[0].repairable)

            repaired, repair_errors = MODULE.repair(findings)
            self.assertEqual(repair_errors, [])
            self.assertEqual(repaired, [path])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"hooks": {"Stop": []}})
            self.assertTrue(path.with_name("hooks.json.bak").exists())

            after, errors = MODULE.scan(Path(tmp))
            self.assertEqual(after, [])
            self.assertEqual(errors, [])

    def test_unknown_metadata_is_reported_but_not_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plugin" / "hooks.json"
            path.parent.mkdir(parents=True)
            original = {"hooks": {}, "version": 1}
            path.write_text(json.dumps(original), encoding="utf-8")

            findings, errors = MODULE.scan(Path(tmp))
            self.assertEqual(errors, [])
            repaired, repair_errors = MODULE.repair(findings)
            self.assertEqual(repaired, [])
            self.assertEqual(len(repair_errors), 1)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
