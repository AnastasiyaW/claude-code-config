"""
KV-cache hit rate analyzer for Claude Code sessions.

Parses ~/.claude/projects/*/<session-id>.jsonl files and computes, for each
session and overall:

    cache_read_input_tokens / (cache_read + cache_creation + input)

That ratio is the "cache hit rate" in the sense Manus uses it - how much of
the input on a turn was served from the prompt cache vs. freshly processed.

Also surfaces:
- Per-session totals (cache_read, cache_creation, input, output)
- Dollar estimate using current Claude pricing for Opus 4.6
- Distribution across sessions (worst, median, best hit rates)
- Sessions newer than N days only (default 7)

Run:
    python ~/.claude/scripts/kvcache_stats.py
    python ~/.claude/scripts/kvcache_stats.py --days 30 --project CODE-Claude
    python ~/.claude/scripts/kvcache_stats.py --top 10
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median

# Claude Opus 4.6 pricing (per 1M tokens) as of April 2026
# Source: https://www.anthropic.com/pricing
PRICE_INPUT = 15.00          # uncached input
PRICE_CACHE_WRITE = 18.75    # cache creation (25% premium)
PRICE_CACHE_READ = 1.50      # cache read (90% discount)
PRICE_OUTPUT = 75.00


def parse_session(path: Path) -> dict | None:
    """Aggregate usage across all assistant messages in a session file."""
    totals = {
        "input": 0,
        "cache_create": 0,
        "cache_read": 0,
        "output": 0,
        "turns": 0,
        "models": set(),
        "first_ts": None,
        "last_ts": None,
    }
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message") or {}
                usage = msg.get("usage") or {}
                if not usage:
                    continue
                totals["input"] += usage.get("input_tokens", 0) or 0
                totals["cache_create"] += usage.get("cache_creation_input_tokens", 0) or 0
                totals["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
                totals["output"] += usage.get("output_tokens", 0) or 0
                totals["turns"] += 1
                model = msg.get("model")
                if model:
                    totals["models"].add(model)
                ts = rec.get("timestamp") or msg.get("created_at")
                if ts:
                    if totals["first_ts"] is None or ts < totals["first_ts"]:
                        totals["first_ts"] = ts
                    if totals["last_ts"] is None or ts > totals["last_ts"]:
                        totals["last_ts"] = ts
    except OSError:
        return None

    if totals["turns"] == 0:
        return None

    total_input = totals["input"] + totals["cache_create"] + totals["cache_read"]
    if total_input == 0:
        hit_rate = 0.0
    else:
        hit_rate = totals["cache_read"] / total_input

    cost = (
        totals["input"] / 1_000_000 * PRICE_INPUT
        + totals["cache_create"] / 1_000_000 * PRICE_CACHE_WRITE
        + totals["cache_read"] / 1_000_000 * PRICE_CACHE_READ
        + totals["output"] / 1_000_000 * PRICE_OUTPUT
    )

    # What cost would be without any caching (everything fresh input)
    naive_cost = (
        total_input / 1_000_000 * PRICE_INPUT
        + totals["output"] / 1_000_000 * PRICE_OUTPUT
    )
    savings = naive_cost - cost

    return {
        "session_id": path.stem,
        "turns": totals["turns"],
        "input": totals["input"],
        "cache_create": totals["cache_create"],
        "cache_read": totals["cache_read"],
        "output": totals["output"],
        "hit_rate": hit_rate,
        "cost_usd": cost,
        "naive_cost_usd": naive_cost,
        "savings_usd": savings,
        "models": sorted(totals["models"]),
        "first_ts": totals["first_ts"],
        "last_ts": totals["last_ts"],
        "mtime": path.stat().st_mtime,
    }


def fmt_tokens(n: int) -> str:
    for unit in ("", "K", "M", "B"):
        if abs(n) < 1000:
            return f"{n:.1f}{unit}"
        n /= 1000
    return f"{n:.1f}T"


def pct(f: float) -> str:
    return f"{f * 100:5.1f}%"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Only consider sessions modified within N days (default 7)")
    parser.add_argument("--project", type=str, default=None, help="Substring to match in project directory name")
    parser.add_argument("--top", type=int, default=15, help="Show top N sessions by total tokens")
    parser.add_argument("--all", action="store_true", help="Ignore --days filter")
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
        print(f"No session files found (filter: days={args.days}, project={args.project})")
        return 1

    print(f"Parsing {len(session_files)} session files...")
    stats: list[dict] = []
    for p in session_files:
        s = parse_session(p)
        if s:
            stats.append(s)
    if not stats:
        print("No sessions contained usage records")
        return 1

    # Overall aggregate
    agg_input = sum(s["input"] for s in stats)
    agg_cache_create = sum(s["cache_create"] for s in stats)
    agg_cache_read = sum(s["cache_read"] for s in stats)
    agg_output = sum(s["output"] for s in stats)
    agg_cost = sum(s["cost_usd"] for s in stats)
    agg_naive = sum(s["naive_cost_usd"] for s in stats)
    agg_savings = sum(s["savings_usd"] for s in stats)
    total_input = agg_input + agg_cache_create + agg_cache_read
    overall_hit = agg_cache_read / total_input if total_input else 0

    hit_rates = [s["hit_rate"] for s in stats if (s["input"] + s["cache_create"] + s["cache_read"]) >= 1000]
    hit_rates.sort()

    print()
    print("=" * 72)
    print(f"KV-CACHE ANALYSIS  ({len(stats)} sessions)")
    if args.project:
        print(f"Project filter:   {args.project}")
    print(f"Window:           {'ALL' if args.all else f'last {args.days} days'}")
    print("=" * 72)
    print()
    print(f"Total turns:            {sum(s['turns'] for s in stats):>12,}")
    print(f"Fresh input tokens:     {agg_input:>12,}  {fmt_tokens(agg_input):>10}")
    print(f"Cache creation tokens:  {agg_cache_create:>12,}  {fmt_tokens(agg_cache_create):>10}")
    print(f"Cache read tokens:      {agg_cache_read:>12,}  {fmt_tokens(agg_cache_read):>10}")
    print(f"Output tokens:          {agg_output:>12,}  {fmt_tokens(agg_output):>10}")
    print()
    print(f"OVERALL HIT RATE:       {pct(overall_hit)}")
    print()
    if hit_rates:
        print("Per-session hit rate distribution (excluding tiny sessions <1K tokens):")
        print(f"  min:    {pct(hit_rates[0])}")
        print(f"  p25:    {pct(hit_rates[len(hit_rates) // 4])}")
        print(f"  median: {pct(median(hit_rates))}")
        print(f"  p75:    {pct(hit_rates[3 * len(hit_rates) // 4])}")
        print(f"  max:    {pct(hit_rates[-1])}")
    print()
    print(f"Actual cost:            ${agg_cost:>10.2f}")
    print(f"Cost without caching:   ${agg_naive:>10.2f}")
    print(f"Savings from cache:     ${agg_savings:>10.2f}  ({pct(agg_savings / agg_naive) if agg_naive else '  0.0%'})")
    print()

    # Top sessions by total input tokens
    stats.sort(key=lambda s: s["input"] + s["cache_create"] + s["cache_read"], reverse=True)
    print("-" * 72)
    print(f"TOP {args.top} SESSIONS BY TOTAL TOKENS")
    print("-" * 72)
    print(f"{'id':10}  {'turns':>6}  {'input':>8}  {'create':>8}  {'read':>8}  {'out':>7}  {'hit%':>6}  {'$':>7}")
    for s in stats[: args.top]:
        sid = s["session_id"][:8]
        print(
            f"{sid:10}  {s['turns']:>6}  "
            f"{fmt_tokens(s['input']):>8}  "
            f"{fmt_tokens(s['cache_create']):>8}  "
            f"{fmt_tokens(s['cache_read']):>8}  "
            f"{fmt_tokens(s['output']):>7}  "
            f"{pct(s['hit_rate']):>6}  "
            f"${s['cost_usd']:>6.2f}"
        )
    print()

    # Worst hit rate sessions (only non-trivial ones)
    nontrivial = [s for s in stats if (s["input"] + s["cache_create"] + s["cache_read"]) >= 50_000]
    nontrivial.sort(key=lambda s: s["hit_rate"])
    if nontrivial:
        print("-" * 72)
        print("WORST HIT RATES (sessions >= 50K tokens)")
        print("-" * 72)
        for s in nontrivial[:5]:
            sid = s["session_id"][:8]
            print(f"  {sid}  hit={pct(s['hit_rate'])}  turns={s['turns']:3d}  total={fmt_tokens(s['input'] + s['cache_create'] + s['cache_read'])}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
