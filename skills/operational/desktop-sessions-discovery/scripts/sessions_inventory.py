#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Claude desktop app sessions inventory.

Scans all <accountId>/<orgId>/local_*.json under
C:\\Users\\<user>\\AppData\\Roaming\\Claude\\claude-code-sessions\\
and prints a compact table grouped by accountId.

Read-only. No writes, no migration. See migrate_session.py for actual move.
"""
from __future__ import annotations
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def storage_root() -> Path:
    """Platform-specific Claude desktop sessions root."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude-code-sessions"
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude-code-sessions"
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude-code-sessions"
    return Path.home() / ".config" / "Claude" / "claude-code-sessions"


ROOT = storage_root()

# Force UTF-8 stdout (Windows cp1252 default would mojibake Cyrillic titles)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def fmt_size(n: int) -> str:
    for unit in ("B", "K", "M", "G"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}T"


def fmt_iso(s) -> str:
    if not s:
        return "?"
    if isinstance(s, (int, float)):
        # Unix ts: ms if > 1e10, else seconds
        ts = s / 1000 if s > 1e10 else s
        try:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(s)
    if isinstance(s, str):
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.astimezone().strftime("%Y-%m-%d %H:%M")
        except Exception:
            return s[:16]
    return str(s)


def parse_session(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:
        return {"error": str(e), "size": path.stat().st_size}
    sid_raw = obj.get("sessionId") or path.stem
    sid_clean = sid_raw.removeprefix("local_")
    return {
        "title": obj.get("title", "(untitled)"),
        "cwd": obj.get("cwd", "?"),
        "last": obj.get("lastActivityAt"),
        "created": obj.get("createdAt"),
        "model": obj.get("model", "?"),
        "turns": obj.get("completedTurns", 0),
        "archived": obj.get("isArchived", False),
        "session_id": sid_clean,
        "size": path.stat().st_size,
    }


def main() -> int:
    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 1

    accounts = sorted([d for d in ROOT.iterdir() if d.is_dir()])
    print(f"# Claude desktop sessions inventory")
    print(f"# Root: {ROOT}")
    print(f"# Accounts found: {len(accounts)}")
    print(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Collect all sessions across all accounts for cross-account view
    all_sessions = []

    for acct_dir in accounts:
        acct_short = acct_dir.name[:8]
        orgs = sorted([d for d in acct_dir.iterdir() if d.is_dir()])

        # Per-account stats
        all_session_files = list(acct_dir.rglob("local_*.json"))
        total_size = sum(p.stat().st_size for p in all_session_files)
        latest = max((p.stat().st_mtime for p in all_session_files), default=0)
        latest_str = datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M") if latest else "(empty)"

        print(f"## Account {acct_short}…  ({len(all_session_files)} sessions, {fmt_size(total_size)}, last {latest_str})")
        print()

        # Sort sessions by lastActivityAt desc (most recent first)
        sessions_meta = []
        for org_dir in orgs:
            for sf in org_dir.glob("local_*.json"):
                meta = parse_session(sf)
                meta["acct"] = acct_short
                meta["org"] = org_dir.name[:8]
                meta["path"] = sf
                sessions_meta.append(meta)

        # Normalize sort key: int/float ts → str ISO via fmt; missing → empty
        def sort_key(m):
            v = m.get("last") or 0
            if isinstance(v, (int, float)):
                return v / 1000 if v > 1e10 else v
            if isinstance(v, str):
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
                except Exception:
                    return 0
            return 0
        sessions_meta.sort(key=sort_key, reverse=True)

        # Print table: date | turns | title | cwd-tail | size
        print(f"  {'last':<16}  {'turns':>5}  {'size':>5}  {'sid':<8}  title  [cwd]")
        print(f"  {'-'*16}  {'-'*5}  {'-'*5}  {'-'*8}  -----")
        for m in sessions_meta:
            last = fmt_iso(m.get("last"))
            turns = m.get("turns", 0)
            sid = m.get("session_id", "?")[:8]
            title = (m.get("title") or "(untitled)")[:60]
            cwd = m.get("cwd", "?")
            cwd_tail = "/".join(cwd.replace("\\", "/").split("/")[-2:]) if cwd != "?" else "?"
            size = fmt_size(m.get("size", 0))
            arch = " [A]" if m.get("archived") else ""
            print(f"  {last:<16}  {turns:>5}  {size:>5}  {sid:<8}  {title}{arch}  [{cwd_tail}]")

        all_sessions.extend(sessions_meta)
        print()

    # Cross-account summary by cwd (which projects appear in which accounts)
    print()
    print("## Cross-account view: same project across multiple accounts?")
    print()
    by_cwd: dict[str, list] = {}
    for m in all_sessions:
        cwd = m.get("cwd", "?")
        cwd_tail = "/".join(cwd.replace("\\", "/").split("/")[-2:]) if cwd != "?" else "?"
        by_cwd.setdefault(cwd_tail, []).append(m)

    multi_acct_projects = {cwd: msgs for cwd, msgs in by_cwd.items() if len({m["acct"] for m in msgs}) > 1}
    if multi_acct_projects:
        print(f"  Projects accessed from multiple accountIds: {len(multi_acct_projects)}")
        for cwd, msgs in sorted(multi_acct_projects.items(), key=lambda kv: -len(kv[1])):
            accts = sorted({m["acct"] for m in msgs})
            print(f"    [{cwd}]: {len(msgs)} sessions across accountIds {accts}")
    else:
        print("  (none — every project lives in exactly one accountId)")
    print()

    print(f"## TOTAL: {len(all_sessions)} sessions across {len(accounts)} accountIds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
