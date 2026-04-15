#!/usr/bin/env python3
"""Reasoning-quality metrics computed from Claude Code session transcripts.

Reproduces the metrics from the AMD investigation of the Feb-Apr 2026 Claude
Code regression (issue #42796). Run periodically (weekly) to track trend; flag
when any metric crosses its degraded threshold.

Input: Claude Code stores session transcripts as JSONL files under
    ~/.claude/projects/<project-slug>/<session-id>.jsonl
This script scans them, computes per-session metrics, and aggregates.

Metrics computed:
  1. Read:Edit ratio           healthy 5-7, degraded < 3
  2. Research:Mutation ratio   healthy > 8, degraded < 3
  3. Edits-without-prior-Read  healthy < 10%, degraded > 30%
  4. Reasoning-loop rate       healthy < 10 per 1K calls, degraded > 20
  5. User-interrupt rate       healthy < 2 per 1K calls, degraded > 10
  6. Write% of mutations       healthy < 5%, degraded > 10%

Usage:
  python scripts/reasoning_metrics.py                    # last 7 days, all projects
  python scripts/reasoning_metrics.py --days 30          # last 30 days
  python scripts/reasoning_metrics.py --project <slug>   # one project only
  python scripts/reasoning_metrics.py --json             # machine-readable output
  python scripts/reasoning_metrics.py --csv              # CSV for spreadsheet

The metric thresholds come from the AMD investigation's healthy-vs-regressed
comparison. Treat them as starting points and recalibrate for your baseline.

Reference: https://github.com/anthropics/claude-code/issues/42796
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PROJECTS_DIR = HOME / ".claude" / "projects"

# Loop-indicator phrases (lowercase) - backtracking / reconsidering
LOOP_PHRASES = [
    "oh wait",
    "actually,",
    "actually let me",
    "let me reconsider",
    "on second thought",
    "wait, that's not",
    "hmm, actually",
    "let me rethink",
]

# Tool classifications
READ_TOOLS = {"Read", "Grep", "Glob", "NotebookRead"}
EDIT_TOOLS = {"Edit", "MultiEdit", "NotebookEdit"}
WRITE_TOOLS = {"Write"}
RESEARCH_TOOLS = READ_TOOLS | {"WebFetch", "WebSearch"}
MUTATION_TOOLS = EDIT_TOOLS | WRITE_TOOLS

THRESHOLDS = {
    "read_edit_ratio": {"healthy_min": 5.0, "degraded_max": 3.0, "higher_better": True},
    "research_mutation_ratio": {"healthy_min": 8.0, "degraded_max": 3.0, "higher_better": True},
    "edits_without_read_pct": {"healthy_max": 10.0, "degraded_min": 30.0, "higher_better": False},
    "loop_rate_per_1k": {"healthy_max": 10.0, "degraded_min": 20.0, "higher_better": False},
    "interrupt_rate_per_1k": {"healthy_max": 2.0, "degraded_min": 10.0, "higher_better": False},
    "write_pct_of_mutations": {"healthy_max": 5.0, "degraded_min": 10.0, "higher_better": False},
}


def parse_message(line: str) -> dict | None:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    return obj


def extract_assistant_text(obj: dict) -> str:
    """Pull text content out of an assistant message in Anthropic block format."""
    msg = obj.get("message") or obj
    if msg.get("role") != "assistant":
        return ""
    content = msg.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
        return "\n".join(parts)
    return ""


def extract_tool_use(obj: dict) -> tuple[str, str | None] | None:
    """If obj is an assistant tool_use block, return (tool_name, target_path_if_applicable)."""
    msg = obj.get("message") or obj
    if msg.get("role") != "assistant":
        return None
    content = msg.get("content", [])
    if not isinstance(content, list):
        return None
    for b in content:
        if not isinstance(b, dict):
            continue
        if b.get("type") != "tool_use":
            continue
        name = b.get("name", "")
        inp = b.get("input") or {}
        path = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
        return (name, path)
    return None


def is_user_interrupt(obj: dict) -> bool:
    """Heuristic: user messages mid-session that correct the agent."""
    msg = obj.get("message") or obj
    if msg.get("role") != "user":
        return False
    content = msg.get("content", "")
    if isinstance(content, list):
        content = "\n".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    if not isinstance(content, str):
        return False
    lower = content.lower()
    interrupt_markers = [
        "no,",
        "wait,",
        "stop",
        "that's wrong",
        "don't do",
        "that's not right",
        "you misunderstood",
    ]
    return any(m in lower[:80] for m in interrupt_markers)


def analyze_session(path: Path) -> dict | None:
    """Analyze one JSONL session file, return metrics dict or None if too short."""
    tool_calls: list[tuple[str, str | None]] = []
    assistant_text_blob: list[str] = []
    user_interrupts = 0
    first_read_by_path: dict[str, int] = {}

    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                obj = parse_message(line)
                if not obj:
                    continue
                tu = extract_tool_use(obj)
                if tu:
                    tool_calls.append(tu)
                    name, p = tu
                    if name in READ_TOOLS and p and p not in first_read_by_path:
                        first_read_by_path[p] = len(tool_calls) - 1
                at = extract_assistant_text(obj)
                if at:
                    assistant_text_blob.append(at)
                if is_user_interrupt(obj):
                    user_interrupts += 1
    except OSError:
        return None

    total_calls = len(tool_calls)
    if total_calls < 10:
        return None  # too short for reliable stats

    by_tool = Counter(name for name, _ in tool_calls)
    reads = sum(by_tool[t] for t in READ_TOOLS)
    edits = sum(by_tool[t] for t in EDIT_TOOLS)
    writes = sum(by_tool[t] for t in WRITE_TOOLS)
    research = sum(by_tool[t] for t in RESEARCH_TOOLS)
    mutations = sum(by_tool[t] for t in MUTATION_TOOLS)

    # Edits without prior Read
    edits_without_prior = 0
    for idx, (name, p) in enumerate(tool_calls):
        if name not in EDIT_TOOLS or not p:
            continue
        if p not in first_read_by_path or first_read_by_path[p] >= idx:
            edits_without_prior += 1

    # Loop phrase count
    blob_lower = "\n".join(assistant_text_blob).lower()
    loop_count = sum(blob_lower.count(phrase) for phrase in LOOP_PHRASES)

    # Guard against divide-by-zero
    def safe_div(a: float, b: float) -> float:
        return a / b if b > 0 else 0.0

    return {
        "path": str(path),
        "mtime": path.stat().st_mtime,
        "total_calls": total_calls,
        "reads": reads,
        "edits": edits,
        "writes": writes,
        "research": research,
        "mutations": mutations,
        "interrupts": user_interrupts,
        "read_edit_ratio": round(safe_div(reads, edits), 2),
        "research_mutation_ratio": round(safe_div(research, mutations), 2),
        "edits_without_read_pct": round(safe_div(edits_without_prior, edits) * 100, 1),
        "loop_rate_per_1k": round(safe_div(loop_count, total_calls) * 1000, 1),
        "interrupt_rate_per_1k": round(safe_div(user_interrupts, total_calls) * 1000, 1),
        "write_pct_of_mutations": round(safe_div(writes, mutations) * 100, 1),
    }


def aggregate(sessions: list[dict]) -> dict:
    """Compute medians and flag metrics that cross degraded threshold."""
    if not sessions:
        return {}

    def median(vals: list[float]) -> float:
        vals = sorted(vals)
        n = len(vals)
        if n == 0:
            return 0.0
        if n % 2:
            return vals[n // 2]
        return (vals[n // 2 - 1] + vals[n // 2]) / 2

    metrics = [
        "read_edit_ratio",
        "research_mutation_ratio",
        "edits_without_read_pct",
        "loop_rate_per_1k",
        "interrupt_rate_per_1k",
        "write_pct_of_mutations",
    ]
    summary: dict = {"session_count": len(sessions), "totals": {}}
    for m in metrics:
        vals = [s[m] for s in sessions if s[m] > 0 or "pct" in m or "rate" in m]
        med = round(median(vals), 2) if vals else 0.0
        threshold = THRESHOLDS[m]
        if threshold["higher_better"]:
            degraded = med < threshold["degraded_max"]
            healthy = med >= threshold["healthy_min"]
        else:
            degraded = med > threshold["degraded_min"]
            healthy = med <= threshold["healthy_max"]
        status = "degraded" if degraded else ("healthy" if healthy else "transition")
        summary["totals"][m] = {"median": med, "status": status, "n": len(vals)}
    return summary


def find_sessions(days: int, project: str | None) -> list[Path]:
    if not PROJECTS_DIR.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: list[Path] = []
    roots = [PROJECTS_DIR / project] if project else PROJECTS_DIR.iterdir()
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.glob("*.jsonl"):
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            if mtime >= cutoff:
                out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="lookback window in days (default: 7)")
    ap.add_argument("--project", help="limit to one project directory name")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON output")
    ap.add_argument("--csv", action="store_true", help="CSV per-session output")
    args = ap.parse_args()

    session_paths = find_sessions(args.days, args.project)
    if not session_paths:
        print(f"No sessions found under {PROJECTS_DIR} in the last {args.days} days.", file=sys.stderr)
        return 0

    sessions: list[dict] = []
    for p in session_paths:
        analysis = analyze_session(p)
        if analysis:
            sessions.append(analysis)

    if not sessions:
        print(f"Found {len(session_paths)} files but none had enough tool calls (>=10).", file=sys.stderr)
        return 0

    summary = aggregate(sessions)

    if args.json:
        print(json.dumps({"summary": summary, "sessions": sessions}, indent=2))
        return 0

    if args.csv:
        keys = [
            "path", "total_calls", "reads", "edits",
            "read_edit_ratio", "research_mutation_ratio",
            "edits_without_read_pct", "loop_rate_per_1k",
            "interrupt_rate_per_1k", "write_pct_of_mutations",
        ]
        print(",".join(keys))
        for s in sessions:
            print(",".join(str(s.get(k, "")) for k in keys))
        return 0

    # Human-readable summary
    print(f"Reasoning metrics across {summary['session_count']} sessions "
          f"(last {args.days} days):")
    print()
    labels = {
        "read_edit_ratio": "Read:Edit ratio            (healthy >= 5, degraded < 3)",
        "research_mutation_ratio": "Research:Mutation ratio    (healthy >= 8, degraded < 3)",
        "edits_without_read_pct": "Edits without prior Read % (healthy <= 10, degraded > 30)",
        "loop_rate_per_1k": "Loop phrases per 1K calls  (healthy <= 10, degraded > 20)",
        "interrupt_rate_per_1k": "User interrupts per 1K     (healthy <= 2, degraded > 10)",
        "write_pct_of_mutations": "Write % of mutations       (healthy <= 5, degraded > 10)",
    }
    for key, label in labels.items():
        info = summary["totals"][key]
        flag = {"healthy": "OK", "degraded": "DEGRADED", "transition": "watch"}[info["status"]]
        print(f"  {label:55}  median={info['median']:<8} [{flag}]")

    print()
    degraded = [k for k, v in summary["totals"].items() if v["status"] == "degraded"]
    if degraded:
        print(f"DEGRADED metrics: {', '.join(degraded)}")
        print("See alternatives/reasoning-regression-debugging.md for response playbook.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
