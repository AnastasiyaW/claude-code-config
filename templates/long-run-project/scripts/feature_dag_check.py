#!/usr/bin/env python3
"""
feature_dag_check.py — validate the dependency DAG + WIP/VCR invariants of a
long-run project's feature_list.json.

The schema already allows `dependencies: []` and the 4-state status with the
WIP=1 invariant, but nothing *enforces* it. This validator does:

  HARD failures (exit 2):
    - dependency referencing a non-existent feature id
    - a dependency cycle (the DAG is not acyclic)
    - WIP>1 (more than one feature 'in-progress' — violates WIP=1)
    - duplicate feature ids
    - id not matching feat-NNN pattern

  SOFT warnings (exit 0, but reported):
    - status='done' with empty 'evidence' (proof-loop: no artifact = not done)
    - status='blocked' with empty 'evidence' (no named blocker)
    - a 'not-started' feature whose deps are all 'done' but nothing is
      in-progress (a ready feature is idle)

  Also prints:
    - READY: not-started features whose dependencies are all 'done'
      (VCR: these are the legal next features to start)

Usage:
    python feature_dag_check.py [path/to/feature_list.json]
Defaults to ./feature_list.json. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys

ID_RE = re.compile(r"^feat-\d{3,}$")
DONE, INPROG, BLOCKED, NOTSTARTED = "done", "in-progress", "blocked", "not-started"
VALID_STATUS = {DONE, INPROG, BLOCKED, NOTSTARTED}


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    feats = data.get("features", [])
    if not isinstance(feats, list):
        raise ValueError("'features' must be an array")
    return feats


def find_cycle(graph):
    """Return a cycle as a list of ids, or None. graph: {id: [dep_ids]}."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack = []

    def dfs(n):
        color[n] = GRAY
        stack.append(n)
        for m in graph.get(n, []):
            if m not in color:
                continue  # missing ref handled elsewhere
            if color[m] == GRAY:
                return stack[stack.index(m):] + [m]
            if color[m] == WHITE:
                c = dfs(m)
                if c:
                    return c
        color[n] = BLACK
        stack.pop()
        return None

    for n in graph:
        if color[n] == WHITE:
            c = dfs(n)
            if c:
                return c
    return None


def check(path):
    feats = load(path)
    errors, warnings = [], []

    ids = [f.get("id") for f in feats]
    by_id = {}
    for f in feats:
        fid = f.get("id")
        if fid in by_id:
            errors.append(f"duplicate feature id: {fid}")
        by_id[fid] = f
        if not fid or not ID_RE.match(str(fid)):
            errors.append(f"id not in feat-NNN format: {fid!r}")
        st = f.get("status")
        if st not in VALID_STATUS:
            errors.append(f"{fid}: invalid status {st!r} (allowed: {sorted(VALID_STATUS)})")

    # dependency refs
    graph = {}
    for f in feats:
        fid = f.get("id")
        deps = f.get("dependencies", []) or []
        graph[fid] = deps
        for d in deps:
            if d not in by_id:
                errors.append(f"{fid}: depends on non-existent feature {d!r}")

    # cycle
    cyc = find_cycle({k: [d for d in v if d in by_id] for k, v in graph.items()})
    if cyc:
        errors.append("dependency cycle: " + " -> ".join(cyc))

    # WIP=1
    inprog = [f.get("id") for f in feats if f.get("status") == INPROG]
    if len(inprog) > 1:
        errors.append(f"WIP>1 violation: {len(inprog)} features in-progress: {inprog}")

    # evidence soft checks
    for f in feats:
        fid, st = f.get("id"), f.get("status")
        ev = (f.get("evidence") or "").strip()
        if st == DONE and not ev:
            warnings.append(f"{fid}: status=done but evidence empty (proof-loop: no artifact = not done)")
        if st == BLOCKED and not ev:
            warnings.append(f"{fid}: status=blocked but evidence empty (name the blocker)")

    # readiness (VCR): not-started with all deps done
    def deps_done(f):
        return all(by_id.get(d, {}).get("status") == DONE for d in (f.get("dependencies") or []))

    ready = [f.get("id") for f in feats if f.get("status") == NOTSTARTED and deps_done(f)]
    if ready and not inprog:
        warnings.append(f"no feature in-progress but {len(ready)} ready to start: {ready}")

    return errors, warnings, ready, inprog


def main(argv=None):
    argv = argv or sys.argv[1:]
    path = argv[0] if argv else "feature_list.json"
    try:
        errors, warnings, ready, inprog = check(path)
    except FileNotFoundError:
        print(f"[feature-dag] file not found: {path}", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[feature-dag] cannot parse {path}: {e}", file=sys.stderr)
        return 2

    print(f"== feature_list DAG check: {path} ==")
    print(f"in-progress: {inprog or '(none)'}")
    print(f"READY to start (deps all done): {ready or '(none)'}")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    if errors:
        print(f"\n{len(errors)} hard violation(s).")
        return 2
    print("\nDAG valid. WIP=1 OK." + (f" {len(warnings)} warning(s)." if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
