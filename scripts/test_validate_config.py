#!/usr/bin/env python3
"""Focused tests for strict documentation-drift validation."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("validate_config.py")
SPEC = importlib.util.spec_from_file_location("validate_config", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ValidateConfigTests(unittest.TestCase):
    def test_runtime_opt_out_file_is_not_treated_as_broken_link(self) -> None:
        self.assertEqual(MODULE.extract_paths("Use `~/.claude/.skip-feedback-capture`."), set())

    def test_strict_mode_fails_but_advisory_mode_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "CLAUDE.md").write_text("See `./missing/reference.md`.\n", encoding="utf-8")
            project = Path(tmp) / "project"
            project.mkdir()
            with patch.object(MODULE.Path, "home", return_value=home), patch.object(MODULE.Path, "cwd", return_value=project):
                self.assertEqual(MODULE.main([]), 0)
                self.assertEqual(MODULE.main(["--strict"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
