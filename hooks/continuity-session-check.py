#!/usr/bin/env python3
"""SessionStart reporter for the shared Claude/Codex continuation contract."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

GUARD_PATH = Path(__file__).with_name("continuity-contract-guard.py")
spec = importlib.util.spec_from_file_location("continuity_guard", GUARD_PATH)
assert spec and spec.loader
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def main() -> int:
    root = guard.repo_root_for(Path.cwd())
    if root is None:
        return 0
    contract, path, error = guard.load_contract(root)
    if error:
        print(f"[continuity] BLOCKED: {error} at {path}")
        return 0
    if contract is None:
        if (root / ".claude" / "handoffs").exists() or (root / ".agent").exists():
            print(
                "[continuity] No shared CONTINUITY.json found. Before changing existing "
                "code after another agent, create .claude/continuity/CONTINUITY.json "
                "with baseline, scope, preserve, do_not_redo, and verification."
            )
        return 0

    baseline = contract.get("baseline") or {}
    scope = contract.get("scope") or {}
    print(
        "[continuity] Shared Claude/Codex contract loaded: "
        f"mode={contract.get('mode', 'continuation')}; "
        f"baseline={baseline.get('branch', '?')}@{baseline.get('head', '?')}; "
        f"scope_files={len(scope.get('files') or [])}; "
        f"preserve={len(contract.get('preserve') or [])}; "
        f"do_not_redo={len(contract.get('do_not_redo') or [])}"
    )
    if contract.get("goal"):
        print(f"[continuity] Goal: {str(contract['goal']).strip()[:300]}")
    if contract.get("preserve"):
        print("[continuity] Preserve: " + " | ".join(map(str, contract["preserve"][:5])))
    if contract.get("do_not_redo"):
        print("[continuity] Do not redo: " + " | ".join(map(str, contract["do_not_redo"][:5])))
    print("[continuity] Existing tracked files may not be overwritten with Write in continuation mode.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
