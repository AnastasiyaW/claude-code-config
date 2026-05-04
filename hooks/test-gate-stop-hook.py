#!/usr/bin/env python3
"""Stop hook: block task completion until tests are green.

Behavioural enforcement layer for the "fix or ticket" pattern. CLAUDE.md
rules can be ignored under context pressure (compliance decay; Jaroslawicz
et al. 2025). This hook works at the structural layer: it runs the project
test suite at every Stop event and blocks if anything is red. The agent
cannot say "done" while tests fail — that claim is now physically false.

Companion to stop-phrase-guard.py (phrase-level detection) and
problems-md-validator.py (PROBLEMS.md ticket discipline). Together they
implement Layer 2-4 of the no-pre-existing-evasion stack.

## Detection order

1. Project override file `.claude/test-command` (literal command, one line)
2. JS/TS via `package.json` "test" script (pnpm > yarn > bun > npm)
3. Python via `pytest.ini` / `pyproject.toml` / `tests/`
4. Rust via `Cargo.toml`
5. Go via `go.mod`

If none detected → silent pass (graceful for non-code dirs).

## Behaviour

- Returncode 0 from test command → silent pass
- Returncode != 0 → emit JSON `{"decision": "block", "reason": "..."}` with
  the tail of the test output. The agent must fix or explicitly bypass.
- `stop_hook_active=true` → silent pass (anti-loop guard, REQUIRED)
- Timeout reached → log + silent pass (don't trap user in long suites)

## Bypass

- env var `CLAUDE_SKIP_TEST_GATE=1` → silent pass
- file `.claude/.skip-test-gate` (project-level) → silent pass
- delete the marker / unset the env var to re-enable

## Register

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/test-gate-stop-hook.py",
        "statusMessage": "Test gate (no-pre-existing-evasion Layer 2)..."
      }]
    }]
  }
}
```

## Tunables

- `TEST_TIMEOUT_SEC` - kill long suites (default 180s)
- `MAX_OUTPUT_BYTES` - cap injected output to keep agent context clean
- `MIN_SESSION_MINUTES` - skip on very short sessions (just opened)

## Reference

- Principle 26: docs/principles/26-no-pre-existing-evasion.md
- bradfeld "fix or ticket" pattern (5 valid exceptions)
- GitHub issue anthropics/claude-code#42796 (origin investigation)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

TEST_TIMEOUT_SEC = 180
MAX_OUTPUT_BYTES = 4000
MIN_SESSION_MINUTES = 2


def detect_test_command(cwd: Path) -> tuple[list[str], str] | None:
    """Detect what test command to run. Returns (cmd_list, label) or None."""

    override = cwd / ".claude" / "test-command"
    if override.exists() and override.is_file():
        cmd_str = override.read_text(encoding="utf-8").strip()
        if cmd_str and not cmd_str.startswith("#"):
            return (cmd_str.split(), f"override({cmd_str})")

    pkg_json = cwd / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "test" in pkg.get("scripts", {}):
                if (cwd / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
                    return (["pnpm", "test"], "pnpm test")
                if (cwd / "yarn.lock").exists() and shutil.which("yarn"):
                    return (["yarn", "test"], "yarn test")
                if (cwd / "bun.lockb").exists() and shutil.which("bun"):
                    return (["bun", "test"], "bun test")
                if shutil.which("npm"):
                    return (["npm", "test", "--silent"], "npm test")
        except (json.JSONDecodeError, OSError):
            pass

    if (cwd / "pytest.ini").exists() or (cwd / "pyproject.toml").exists() or (cwd / "tests").is_dir():
        if shutil.which("pytest"):
            return (["pytest", "--tb=short", "-q"], "pytest")

    if (cwd / "Cargo.toml").exists() and shutil.which("cargo"):
        return (["cargo", "test", "--quiet"], "cargo test")

    if (cwd / "go.mod").exists() and shutil.which("go"):
        return (["go", "test", "./..."], "go test")

    return None


def session_age_minutes(claude_dir: Path) -> float:
    marker = claude_dir / ".session-start"
    if marker.exists():
        return (time.time() - marker.stat().st_mtime) / 60
    return 999


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return 0

    if event.get("stop_hook_active"):
        return 0

    if os.environ.get("CLAUDE_SKIP_TEST_GATE"):
        return 0

    cwd = Path.cwd()

    if (cwd / ".claude" / ".skip-test-gate").exists():
        return 0

    claude_dir = cwd / ".claude"
    if claude_dir.exists() and session_age_minutes(claude_dir) < MIN_SESSION_MINUTES:
        return 0

    detected = detect_test_command(cwd)
    if detected is None:
        return 0

    cmd, label = detected

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            timeout=TEST_TIMEOUT_SEC,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        print(f"[test-gate] {label} timeout after {TEST_TIMEOUT_SEC}s - skipping",
              file=sys.stderr)
        return 0
    except (FileNotFoundError, OSError) as e:
        print(f"[test-gate] {label} unavailable: {e}", file=sys.stderr)
        return 0

    if result.returncode == 0:
        return 0

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if len(output) > MAX_OUTPUT_BYTES:
        output = output[-MAX_OUTPUT_BYTES:]

    reason = (
        f"Test gate failed ({label}, exit {result.returncode}). "
        f"Cannot complete task while tests are red. "
        f"Per no-pre-existing-evasion rule: tests must be green before 'done'.\n\n"
        f"Output (tail {MAX_OUTPUT_BYTES} bytes):\n{output}\n\n"
        f"Options:\n"
        f"1. Fix the failures (preferred)\n"
        f"2. If failures are in genuinely unfixable area: add to PROBLEMS.md "
        f"with one of 5-exception reasons (missing-data, missing-dep, "
        f"arch-decision, scope-explosion, inaccessible-repo) and create "
        f".claude/.skip-test-gate for this session\n"
        f"3. Bypass: CLAUDE_SKIP_TEST_GATE=1 (only for emergency)"
    )

    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
