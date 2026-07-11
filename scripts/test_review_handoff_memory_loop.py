#!/usr/bin/env python3
"""Self-tests for review_handoff_memory_loop.py.

The tests use only stdlib so they can run from the hub health check without
extra dependencies.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("review_handoff_memory_loop.py")


GOOD_HANDOFF = """# Session Handoff - 2026-06-24 19:00

**Session ID:** test-session
**Status:** ACTIVE
**Project:** sample-project

## Goal
Ship the loop.

## What Was Done
Implemented the validator.

## What Did NOT Work
Nothing blocked.

## Current State
Ready.

## Key Decisions
Use deterministic checks.

## Single Next Step
Run the proof.
"""

SUFFIX_HANDOFF = """# Session Handoff - 2026-06-24 19:00

**Session ID:** test-session
**Status:** ACTIVE
**Project:** sample-project

## Goal
Ship the loop.

## Done verified
Implemented the validator.

## What did NOT work / gotchas
Nothing blocked.

## Current state (running) — updated 23:10
Ready.

## Key Decisions
Use deterministic checks.

## Next step (optional, nothing critical pending)
Run the proof.
"""


BAD_HANDOFF = """# Session Handoff - 2026-06-24 19:00

**Session ID:** test-session
**Status:** ACTIVE
**Project:** sample-project

## Goal
Incomplete.
"""

ALIAS_HANDOFF = """# Session Handoff - 2026-06-24 19:00

**Session ID:** test-session
**Status:** ACTIVE
**Project:** sample-project

## Goal
Ship the loop.

## Done
Implemented the validator.

## What did NOT work / notes
Nothing blocked.

## State
Ready.

## Key Decisions
Use deterministic checks.

