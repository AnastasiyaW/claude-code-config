#!/usr/bin/env python3
"""Report and safely clean explicitly approved temporary workspace entries.

The default is a dry run. Automatic cleanup requires a policy entry with:
safe_to_delete=true, a rebuild description, and an age beyond ttl_days.
Unknown files and folders are always kept and reported for review.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import sys
import time
from pathlib import Path


ALLOWED_LABELS = {"TEMP_REPRODUCIBLE", "CACHE_GENERATED", "ARTIFACT_REGENERABLE"}
LOCK_NAMES = {".active", ".in-use", ".lock", "RUNNING", "running.pid"}


def load_policy(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("policy must be a JSON list")
    result = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
            raise ValueError("each policy entry needs a string pattern")
        result.append(item)
    return result


def matching_policy(name: str, policies: list[dict[str, object]]) -> dict[str, object] | None:
    for policy in policies:
        if fnmatch.fnmatchcase(name, str(policy["pattern"])):
            return policy
    return None


def has_active_marker(path: Path) -> bool:
    if path.is_dir():
        return any((path / marker).exists() for marker in LOCK_NAMES)
    return False


def age_days(path: Path, now: float) -> float:
    return max(0.0, (now - path.stat().st_mtime) / 86400.0)


def inspect(root: Path, policies: list[dict[str, object]], now: float | None = None) -> list[dict[str, object]]:
    now = time.time() if now is None else now
    records = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if path.name in {".folder-meta.json", "cleanup-policy.json"}:
            continue
        policy = matching_policy(path.name, policies)
        record: dict[str, object] = {
            "path": str(path),
            "name": path.name,
            "kind": "dir" if path.is_dir() else "file",
            "age_days": round(age_days(path, now), 2),
            "action": "keep",
            "reason": "unlabelled or no matching policy",
        }
        if policy is None:
            records.append(record)
            continue
        label = str(policy.get("label", "")).upper()
        ttl = float(policy.get("ttl_days", 14))
        safe = bool(policy.get("safe_to_delete", False))
        rebuild = str(policy.get("rebuild", "")).strip()
        record.update({"pattern": policy["pattern"], "label": label, "ttl_days": ttl})
        if label not in ALLOWED_LABELS or not safe:
            record["reason"] = "policy is not deletion-approved"
        elif not rebuild:
            record["reason"] = "policy has no rebuild/source-of-truth description"
        elif has_active_marker(path):
            record["reason"] = "active marker present"
        elif float(record["age_days"]) < ttl:
            record["reason"] = "younger than policy TTL"
        else:
            record["action"] = "delete-candidate"
            record["reason"] = "approved label, rebuild path, TTL, and no active marker"
        records.append(record)
    return records


def apply_cleanup(records: list[dict[str, object]]) -> list[str]:
    deleted: list[str] = []
    for record in records:
        if record["action"] != "delete-candidate":
            continue
        path = Path(str(record["path"])).resolve()
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
        if path.exists():
            raise RuntimeError(f"cleanup verification failed: {path}")
        deleted.append(str(path))
    return deleted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="delete only approved stale candidates")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    policy_path = args.policy.resolve()
    if not root.is_dir():
        raise SystemExit(f"root is not a directory: {root}")
    records = inspect(root, load_policy(policy_path))
    deleted = apply_cleanup(records) if args.apply else []
    result = {"root": str(root), "policy": str(policy_path), "dry_run": not args.apply, "records": records, "deleted": deleted}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        candidates = sum(1 for item in records if item["action"] == "delete-candidate")
        print(f"temp cleanup: root={root} candidates={candidates} deleted={len(deleted)} dry_run={not args.apply}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
