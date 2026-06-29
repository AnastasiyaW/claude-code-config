#!/usr/bin/env python3
"""Tests for task-completion hook discipline.

These tests make the hook expectations executable:
- Stop hooks must include the guards that prevent unfinished work from being
  silently closed.
- PreCompact must preserve handoff state.
- The stop-phrase guard must block defer/ask endings.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOKS_JSON = Path.home() / ".codex" / "hooks.json"
STOP_GUARD = Path.home() / ".claude" / "claude-code-config" / "hooks" / "stop-phrase-guard.py"
PLUGIN_CACHE = Path.home() / ".codex" / "plugins" / "cache"

REQUIRED_STOP_HOOKS = (
    "stop-phrase-guard.py",
    "test-gate-stop-hook.py",
    "problems-md-validator.py",
    "feature-list-validator.py",
    "session-handoff-reminder.py",
)

REQUIRED_PRECOMPACT_HOOKS = (
    "precompact-handoff-guard.py",
)

REQUIRED_SESSIONSTART_HOOKS = (
    "session-handoff-check.py",
    "review_handoff_memory_loop.py",
)


def hook_commands(event_name: str) -> list[str]:
    config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    commands: list[str] = []
    for group in config["hooks"].get(event_name, []):
        for hook in group.get("hooks", []):
            command = hook.get("command")
            if isinstance(command, str):
                commands.append(command)
    return commands


class TaskCompletionHookTests(unittest.TestCase):
    def test_plugin_hook_configs_have_supported_top_level_schema(self) -> None:
        if not PLUGIN_CACHE.exists():
            self.skipTest("plugin cache is absent")
        offenders: list[str] = []
        for path in PLUGIN_CACHE.rglob("hooks/hooks.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            extra = sorted(set(data) - {"hooks"})
            if extra:
                offenders.append(f"{path}: unsupported top-level keys {extra}")
            if "hooks" not in data:
                offenders.append(f"{path}: missing top-level hooks")
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_stop_hooks_include_completion_guards(self) -> None:
        commands = "\n".join(hook_commands("Stop"))
        for required in REQUIRED_STOP_HOOKS:
            self.assertIn(required, commands)

    def test_precompact_hooks_include_handoff_guard(self) -> None:
        commands = "\n".join(hook_commands("PreCompact"))
        for required in REQUIRED_PRECOMPACT_HOOKS:
            self.assertIn(required, commands)

    def test_sessionstart_hooks_include_handoff_memory_review(self) -> None:
        commands = "\n".join(hook_commands("SessionStart"))
        for required in REQUIRED_SESSIONSTART_HOOKS:
            self.assertIn(required, commands)

    def test_stop_phrase_guard_blocks_defer_ending(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task-completion-hook-") as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".claude").mkdir()
            transcript = tmp_path / "transcript.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Осталось доделать проверку; хочешь, сделаю следующим шагом.",
                        }
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            event = json.dumps({"transcript_path": str(transcript)}, ensure_ascii=False)
            result = subprocess.run(
                [sys.executable, str(STOP_GUARD)],
                input=event,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=tmp,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload.get("decision"), "block")
            self.assertIn("actually finish the work", payload.get("reason", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
