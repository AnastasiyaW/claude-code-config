#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Restore one Claude desktop session into the active accountId.

Active accountId = directory with the most recently modified local_*.json
(heuristic — print and confirm via --dry-run before commit).

Usage:
    python sessions_restore.py <sessionId-8-or-full>           # auto-detect active acct
    python sessions_restore.py <sessionId> --to <acct-prefix>  # explicit target
    python sessions_restore.py <sessionId> --dry-run            # show what would happen

Behaviour:
    1. Find source session across all accountIds (by sessionId substring)
    2. Detect or use --to active accountId
    3. Copy local_<full-id>.json into <activeAcct>/<sameOrgId>/
       (if target orgId folder doesn't exist — create it)
    4. Verify by reading back and comparing bytes
    5. Append to ~/.claude/desktop-migrations.jsonl audit log
    6. Print restart-app reminder

Source file is NEVER deleted. Original stays as backup.
"""
from __future__ import annotations
import argparse
import io
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def storage_root() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude-code-sessions"
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude-code-sessions"
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude-code-sessions"
    return Path.home() / ".config" / "Claude" / "claude-code-sessions"


ROOT = storage_root()
AUDIT_LOG = Path.home() / ".claude" / "desktop-migrations.jsonl"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def find_session(query: str) -> list[Path]:
    q = query.lower()
    found = []
    for acct in ROOT.iterdir():
        if not acct.is_dir():
            continue
        for f in acct.rglob("local_*.json"):
            sid = f.stem.replace("local_", "").lower()
            if q in sid:
                found.append(f)
    return found


def detect_active_acct() -> str | None:
    best = (0.0, None)
    for acct in ROOT.iterdir():
        if not acct.is_dir():
            continue
        latest = max((f.stat().st_mtime for f in acct.rglob("local_*.json")), default=0)
        if latest > best[0]:
            best = (latest, acct.name)
    return best[1]


def append_audit(entry: dict) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session_id", help="sessionId substring (8 chars usually enough)")
    ap.add_argument("--to", help="target accountId prefix (default: auto-detect active)")
    ap.add_argument("--dry-run", action="store_true", help="show plan, don't copy")
    args = ap.parse_args()

    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 1

    matches = find_session(args.session_id)
    if not matches:
        print(f"ERROR: no session matching {args.session_id!r}", file=sys.stderr)
        return 2
    if len(matches) > 1:
        print(f"ERROR: ambiguous, {len(matches)} matches:", file=sys.stderr)
        for m in matches:
            print(f"   {m}", file=sys.stderr)
        print("Pass more characters of sessionId to disambiguate.", file=sys.stderr)
        return 3

    src = matches[0]
    src_acct = src.parent.parent.name
    src_org = src.parent.name
    src_sid = src.stem.replace("local_", "")

    if args.to:
        target_acct = next(
            (d.name for d in ROOT.iterdir() if d.is_dir() and d.name.startswith(args.to)),
            None,
        )
        if not target_acct:
            print(f"ERROR: no accountId starting with {args.to!r}", file=sys.stderr)
            return 4
    else:
        target_acct = detect_active_acct()
        if not target_acct:
            print("ERROR: cannot detect active accountId", file=sys.stderr)
            return 5

    if target_acct == src_acct:
        print(f"NOOP: session is already in target accountId {target_acct[:8]}", file=sys.stderr)
        return 0

    target_acct_dir = ROOT / target_acct
    target_orgs = [d.name for d in target_acct_dir.iterdir() if d.is_dir()]
    if src_org in target_orgs:
        target_org = src_org
    elif target_orgs:
        target_org = target_orgs[0]
    else:
        target_org = src_org

    target_dir = target_acct_dir / target_org
    target_path = target_dir / src.name

    try:
        with src.open(encoding="utf-8") as f:
            meta = json.load(f)
        title = meta.get("title", "(no title)")
    except Exception:
        title = "(parse error)"

    print(f"# Restore plan:")
    print(f"#   sessionId:  {src_sid}")
    print(f"#   title:      {title}")
    print(f"#   from:       {src_acct[:8]}/{src_org[:8]}/")
    print(f"#   to:         {target_acct[:8]}/{target_org[:8]}/")
    print(f"#   src bytes:  {src.stat().st_size}")

    if args.dry_run:
        print("# --dry-run: no copy performed")
        return 0

    if target_path.exists():
        print(f"ERROR: target already exists: {target_path}", file=sys.stderr)
        print("       Refusing to overwrite. Delete it first if you really want to re-copy.", file=sys.stderr)
        return 6

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target_path)

    if not target_path.exists():
        print(f"ERROR: copy did not produce target file", file=sys.stderr)
        return 7
    src_bytes = src.read_bytes()
    target_bytes = target_path.read_bytes()
    if src_bytes != target_bytes:
        target_path.unlink(missing_ok=True)
        print(f"ERROR: byte mismatch after copy, removed target", file=sys.stderr)
        return 8

    append_audit(
        {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "session_id": src_sid,
            "title": title,
            "from_acct": src_acct,
            "from_org": src_org,
            "to_acct": target_acct,
            "to_org": target_org,
            "bytes": src.stat().st_size,
        }
    )

    print(f"OK: copied {src.stat().st_size} bytes")
    print(f"    src kept as backup: {src}")
    print(f"    target: {target_path}")
    print()
    print("# REMINDER: restart Claude desktop app to see the restored session")
    print("# AUDIT: ", AUDIT_LOG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
