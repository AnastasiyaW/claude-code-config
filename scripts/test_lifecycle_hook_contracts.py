#!/usr/bin/env python3
"""Behavioral contracts for the blocking and continuity lifecycle hooks."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"


def run_hook_result(name: str, cwd: Path, event: dict) -> tuple[dict | None, str, int]:
    home = cwd / "test-home"
    home.mkdir(exist_ok=True)
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, str(HOOKS / name)],
        cwd=cwd,
        input=json.dumps(event),
        text=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    payload = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            payload = json.loads(line)
            break
    return payload, result.stdout + result.stderr, result.returncode


def run_hook(name: str, cwd: Path, event: dict) -> tuple[dict | None, str]:
    payload, output, _ = run_hook_result(name, cwd, event)
    return payload, output


VALID_CLOSURE = """## Closure Audit
- Primary request status: COMPLETE
- Acceptance/checklist verified: tests passed
- Related/scope-adjacent tasks checked: checked
- Unfinished related tasks: NONE
- Why not continuing now: NONE
"""


class LifecycleHookContracts(unittest.TestCase):
    def make_project(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="lifecycle-hook-"))
        (root / ".claude").mkdir()
        return root

    def test_handoff_closure_audit_blocks_incomplete_and_allows_complete(self) -> None:
        root = self.make_project()
        target = root / ".claude" / "handoffs" / "demo" / "2026-07-11_12-00_test.md"
        target.parent.mkdir(parents=True)
        event = {"tool_name": "Write", "tool_input": {"file_path": str(target), "content": "# Handoff\n"}}
        payload, _ = run_hook("handoff-closure-audit-guard.py", root, event)
        self.assertEqual(payload and payload.get("decision"), "block")

        event["tool_input"]["content"] = "# Handoff\n\n" + VALID_CLOSURE
        payload, output = run_hook("handoff-closure-audit-guard.py", root, event)
        self.assertIsNone(payload, output)

    def test_problems_gate_rejects_plain_open(self) -> None:
        root = self.make_project()
        problems = root / "PROBLEMS.md"
        problems.write_text("## 2026-07-11 Unfixed\n**Status**: OPEN\n", encoding="utf-8")
        payload, _ = run_hook("problems-md-validator.py", root, {})
        self.assertEqual(payload and payload.get("decision"), "block")

        problems.write_text("## 2026-07-11 Waiting\n**Status**: missing-data\n", encoding="utf-8")
        payload, output = run_hook("problems-md-validator.py", root, {})
        self.assertIsNone(payload, output)

    def test_test_gate_blocks_red_and_allows_green(self) -> None:
        root = self.make_project()
        command = root / ".claude" / "test-command"
        command.write_text("python gate_test.py\n", encoding="utf-8")
        test_file = root / "gate_test.py"
        test_file.write_text("raise SystemExit(1)\n", encoding="utf-8")
        payload, _ = run_hook("test-gate-stop-hook.py", root, {})
        self.assertEqual(payload and payload.get("decision"), "block")

        test_file.write_text("raise SystemExit(0)\n", encoding="utf-8")
        payload, output = run_hook("test-gate-stop-hook.py", root, {})
        self.assertIsNone(payload, output)

    def test_precompact_creates_draft_then_accepts_fresh_handoff(self) -> None:
        root = self.make_project()
        payload, output = run_hook("precompact-handoff-guard.py", root, {"cwd": str(root), "session_id": "test"})
        self.assertIsNone(payload, output)
        self.assertIn("NO FRESH HANDOFF", output)
        self.assertTrue((root / ".claude" / ".precompact-handoff-needed").exists())
        self.assertEqual(len(list((root / ".claude" / "handoffs" / "codex-auto").glob("*.md"))), 1)

        fresh = root / ".claude" / "handoffs" / "demo" / "2026-07-11_12-00_test.md"
        fresh.parent.mkdir(parents=True)
        fresh.write_text("# Fresh\n", encoding="utf-8")
        os.utime(fresh, None)
        payload, output = run_hook("precompact-handoff-guard.py", root, {"cwd": str(root), "session_id": "test"})
        self.assertIsNone(payload, output)
        self.assertIn("fresh handoff exists", output)
        self.assertFalse((root / ".claude" / ".precompact-handoff-needed").exists())

    def test_handoff_reminder_blocks_long_session_without_handoff(self) -> None:
        root = self.make_project()
        marker = root / ".claude" / ".session-start"
        marker.touch()
        old = time.time() - 16 * 60
        os.utime(marker, (old, old))
        payload, _ = run_hook("session-handoff-reminder.py", root, {})
        self.assertEqual(payload and payload.get("decision"), "block")

    def test_github_workflow_security_blocks_once_then_allows(self) -> None:
        root = self.make_project()
        workflow = root / ".github" / "workflows" / "ci.yaml"
        event = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(workflow)},
            "session_id": "workflow-test",
        }

        payload, output, returncode = run_hook_result("github-workflow-security.py", root, event)
        self.assertIsNone(payload, output)
        self.assertEqual(returncode, 2, output)
        self.assertIn("workflow security checklist", output)

        payload, output, returncode = run_hook_result("github-workflow-security.py", root, event)
        self.assertIsNone(payload, output)
        self.assertEqual(returncode, 0, output)
        self.assertIn("workflow security checklist", output)

        payload, output, returncode = run_hook_result(
            "github-workflow-security.py",
            root,
            {"tool_name": "Edit", "tool_input": {"file_path": str(root / "src" / "app.py")}},
        )
        self.assertIsNone(payload, output)
        self.assertEqual(returncode, 0, output)

    def test_git_source_gate_requires_repo_and_origin_for_long_run_work(self) -> None:
        root = self.make_project()
        (root / "feature_list.json").write_text('{"features": []}', encoding="utf-8")

        payload, _ = run_hook("git-source-gate.py", root, {})
        self.assertEqual(payload and payload.get("decision"), "block")
        self.assertIn("not inside a Git repository", payload["reason"])

        initialized = subprocess.run(["git", "init", "-q"], cwd=root, check=False)
        self.assertEqual(initialized.returncode, 0)
        payload, _ = run_hook("git-source-gate.py", root, {})
        self.assertEqual(payload and payload.get("decision"), "block")
        self.assertIn("no `origin` remote", payload["reason"])

        remote = subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/example/private-project.git"],
            cwd=root,
            check=False,
        )
        self.assertEqual(remote.returncode, 0)
        payload, output = run_hook("git-source-gate.py", root, {})
        self.assertIsNone(payload, output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
