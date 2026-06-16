#!/usr/bin/env python3
"""PreToolUse (GLOBAL): claim-before-edit gate for ANY coord-enabled repo.

Why global: sessions often run with cwd = a multi-project hub root while editing
files under a sub-checkout such as <repo>/. A project-local hook in that repo's
.claude/settings.json only
fires when Claude's cwd is inside that repo, so it does NOT cover hub-cwd sessions.
This generic global hook keys off the EDITED FILE PATH, not cwd: if the file lives inside
a repo that has `.claude/coord/guard.py`, it delegates the decision to that repo's guard
(the rule lives WITH the project, versioned in git). No-op for every other path.

Pairs with: <repo>/.claude/coord/{guard.py, work.py, README.md}.
Reuses safety_common for event read + block. FAIL-OPEN on any error.
Bypass: env CLAUDE_COORD_BYPASS=1 (handled inside guard.evaluate).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import allow, read_event  # noqa: E402


def _find_guard(file_path: str) -> Path | None:
    try:
        p = Path(file_path).resolve()
    except (OSError, ValueError):
        return None
    if p.is_file() or not p.exists():
        p = p.parent
    for _ in range(15):
        g = p / ".claude" / "coord" / "guard.py"
        if g.is_file():
            return g
        parent = p.parent
        if parent == p:
            break
        p = parent
    return None


def _load(guard_path: Path):
    spec = importlib.util.spec_from_file_location("coord_guard", str(guard_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def main() -> None:
    event = read_event()
    tool = event.get("tool_name", "")
    if tool not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        allow()

    ti = event.get("tool_input", {})
    if isinstance(ti, str):
        try:
            ti = json.loads(ti)
        except json.JSONDecodeError:
            allow()
    fp = ti.get("file_path") or ti.get("path") or ""
    if not fp:
        allow()

    guard_path = _find_guard(fp)
    if guard_path is None:
        allow()  # not a coord-enabled repo

    try:
        guard = _load(guard_path)
        session = guard.resolve_session(event)
        decision, reason = guard.evaluate(tool, fp, session)
    except Exception:
        allow()  # never block on a delegation/guard bug

    if decision == "block":
        # use the guard's own block channel via safety_common
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        sys.exit(0)
    allow()


if __name__ == "__main__":
    main()
