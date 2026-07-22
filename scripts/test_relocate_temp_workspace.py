import os
import tempfile
import unittest
from pathlib import Path

from relocate_temp_workspace import copy_tree, cutover, inventory, verify_copy


class RelocateTempWorkspaceTests(unittest.TestCase):
    def test_copy_and_verify_preserves_all_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            (source / "nested").mkdir(parents=True)
            (source / "one.bin").write_bytes(b"one")
            (source / "nested" / "two.txt").write_text("two", encoding="utf-8")
            expected = inventory(source)
            self.assertEqual(copy_tree(source, target, "python"), "python")
            self.assertEqual(verify_copy(source, target, expected), expected)

    @unittest.skipUnless(os.name == "nt", "junction cutover is Windows-specific")
    def test_cutover_keeps_compatibility_path_and_purges_verified_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            (source / "payload.txt").write_text("payload", encoding="utf-8")
            copy_tree(source, target, "python")
            cutover(source, target, "junction", purge_source=True)
            self.assertTrue(source.is_dir())
            self.assertEqual(source.resolve(), target.resolve())
            self.assertEqual((source / "payload.txt").read_text(encoding="utf-8"), "payload")
            self.assertFalse(any(root.glob("source.relocation-backup-*")))


if __name__ == "__main__":
    unittest.main()
