#!/usr/bin/env python3
"""Relocate a Windows temp workspace with capacity and copy verification."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path


WINDOWS_REPARSE_POINT = 0x400
DEFAULT_RESERVE_BYTES = 1 << 30


@dataclass(frozen=True)
class Inventory:
    files: int
    bytes: int


def inventory(root: Path) -> Inventory:
    files = 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        files += 1
        total += path.stat().st_size
    return Inventory(files, total)


def ensure_capacity(source: Path, target_parent: Path, reserve_bytes: int) -> tuple[Inventory, int]:
    source_inventory = inventory(source)
    free_bytes = shutil.disk_usage(target_parent).free
    required_bytes = source_inventory.bytes + reserve_bytes
    if free_bytes < required_bytes:
        raise RuntimeError(
            f"insufficient free space: need={required_bytes} free={free_bytes} "
            f"source_bytes={source_inventory.bytes} reserve={reserve_bytes}"
        )
    return source_inventory, free_bytes


def validate_paths(source: Path, target: Path) -> None:
    source = source.resolve()
    target = target.resolve(strict=False)
    if not source.is_dir() or source.is_symlink():
        raise ValueError(f"source must be a real directory: {source}")
    if source == target:
        raise ValueError("source and target must be different")
    try:
        target.relative_to(source)
    except ValueError:
        return
    raise ValueError("target must not be inside source")


def copy_with_robocopy(source: Path, target: Path) -> int:
    command = [
        "robocopy",
        str(source),
        str(target),
        "/E",
        "/COPY:DAT",
        "/DCOPY:DAT",
        "/XJ",
        "/R:1",
        "/W:1",
        "/NP",
        "/NFL",
        "/NDL",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode > 7:
        raise RuntimeError(f"robocopy failed with exit code {completed.returncode}: {completed.stderr[-500:]}")
    return completed.returncode


def copy_with_python(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, copy_function=shutil.copy2)


def copy_tree(source: Path, target: Path, engine: str) -> str:
    target.mkdir(parents=True, exist_ok=True)
    if engine in {"auto", "robocopy"} and os.name == "nt":
        copy_with_robocopy(source, target)
        return "robocopy"
    if engine == "robocopy":
        raise RuntimeError("robocopy engine is available only on Windows")
    copy_with_python(source, target)
    return "python"


def verify_copy(source: Path, target: Path, expected: Inventory) -> Inventory:
    current = inventory(source)
    if current != expected:
        raise RuntimeError(f"source changed during copy: before={expected} after={current}")
    target_inventory = inventory(target)
    if target_inventory.files < expected.files or target_inventory.bytes < expected.bytes:
        raise RuntimeError(f"target is incomplete: source={expected} target={target_inventory}")
    for source_path in source.rglob("*"):
        if not source_path.is_file() or source_path.is_symlink():
            continue
        relative = source_path.relative_to(source)
        target_path = target / relative
        if not target_path.is_file() or target_path.stat().st_size != source_path.stat().st_size:
            raise RuntimeError(f"target mismatch: {relative}")
    return target_inventory


def is_directory_link(path: Path) -> bool:
    if os.name != "nt":
        return path.is_symlink()
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attributes & WINDOWS_REPARSE_POINT)


def create_compat_link(link: Path, target: Path, kind: str) -> None:
    if kind == "junction" and os.name != "nt":
        raise RuntimeError("junction links are supported only on Windows")
    if kind == "junction":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"mklink failed: {completed.stderr or completed.stdout}")
    else:
        link.symlink_to(target, target_is_directory=True)
    if not is_directory_link(link) or link.resolve() != target.resolve():
        raise RuntimeError(f"compatibility link verification failed: {link} -> {target}")


def cutover(source: Path, target: Path, kind: str, purge_source: bool) -> Path | None:
    backup = source.with_name(f"{source.name}.relocation-backup-{uuid.uuid4().hex[:8]}")
    source.rename(backup)
    try:
        create_compat_link(source, target, kind)
    except Exception:
        if source.exists() and is_directory_link(source):
            source.rmdir()
        backup.rename(source)
        raise
    if not purge_source:
        return backup
    shutil.rmtree(backup)
    if backup.exists():
        raise RuntimeError(f"backup removal verification failed: {backup}")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--engine", choices=("auto", "robocopy", "python"), default="auto")
    parser.add_argument("--link", choices=("junction", "symlink"), default="junction")
    parser.add_argument("--reserve-gib", type=float, default=1.0)
    parser.add_argument("--apply", action="store_true", help="copy and verify; without this flag only report")
    parser.add_argument("--purge-source", action="store_true", help="remove the verified source after link cutover")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    source = args.source.resolve()
    target = args.target.resolve(strict=False)
    validate_paths(source, target)
    if args.purge_source and not args.apply:
        raise SystemExit("--purge-source requires --apply")
    target.parent.mkdir(parents=True, exist_ok=True)
    expected, free_bytes = ensure_capacity(source, target.parent, int(args.reserve_gib * (1 << 30)))
    result: dict[str, object] = {
        "source": str(source),
        "target": str(target),
        "source_files": expected.files,
        "source_bytes": expected.bytes,
        "target_free_bytes_before": free_bytes,
        "apply": args.apply,
        "purge_source": args.purge_source,
        "link": args.link,
    }
    if args.apply:
        result["engine"] = copy_tree(source, target, args.engine)
        result["target_inventory"] = inventory(target).__dict__
        verify_copy(source, target, expected)
        result["backup"] = str(cutover(source, target, args.link, args.purge_source) or "")
        result["link_verified"] = source.resolve() == target.resolve()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(
            f"relocate: source_files={expected.files} source_bytes={expected.bytes} "
            f"apply={args.apply} purge_source={args.purge_source}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