## Next Step
Run the proof.
"""


class HandoffMemoryLoopTests(unittest.TestCase):
    def make_fixture(self, handoff_text: str, include_memory_notes: bool = True) -> tuple[Path, Path, Path]:
        base = Path(tempfile.mkdtemp(prefix="handoff-loop-test-"))
        root = base / "hub"
        handoffs = root / ".claude" / "handoffs" / "sample-project"
        handoffs.mkdir(parents=True)
        (handoffs / "2026-06-24_19-00_test.md").write_text(handoff_text, encoding="utf-8")
        (handoffs / "PROBLEMS.md").write_text("# Problems\n", encoding="utf-8")
        index = root / ".claude" / "handoffs" / "INDEX.md"
        index.write_text(
            "2026-06-24 19:00 | test-session | sample-project | validator fixture | ACTIVE\n",
            encoding="utf-8",
        )

        hooks = base / "hooks.json"
        hooks.write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {"command": "session-handoff-check.py"},
                                    {"command": "precompact-handoff-guard.py"},
                                    {"command": "session-handoff-reminder.py"},
                                ]
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )

        memory = base / "memories"
        notes = memory / "extensions" / "ad_hoc" / "notes"
        notes.mkdir(parents=True)
        (memory / "MEMORY.md").write_text(
            "\n".join(
                [
                    "# Test memory",
                    "finish every task to full completion",
                    "handoff must preserve unfinished work",
                ]
            ),
            encoding="utf-8",
        )
        if include_memory_notes:
            (notes / "2026-06-24-handoff-unfinished-work.md").write_text(
                "\n".join(
                    [
                        "# Handoff must preserve unfinished work",
                        "Explicitly list every known unfinished related task.",
                        "Finish reversible and reachable related work before writing the handoff.",
                        "If blocked, record the blocked with the exact evidence state.",
                    ]
                ),
                encoding="utf-8",
            )
            (notes / "2026-06-24-finish-all-tasks-to-completion.md").write_text(
                "\n".join(
                    [
                        "# Finish every task to full completion",
                        "Carry it through to the full reachable result.",
                        "Finish implementation verification documentation in one loop.",
                        "Do not leave adjacent required tasks implicit.",
                    ]
                ),
                encoding="utf-8",
            )
        return root, hooks, memory

    def run_validator(self, root: Path, hooks: Path, memory: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(root),
                "--hooks",
                str(hooks),
                "--memory-base",
                str(memory),
                *extra,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_good_handoff_passes_strict_with_heading_case_variants(self) -> None:
        root, hooks, memory = self.make_fixture(GOOD_HANDOFF)
        result = self.run_validator(root, hooks, memory, "--strict-legacy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"pass": true', result.stdout)

    def test_handoff_alias_headings_pass_strict(self) -> None:
        root, hooks, memory = self.make_fixture(ALIAS_HANDOFF)
        result = self.run_validator(root, hooks, memory, "--strict-legacy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"pass": true', result.stdout)

    def test_handoff_heading_suffixes_pass_strict(self) -> None:
        root, hooks, memory = self.make_fixture(SUFFIX_HANDOFF)
        result = self.run_validator(root, hooks, memory, "--strict-legacy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"pass": true', result.stdout)

    def test_missing_handoff_sections_warn_by_default_fail_in_strict(self) -> None:
        root, hooks, memory = self.make_fixture(BAD_HANDOFF)
        default_result = self.run_validator(root, hooks, memory)
        self.assertEqual(default_result.returncode, 0, default_result.stdout + default_result.stderr)
        self.assertIn('"warn": 1', default_result.stdout)

        strict_result = self.run_validator(root, hooks, memory, "--strict-legacy")
        self.assertNotEqual(strict_result.returncode, 0, strict_result.stdout + strict_result.stderr)
        self.assertIn('"fail": 1', strict_result.stdout)

    def test_precanonical_index_records_are_accepted(self) -> None:
        root, hooks, memory = self.make_fixture(GOOD_HANDOFF)
        index = root / ".claude" / "handoffs" / "INDEX.md"
        with index.open("a", encoding="utf-8") as handle:
            handle.write("- 2026-06-07 17:52 | e5d1fa70 | historical summary | ACTIVE\n")
            handle.write("| 2026-06-19 | 00:35 | car-classifier-base | 019edc8e | historical summary |\n")
        result = self.run_validator(root, hooks, memory, "--strict-legacy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"warn": 0', result.stdout)

    def test_post_cutoff_noncanonical_index_record_is_reported(self) -> None:
        root, hooks, memory = self.make_fixture(GOOD_HANDOFF)
        index = root / ".claude" / "handoffs" / "INDEX.md"
        with index.open("a", encoding="utf-8") as handle:
            handle.write("- 2026-07-01 10:00 | new-session | noncanonical summary | ACTIVE\n")
        result = self.run_validator(root, hooks, memory)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unparseable INDEX line", result.stdout)

    def test_latest_handoff_uses_filename_timestamp_not_checkout_mtime(self) -> None:
        root, hooks, memory = self.make_fixture(GOOD_HANDOFF)
        older = root / ".claude" / "handoffs" / "sample-project" / "2026-06-23_23-59_old.md"
        older.write_text(BAD_HANDOFF, encoding="utf-8")
        future = time.time() + 3600
        os.utime(older, (future, future))

        result = self.run_validator(root, hooks, memory, "--strict-legacy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"pass": true', result.stdout)

    def test_explicit_runtime_report_dir_does_not_dirty_project_root(self) -> None:
        root, hooks, memory = self.make_fixture(GOOD_HANDOFF)
        runtime_reports = root.parent / "runtime-reports"
        result = self.run_validator(
            root,
            hooks,
            memory,
            "--write-report",
            "--report-dir",
            str(runtime_reports),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((runtime_reports / "latest.json").exists())
        self.assertFalse((root / "reports" / "handoff-memory-loop").exists())

    def test_missing_memory_note_fails(self) -> None:
        root, hooks, memory = self.make_fixture(GOOD_HANDOFF, include_memory_notes=False)
        result = self.run_validator(root, hooks, memory)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("required ad-hoc memory note missing", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
