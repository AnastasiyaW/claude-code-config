#!/usr/bin/env python3
"""Regression tests for validate_agent_tickets.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "validate_agent_tickets.py"


GOOD = """# TICKET-001 Demo Slice

## Status
ready-for-agent

## Parent
Local eval

## What To Build
Add one narrow end-to-end path that writes a marker and reads it back.

## Acceptance Criteria
- [ ] Marker write is visible through the public command.
- [ ] Marker read reports the expected value.

## Verification
Run: python scripts/verify_marker_roundtrip.py

## Blocked By
None

## Notes
Tracer bullet; not a full subsystem rewrite.
"""


BAD = """# TICKET-001 Bad

## Status
draft

## Parent
Local eval

## What To Build
Implement all backend.

## Acceptance Criteria
Done.

## Verification
Check it.

## Blocked By

## Notes
Bad on purpose.
"""


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--tickets-dir", str(path)],
        text=True,
        capture_output=True,
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        good_dir = root / "good"
        bad_dir = root / "bad"
        good_dir.mkdir()
        bad_dir.mkdir()
        (good_dir / "TICKET-001-demo.md").write_text(GOOD, encoding="utf-8")
        (bad_dir / "TICKET-001-bad.md").write_text(BAD, encoding="utf-8")

        good = run_validator(good_dir)
        assert good.returncode == 0, good.stdout + good.stderr
        assert "OK (1 tickets)" in good.stdout

        bad = run_validator(bad_dir)
        assert bad.returncode == 1, bad.stdout + bad.stderr
        assert "horizontal layer slice" in bad.stdout
        assert "status must contain ready-for-agent" in bad.stdout
        assert "acceptance criteria" in bad.stdout

    print("test_validate_agent_tickets: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
