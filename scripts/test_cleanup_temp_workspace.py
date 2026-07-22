import json
import tempfile
import time
import unittest
from pathlib import Path

from cleanup_temp_workspace import inspect


class CleanupTempWorkspaceTests(unittest.TestCase):
    def test_unknown_entries_are_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unknown-output.bin").write_bytes(b"x")
            records = inspect(root, [{"pattern": "test-*", "label": "TEMP_REPRODUCIBLE", "safe_to_delete": True, "ttl_days": 0, "rebuild": "rerun"}])
            self.assertEqual(records[0]["action"], "keep")

    def test_approved_old_entry_is_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "test-old"
            candidate.mkdir()
            policy = [{"pattern": "test-*", "label": "TEMP_REPRODUCIBLE", "safe_to_delete": True, "ttl_days": 0, "rebuild": "rerun test"}]
            records = inspect(root, policy, now=time.time() + 86400)
            self.assertEqual(records[0]["action"], "delete-candidate")

    def test_active_marker_blocks_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "test-running"
            candidate.mkdir()
            (candidate / ".active").write_text("1", encoding="utf-8")
            policy = [{"pattern": "test-*", "label": "TEMP_REPRODUCIBLE", "safe_to_delete": True, "ttl_days": 0, "rebuild": "rerun test"}]
            records = inspect(root, policy, now=time.time() + 86400)
            self.assertEqual(records[0]["action"], "keep")
            self.assertEqual(records[0]["reason"], "active marker present")


if __name__ == "__main__":
    unittest.main()
