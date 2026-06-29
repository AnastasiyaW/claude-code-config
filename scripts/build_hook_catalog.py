#!/usr/bin/env python3
"""Build a readable catalog of configured Codex hooks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def hook_rows(source: str, path: Path, config: dict) -> list[dict]:
    rows: list[dict] = []
    hooks = config.get("hooks", {})
    if not isinstance(hooks, dict):
        return rows
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            continue
        for group_index, group in enumerate(groups, start=1):
            if not isinstance(group, dict):
                continue
            matcher = group.get("matcher") or "*"
            for hook_index, hook in enumerate(group.get("hooks", []), start=1):
                if not isinstance(hook, dict):
                    continue
                command = str(hook.get("command") or "")
                status = str(hook.get("statusMessage") or "").strip()
                rows.append(
                    {
                        "source": source,
                        "file": str(path),
                        "event": event,
                        "matcher": matcher,
                        "group": group_index,
                        "hook": hook_index,
                        "statusMessage": status,
                        "hasReadableName": bool(status),
                        "command": command,
                    }
                )
    return rows


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="reports/hooks/hook-catalog.json")
    parser.add_argument("--user-hooks", default=str(Path.home() / ".codex" / "hooks.json"))
    parser.add_argument("--plugin-cache", default=str(Path.home() / ".codex" / "plugins" / "cache"))
    args = parser.parse_args()

    rows: list[dict] = []
    user_hooks = Path(args.user_hooks)
    data = load_json(user_hooks)
    if data is not None:
        rows.extend(hook_rows("user", user_hooks, data))

    plugin_cache = Path(args.plugin_cache)
    if plugin_cache.exists():
        for path in sorted(plugin_cache.rglob("hooks/hooks.json")):
            data = load_json(path)
            if data is not None:
                rows.extend(hook_rows("plugin", path, data))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total": len(rows),
        "withoutReadableName": sum(1 for row in rows if not row["hasReadableName"]),
        "rows": rows,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"total": payload["total"], "withoutReadableName": payload["withoutReadableName"], "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
