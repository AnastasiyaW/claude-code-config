#!/usr/bin/env python3
"""Smoke test for conversation-history-capture.py with fake session logs."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


HOOK = Path(__file__).resolve().parent.parent / "hooks" / "conversation-history-capture.py"


def load_module():
    spec = importlib.util.spec_from_file_location("conversation_history_capture", HOOK)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "sessions"
        dest = root / "history"
        session_dir = source / "2026" / "07" / "04"
        session_dir.mkdir(parents=True)
        log = session_dir / "rollout-test-session.jsonl"
        log.write_text(
            "\n".join(
                [
                    json.dumps({"type": "session_meta", "payload": {"id": "test-session", "cwd": "C:/work"}}),
                    json.dumps({"role": "user", "content": "make a hook"}),
                    json.dumps({"role": "assistant", "content": "done"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        old_source = mod.SOURCE_ROOT
        old_dest = mod.DEST_ROOT
        old_archive = mod.ARCHIVE_ROOT
        old_index = mod.INDEX_PATH
        old_latest = mod.LATEST_MD
        try:
            mod.SOURCE_ROOT = source
            mod.DEST_ROOT = dest
            mod.ARCHIVE_ROOT = dest / "archive"
            mod.INDEX_PATH = dest / "codex_sessions_index.jsonl"
            mod.LATEST_MD = dest / "LATEST.md"
            result = mod.collect(recent_days=30, limit=10)
            assert result["indexed_total"] == 1, result
            assert result["archived_or_updated"] == 1, result
            index_text = mod.INDEX_PATH.read_text(encoding="utf-8")
            assert "test-session" in index_text
            assert "make a hook" in index_text
            assert (mod.ARCHIVE_ROOT / "2026" / "07" / "04" / "rollout-test-session.jsonl").exists()
        finally:
            mod.SOURCE_ROOT = old_source
            mod.DEST_ROOT = old_dest
            mod.ARCHIVE_ROOT = old_archive
            mod.INDEX_PATH = old_index
            mod.LATEST_MD = old_latest

    print("test_conversation_history_capture: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
