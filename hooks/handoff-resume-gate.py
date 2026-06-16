#!/usr/bin/env python3
"""SessionStart hook: resume freshness-gate (R1 resumable context, mechanism #2).

session-handoff-check.py *shows* recent handoffs. This complements it by
flagging STALE ones: a handoff older than STALE_DAYS that is still ACTIVE is
a trap -- a resuming session trusts assumptions ("VM up", "Go installed",
"branch X is canon") that may have rotted. Per no-guessing / proof-loop:
re-verify before acting. This hook does NOT re-show content; it emits a short
"verify before trusting" nudge listing the exact claim-bearing lines.

Read-only (emits a reminder; never modifies files) -> multi-session safe.

## Behaviour (SessionStart)
- For each project's LATEST handoff: if age >= STALE_DAYS and not CLOSED/
  ABANDONED -> print a verify-nudge with its Current-state / What-did-NOT-work
  / Next-step lines. Fresh handoffs -> silent (the other hook shows them).
- No handoffs -> silent.

## Self-test
    python handoff-resume-gate.py --self-test
Plants a stale ACTIVE handoff (must flag) + a fresh one (must not); prints
SCANNED: + PASS/FAIL.

## Register (NOT wired by default)
    {"hooks":{"SessionStart":[{"hooks":[{"type":"command",
      "command":"python ~/.claude/claude-code-config/hooks/handoff-resume-gate.py",
      "statusMessage":"Handoff freshness gate..."}]}]}}

## Reference
- ~/.claude/rules/no-guessing.md (verify, do not trust stale state)
- ~/.claude/rules/session-handoff.md ; registry/R1-resumable-context-audit.md
"""
from __future__ import annotations

import re
import sys
import tempfile
import time
from pathlib import Path

STALE_DAYS = 3
TS_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:_(\d{2})-(\d{2}))?")
DEAD_STATES = ("CLOSED", "ABANDONED", "RESOLVED", "SUPERSEDE")
# Lines whose claims a resuming session must re-verify.
CLAIM_HEADINGS = ("current state", "what did not", "what didn't", "next step",
                  "blocked", "verification")


def file_ts(path: Path) -> float:
    m = TS_RE.match(path.name)
    if m:
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            hh = int(m.group(4)) if m.group(4) else 0
            mm = int(m.group(5)) if m.group(5) else 0
            return time.mktime((y, mo, d, hh, mm, 0, 0, 0, -1))
        except (ValueError, OverflowError):
            pass
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def latest_per_project(handoffs_dir: Path) -> dict:
    """{project_slug: latest .md Path} from .claude/handoffs/<slug>/*.md."""
    out: dict = {}
    if not handoffs_dir.is_dir():
        return out
    for sub in handoffs_dir.iterdir():
        if not sub.is_dir() or sub.name in ("archive", "_graph"):
            continue
        mds = [p for p in sub.glob("*.md") if p.name.upper() != "INDEX.MD"]
        if not mds:
            continue
        out[sub.name] = max(mds, key=file_ts)
    return out


def is_dead(text: str) -> bool:
    head = text[:1200].upper()
    # Look for a Status: ... CLOSED/ABANDONED line near the top.
    m = re.search(r"STATUS[:*\s]+([A-Z\-]+)", head)
    if m and any(m.group(1).startswith(s) for s in DEAD_STATES):
        return True
    return False


def claim_lines(text: str, limit: int = 6) -> list[str]:
    lines = text.split("\n")
    picked: list[str] = []
    grab = False
    for ln in lines:
        low = ln.strip().lower()
        if low.startswith("#"):
            grab = any(h in low for h in CLAIM_HEADINGS)
            continue
        if grab and ln.strip() and not ln.strip().startswith("#"):
            picked.append(ln.strip())
            if len(picked) >= limit:
                break
    return picked


def assess(handoffs_dir: Path, now: float) -> list[str]:
    msgs: list[str] = []
    for slug, path in sorted(latest_per_project(handoffs_dir).items()):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        age_days = (now - file_ts(path)) / 86400.0
        if age_days < STALE_DAYS or is_dead(text):
            continue
        claims = claim_lines(text)
        block = ["[resume-gate] STALE handoff for '%s' (%.0fd old, still ACTIVE): %s"
                 % (slug, age_days, path.name),
                 "  Verify these claims against CURRENT reality before trusting (no-guessing):"]
        for c in claims[:5]:
            block.append("   - " + (c[:140]))
        if not claims:
            block.append("   - (no Current-state/Next-step section found; read the file fully)")
        msgs.append("\n".join(block))
    return msgs


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        now = time.time()
        stale_day = time.strftime("%Y-%m-%d", time.localtime(now - 6 * 86400))
        fresh_day = time.strftime("%Y-%m-%d", time.localtime(now - 1 * 86400))
        (root / "projA").mkdir(parents=True)
        (root / "projA" / ("%s_10-00_aaaa.md" % stale_day)).write_text(
            "# Handoff\n**Status:** ACTIVE\n## Current state\n- VM up at 1.2.3.4\n- branch X is canon\n",
            encoding="utf-8")
        (root / "projB").mkdir(parents=True)
        (root / "projB" / ("%s_10-00_bbbb.md" % fresh_day)).write_text(
            "# Handoff\n**Status:** ACTIVE\n## Current state\n- fresh, do not flag\n",
            encoding="utf-8")
        (root / "projC").mkdir(parents=True)
        (root / "projC" / ("%s_09-00_cccc.md" % stale_day)).write_text(
            "# Handoff\n**Status:** CLOSED\n## Current state\n- old but closed, skip\n",
            encoding="utf-8")
        msgs = assess(root, now)
        flagged = " ".join(msgs)
        ok = ("projA" in flagged) and ("projB" not in flagged) and ("projC" not in flagged)
        print("SCANNED: handoffs_assessed=3 flagged=%d" % len(msgs))
        if not ok:
            print("[ERR] self-test FAILED: %r" % msgs)
            return 1
        print("[OK] handoff-resume-gate self-test passed (stale flagged, fresh+closed skipped)")
        return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    # stdin event is ignored (SessionStart payload not needed); read+discard.
    try:
        sys.stdin.read()
    except OSError:
        pass
    handoffs_dir = Path.cwd() / ".claude" / "handoffs"
    msgs = assess(handoffs_dir, time.time())
    if msgs:
        print("\n".join(msgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
