"""
Context fill vs quality degradation analyzer.

Tests the claim: "40%+ context fill => degradation"

Approach: parse Claude Code session logs, track per-turn:
  - Context fill level (total input tokens / context window)
  - Quality proxies: output length, tool use vs end_turn ratio, tool failures
  - Compaction events (context drops significantly)

Groups turns by fill-level buckets (0-20%, 20-40%, 40-60%, 60-80%, 80%+)
and compares quality metrics across buckets.

Run:
    python scripts/context_degradation.py
    python scripts/context_degradation.py --project CODE-Claude --days 14
    python scripts/context_degradation.py --context-window 200000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev


# Context window sizes by model family
CONTEXT_WINDOWS = {
    "claude-sonnet-4": 200_000,
    "claude-opus-4": 200_000,
    "claude-3-5-sonnet": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-5-haiku": 200_000,
    # Extended thinking / 1M models
    "claude-sonnet-4-1m": 1_000_000,
    "claude-opus-4-1m": 1_000_000,
}

BUCKETS = [
    (0.0, 0.2, "0-20%"),
    (0.2, 0.4, "20-40%"),
    (0.4, 0.6, "40-60%"),
    (0.6, 0.8, "60-80%"),
    (0.8, 1.0, "80-100%"),
]


def guess_context_window(model: str) -> int:
    """Guess context window from model name."""
    if not model:
        return 200_000
    model_lower = model.lower()
    if "1m" in model_lower or "1000k" in model_lower:
        return 1_000_000
    for prefix, size in CONTEXT_WINDOWS.items():
        if prefix in model_lower:
            return size
    return 200_000


def parse_session_turns(path: Path, context_window_override: int | None = None) -> list[dict]:
    """Parse a session into per-turn records with fill level."""
    turns = []
    prev_total = 0

    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if rec.get("type") == "assistant":
                    msg = rec.get("message") or {}
                    usage = msg.get("usage") or {}
                    if not usage:
                        continue

                    inp = usage.get("input_tokens", 0) or 0
                    cc = usage.get("cache_creation_input_tokens", 0) or 0
                    cr = usage.get("cache_read_input_tokens", 0) or 0
                    out = usage.get("output_tokens", 0) or 0
                    total_in = inp + cc + cr

                    model = msg.get("model", "")
                    ctx_win = context_window_override or guess_context_window(model)

                    # Detect compaction: context dropped significantly
                    compacted = total_in < prev_total * 0.7 and prev_total > 10_000

                    fill = total_in / ctx_win if ctx_win > 0 else 0
                    stop = msg.get("stop_reason", "")

                    turns.append({
                        "total_input": total_in,
                        "output": out,
                        "fill": fill,
                        "fill_pct": fill * 100,
                        "stop_reason": stop,
                        "compacted": compacted,
                        "model": model,
                        "ctx_window": ctx_win,
                    })

                    prev_total = total_in

    except OSError:
        return []

    return turns


def bucket_for(fill: float) -> str:
    for lo, hi, label in BUCKETS:
        if lo <= fill < hi:
            return label
    return "80-100%"  # overflow


def analyze_sessions(session_files: list[Path], ctx_override: int | None) -> dict:
    """Analyze all sessions, return bucket-level stats."""
    bucket_data = defaultdict(lambda: {
        "outputs": [],
        "tool_use_count": 0,
        "end_turn_count": 0,
        "total_turns": 0,
        "compaction_count": 0,
    })

    session_summaries = []
    total_turns = 0
    total_compactions = 0

    for path in session_files:
        turns = parse_session_turns(path, ctx_override)
        if len(turns) < 5:
            continue

        session_max_fill = 0
        session_compactions = 0

        for t in turns:
            b = bucket_for(t["fill"])
            bd = bucket_data[b]
            bd["total_turns"] += 1
            bd["outputs"].append(t["output"])
            if t["stop_reason"] == "tool_use":
                bd["tool_use_count"] += 1
            elif t["stop_reason"] == "end_turn":
                bd["end_turn_count"] += 1
            if t["compacted"]:
                bd["compaction_count"] += 1
                session_compactions += 1
            session_max_fill = max(session_max_fill, t["fill"])

        total_turns += len(turns)
        total_compactions += session_compactions

        session_summaries.append({
            "id": path.stem[:8],
            "turns": len(turns),
            "max_fill": session_max_fill,
            "compactions": session_compactions,
            "ctx_window": turns[0]["ctx_window"] if turns else 0,
        })

    return {
        "buckets": dict(bucket_data),
        "sessions": session_summaries,
        "total_turns": total_turns,
        "total_compactions": total_compactions,
    }


def print_report(data: dict) -> None:
    buckets = data["buckets"]
    sessions = data["sessions"]

    print()
    print("=" * 78)
    print("CONTEXT FILL vs QUALITY DEGRADATION ANALYSIS")
    print("=" * 78)
    print(f"Sessions analyzed: {len(sessions)}")
    print(f"Total turns:       {data['total_turns']:,}")
    print(f"Compaction events: {data['total_compactions']}")
    print()

    # Main table
    print("-" * 78)
    print(f"{'Fill Level':<12} {'Turns':>8} {'Avg Output':>11} {'Med Output':>11} "
          f"{'Tool Use%':>10} {'End Turn%':>10} {'Compact':>8}")
    print("-" * 78)

    for _, _, label in BUCKETS:
        bd = buckets.get(label)
        if not bd or bd["total_turns"] == 0:
            print(f"{label:<12} {'---':>8}")
            continue

        n = bd["total_turns"]
        outputs = bd["outputs"]
        avg_out = mean(outputs) if outputs else 0
        med_out = median(outputs) if outputs else 0
        active = bd["tool_use_count"] + bd["end_turn_count"]
        tool_pct = bd["tool_use_count"] / active * 100 if active else 0
        end_pct = bd["end_turn_count"] / active * 100 if active else 0

        print(f"{label:<12} {n:>8,} {avg_out:>11.0f} {med_out:>11.0f} "
              f"{tool_pct:>9.1f}% {end_pct:>9.1f}% {bd['compaction_count']:>8}")

    print("-" * 78)
    print()

    # Interpretation
    print("INTERPRETATION GUIDE:")
    print("  - Avg/Med Output: lower = model writing shorter responses (possible rushing)")
    print("  - Tool Use%: higher = model actively using tools (healthy)")
    print("  - End Turn%: higher = model stopping without tool use (possible giving up)")
    print("  - Compact: context compaction events (context was reset)")
    print()
    print("  The '40% degradation' claim would show as:")
    print("    - Output length dropping in 40-60%+ buckets")
    print("    - End Turn% increasing (model stops working, starts talking)")
    print("    - Tool Use% decreasing (less active problem-solving)")
    print()

    # Sessions that hit high fill
    high_fill = [s for s in sessions if s["max_fill"] > 0.4]
    if high_fill:
        high_fill.sort(key=lambda s: s["max_fill"], reverse=True)
        print("-" * 78)
        print(f"SESSIONS THAT EXCEEDED 40% FILL ({len(high_fill)} of {len(sessions)})")
        print("-" * 78)
        print(f"{'Session':<12} {'Turns':>7} {'Max Fill':>10} {'Window':>10} {'Compactions':>12}")
        for s in high_fill[:15]:
            win_label = "1M" if s["ctx_window"] >= 500_000 else "200K"
            print(f"{s['id']:<12} {s['turns']:>7} {s['max_fill']*100:>9.1f}% {win_label:>10} {s['compactions']:>12}")
        print()

    # Verdict
    b_low = buckets.get("0-20%", {})
    b_mid = buckets.get("40-60%", {})
    b_high = buckets.get("60-80%", {})

    if b_low.get("total_turns", 0) > 10 and b_mid.get("total_turns", 0) > 10:
        avg_low = mean(b_low["outputs"]) if b_low["outputs"] else 0
        avg_mid = mean(b_mid["outputs"]) if b_mid["outputs"] else 0
        change = (avg_mid - avg_low) / avg_low * 100 if avg_low > 0 else 0
        print("-" * 78)
        print("VERDICT:")
        print(f"  Output length 0-20% vs 40-60%: {change:+.1f}%")
        if abs(change) < 15:
            print("  -> No significant degradation detected at 40% fill level")
        elif change < -15:
            print("  -> OUTPUT LENGTH DROPS at 40%+ fill - supports degradation claim")
        else:
            print("  -> Output length INCREASES at higher fill (longer sessions = more complex tasks)")
        print()
    else:
        print("Not enough data in both low and mid buckets for comparison.")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze context fill level vs quality degradation"
    )
    parser.add_argument("--days", type=int, default=14,
                        help="Sessions from last N days (default 14)")
    parser.add_argument("--project", type=str, default=None,
                        help="Filter by project directory substring")
    parser.add_argument("--context-window", type=int, default=None,
                        help="Override context window size (e.g., 200000 or 1000000)")
    parser.add_argument("--all", action="store_true",
                        help="Analyze all sessions regardless of age")
    args = parser.parse_args()

    projects_root = Path.home() / ".claude" / "projects"
    if not projects_root.exists():
        print(f"No projects directory at {projects_root}")
        return 1

    cutoff = time.time() - (args.days * 86400)

    session_files: list[Path] = []
    for proj_dir in projects_root.iterdir():
        if not proj_dir.is_dir():
            continue
        if args.project and args.project not in proj_dir.name:
            continue
        session_files.extend(proj_dir.glob("*.jsonl"))

    if not args.all:
        session_files = [p for p in session_files if p.stat().st_mtime >= cutoff]

    if not session_files:
        print(f"No session files found (days={args.days}, project={args.project})")
        return 1

    print(f"Parsing {len(session_files)} session files...")
    data = analyze_sessions(session_files, args.context_window)
    print_report(data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
