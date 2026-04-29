#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate HTML registry of all Claude desktop app sessions for browse + selective restore.

Reads metadata from <accountId>/<orgId>/local_*.json across all accountIds
and writes a self-contained HTML file with search, filters, sorting, and
copy-to-clipboard restore commands. Auto-opens in default browser.

Cross-platform: macOS, Windows (Win32 install), Linux.

Usage:
    python sessions_registry.py                          # generate + auto-open
    python sessions_registry.py --output /path/file.html  # custom path
    python sessions_registry.py --no-open                 # generate, don't open
"""
from __future__ import annotations
import argparse
import html
import io
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def storage_root() -> Path:
    """Platform-specific Claude desktop sessions root (current path, not legacy)."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude-code-sessions"
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude-code-sessions"
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude-code-sessions"
    return Path.home() / ".config" / "Claude" / "claude-code-sessions"


def legacy_root() -> Path:
    """Pre-Feb 2026 storage path. Some installations still hold legacy sessions here."""
    base = storage_root().parent
    return base / "local-agent-mode-sessions"


ROOT = storage_root()
LEGACY = legacy_root()
AUDIT_LOG = Path.home() / ".claude" / "desktop-migrations.jsonl"
DEFAULT_OUT = Path.home() / ".claude" / "sessions-registry.html"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def fmt_size(n: int) -> str:
    for unit in ("B", "K", "M", "G"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}T"


def fmt_iso(s) -> str:
    if not s:
        return "unknown"
    if isinstance(s, (int, float)):
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


def to_ts(v) -> float:
    if isinstance(v, (int, float)):
        return v / 1000 if v > 1e10 else v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0
    return 0


def humanize_relative(ts: float) -> str:
    if ts == 0:
        return ""
    delta_sec = datetime.now().timestamp() - ts
    if delta_sec < 0:
        return "future"
    if delta_sec < 3600:
        return f"{int(delta_sec/60)}m ago"
    if delta_sec < 86400:
        return f"{int(delta_sec/3600)}h ago"
    if delta_sec < 86400 * 30:
        return f"{int(delta_sec/86400)}d ago"
    if delta_sec < 86400 * 365:
        return f"{int(delta_sec/(86400*30))}mo ago"
    return f"{int(delta_sec/(86400*365))}y ago"


def parse_session(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:
        return {"error": str(e), "size": path.stat().st_size, "path": str(path)}
    return {
        "title": obj.get("title", "(untitled)"),
        "cwd": obj.get("cwd", ""),
        "last": obj.get("lastActivityAt"),
        "created": obj.get("createdAt"),
        "model": obj.get("model", ""),
        "turns": obj.get("completedTurns", 0),
        "archived": obj.get("isArchived", False),
        "session_id": obj.get("sessionId", path.stem.replace("local_", "")),
        "size": path.stat().st_size,
        "path": str(path),
    }


def load_audit_log() -> set[str]:
    """Return set of sessionIds already restored (per audit log)."""
    if not AUDIT_LOG.exists():
        return set()
    restored = set()
    try:
        for line in AUDIT_LOG.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
                sid = entry.get("session_id", "")
                if sid:
                    restored.add(sid)
            except Exception:
                pass
    except Exception:
        pass
    return restored


def collect_sessions(root: Path, source_label: str) -> list[dict]:
    if not root.exists():
        return []
    out = []
    for acct_dir in root.iterdir():
        if not acct_dir.is_dir():
            continue
        # skip skills-plugin and other non-session folders
        if acct_dir.name == "skills-plugin":
            continue
        for json_path in acct_dir.rglob("local_*.json"):
            meta = parse_session(json_path)
            meta["acct"] = acct_dir.name
            meta["org"] = json_path.parent.name
            meta["source"] = source_label
            out.append(meta)
    return out


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Desktop Sessions Registry</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    margin: 0; padding: 20px; background: #0d0e10; color: #e8eaed;
    font-size: 14px; line-height: 1.5;
  }
  h1 { margin: 0 0 10px; font-size: 24px; }
  .stats { color: #9aa0a6; margin-bottom: 20px; font-size: 13px; }
  .controls {
    background: #1a1b1e; padding: 12px; border-radius: 8px; margin-bottom: 16px;
    display: flex; gap: 12px; flex-wrap: wrap; align-items: center; position: sticky; top: 0; z-index: 10;
  }
  input[type="text"], select {
    background: #2a2b2e; color: #e8eaed; border: 1px solid #3a3b3e;
    padding: 8px 12px; border-radius: 6px; font-size: 14px; font-family: inherit;
  }
  input[type="text"] { flex: 1; min-width: 200px; }
  label { color: #9aa0a6; font-size: 13px; }
  .acct-section { margin-bottom: 28px; }
  .acct-header {
    background: #1a1b1e; padding: 10px 14px; border-radius: 8px 8px 0 0;
    display: flex; justify-content: space-between; align-items: center;
    border-left: 4px solid #4285f4;
    cursor: pointer; user-select: none;
  }
  .acct-header.active { border-left-color: #34a853; }
  .acct-header h2 { margin: 0; font-size: 16px; font-weight: 500; }
  .acct-meta { color: #9aa0a6; font-size: 13px; }
  .acct-id { font-family: ui-monospace, "SF Mono", Consolas, monospace; }
  .acct-body { padding: 0; }
  .acct-body.collapsed { display: none; }
  .session-card {
    background: #15161a; padding: 12px 14px; border-bottom: 1px solid #25262a;
    display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center;
  }
  .session-card:hover { background: #1c1d22; }
  .session-card.restored { background: #15201a; }
  .session-card.restored::after {
    content: "RESTORED"; color: #34a853; font-size: 10px; font-weight: 600;
    grid-column: 3; align-self: start;
  }
  .session-title { font-weight: 500; font-size: 15px; color: #e8eaed; }
  .session-meta {
    color: #9aa0a6; font-size: 12px; margin-top: 4px;
    display: flex; gap: 12px; flex-wrap: wrap;
  }
  .badge {
    background: #2a2b2e; padding: 2px 8px; border-radius: 10px;
    font-size: 11px; font-family: ui-monospace, monospace;
  }
  .badge.turns { background: #1a3a5a; }
  .badge.project { background: #2a3a1a; }
  .badge.archived { background: #5a3a1a; }
  .session-id {
    font-family: ui-monospace, monospace; color: #9aa0a6; font-size: 11px;
  }
  .restore-btn {
    background: #4285f4; color: white; border: none; padding: 8px 14px;
    border-radius: 6px; cursor: pointer; font-size: 13px; font-family: inherit;
    white-space: nowrap;
  }
  .restore-btn:hover { background: #5a95f5; }
  .restore-btn.copied { background: #34a853; }
  .untitled { color: #777; font-style: italic; }
  .legacy-tag { background: #5a1a1a; color: #ffaaaa; padding: 1px 6px; border-radius: 8px; font-size: 10px; margin-left: 6px; }
  .footer { margin-top: 30px; padding: 14px; background: #1a1b1e; border-radius: 8px; color: #9aa0a6; font-size: 13px; }
  .footer code { background: #0d0e10; padding: 2px 6px; border-radius: 4px; font-family: ui-monospace, monospace; }
  .empty { padding: 60px; text-align: center; color: #9aa0a6; }
  details summary { cursor: pointer; padding: 6px 0; }
</style>
</head>
<body>
  <h1>Claude Desktop Sessions Registry</h1>
  <div class="stats">__STATS__</div>

  <div class="controls">
    <input type="text" id="search" placeholder="Search by title, project, or session ID..." autofocus>
    <label>Sort: <select id="sort">
      <option value="recent">Most recent</option>
      <option value="turns">Most turns</option>
      <option value="title">Title A-Z</option>
      <option value="size">Size (largest first)</option>
    </select></label>
    <label><input type="checkbox" id="hide-empty"> Hide 0-turn sessions</label>
    <label><input type="checkbox" id="hide-restored"> Hide already restored</label>
  </div>

  <div id="content">__CONTENT__</div>

  <div class="footer">
    <strong>How to restore</strong>: click the blue button on any session — it copies the command to your clipboard.
    Paste in chat with Claude:<br>
    <code>восстанови эту сессию: python ~/.claude/scripts/sessions_restore.py &lt;sid8&gt;</code><br>
    Or run directly in terminal. Source files are NEVER deleted; restore is a copy-only operation with byte-verify.
    Restart Claude desktop app after restore to see sessions appear in UI.
    <br><br>
    <details>
      <summary>Troubleshooting</summary>
      <ul>
        <li><strong>"Session is already in target accountId"</strong> — already in your active account, no restore needed.</li>
        <li><strong>"target already exists"</strong> — restored before; check audit log <code>~/.claude/desktop-migrations.jsonl</code>.</li>
        <li><strong>Restored but not visible after restart</strong> — possibly v2.1.9+ validation rejected (issue #18645). Cross-machine session blocked even on same accountId.</li>
        <li><strong>Anything weird</strong> — source kept as backup. Re-copy or restore in different account is always safe.</li>
      </ul>
    </details>
    <br>
    Generated __TIMESTAMP__ from __ROOT__ (and legacy storage if present).<br>
    See <a href="https://github.com/AnastasiyaW/claude-code-config/tree/main/skills/operational/desktop-sessions-discovery" style="color:#5a95f5">desktop-sessions-discovery skill</a> for details.
  </div>

<script>
  const cards = Array.from(document.querySelectorAll('.session-card'));
  const search = document.getElementById('search');
  const sortSel = document.getElementById('sort');
  const hideEmpty = document.getElementById('hide-empty');
  const hideRestored = document.getElementById('hide-restored');

  function applyFilter() {
    const q = search.value.toLowerCase().trim();
    const he = hideEmpty.checked;
    const hr = hideRestored.checked;
    cards.forEach(c => {
      const text = c.dataset.search || '';
      const turns = parseInt(c.dataset.turns || '0', 10);
      const restored = c.classList.contains('restored');
      const matchQ = !q || text.includes(q);
      const matchEmpty = !he || turns > 0;
      const matchRestored = !hr || !restored;
      c.style.display = (matchQ && matchEmpty && matchRestored) ? '' : 'none';
    });
    document.querySelectorAll('.acct-section').forEach(s => {
      const visible = Array.from(s.querySelectorAll('.session-card')).some(c => c.style.display !== 'none');
      s.style.display = visible ? '' : 'none';
    });
  }

  function applySort() {
    const mode = sortSel.value;
    document.querySelectorAll('.acct-body').forEach(body => {
      const items = Array.from(body.querySelectorAll('.session-card'));
      items.sort((a, b) => {
        if (mode === 'recent') return parseFloat(b.dataset.ts || 0) - parseFloat(a.dataset.ts || 0);
        if (mode === 'turns') return parseInt(b.dataset.turns || 0, 10) - parseInt(a.dataset.turns || 0, 10);
        if (mode === 'size') return parseInt(b.dataset.size || 0, 10) - parseInt(a.dataset.size || 0, 10);
        if (mode === 'title') return (a.dataset.title || '').localeCompare(b.dataset.title || '');
        return 0;
      });
      items.forEach(i => body.appendChild(i));
    });
  }

  search.addEventListener('input', applyFilter);
  sortSel.addEventListener('change', applySort);
  hideEmpty.addEventListener('change', applyFilter);
  hideRestored.addEventListener('change', applyFilter);

  document.querySelectorAll('.acct-header').forEach(h => {
    h.addEventListener('click', () => {
      h.nextElementSibling.classList.toggle('collapsed');
    });
  });

  document.querySelectorAll('.restore-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      const cmd = btn.dataset.cmd;
      navigator.clipboard.writeText(cmd).then(() => {
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1200);
      });
    });
  });

  applySort();
</script>
</body>
</html>"""


def render_session_card(meta: dict, restored_ids: set[str]) -> str:
    sid = meta.get("session_id", "")
    sid8 = sid[:8] if sid else "?"
    is_restored = sid in restored_ids
    title = meta.get("title") or "(untitled)"
    title_html = html.escape(title)
    if title == "(untitled)":
        title_html = f'<span class="untitled">{title_html}</span>'
    if "error" in meta:
        title_html = f'{title_html} <span class="legacy-tag">PARSE ERR</span>'

    cwd = meta.get("cwd") or ""
    cwd_tail = "/".join(cwd.replace("\\", "/").split("/")[-2:]) if cwd else "?"
    turns = meta.get("turns", 0)
    last_iso = fmt_iso(meta.get("last"))
    last_ts = to_ts(meta.get("last"))
    last_rel = humanize_relative(last_ts)
    size = fmt_size(meta.get("size", 0))
    archived = meta.get("archived", False)
    src = meta.get("source", "")
    src_tag = '<span class="legacy-tag">LEGACY</span>' if src == "legacy" else ""

    badges = [
        f'<span class="badge turns">{turns} turns</span>',
        f'<span class="badge project">{html.escape(cwd_tail)}</span>',
        f'<span class="badge">{size}</span>',
    ]
    if archived:
        badges.append('<span class="badge archived">archived</span>')

    search_text = f"{title} {cwd} {sid}".lower()
    classes = ["session-card"]
    if is_restored:
        classes.append("restored")

    restore_cmd = f"python ~/.claude/scripts/sessions_restore.py {sid8}"

    return f"""
    <div class="{' '.join(classes)}"
         data-search="{html.escape(search_text)}"
         data-ts="{last_ts}"
         data-turns="{turns}"
         data-size="{meta.get('size', 0)}"
         data-title="{html.escape(title.lower())}">
      <div>
        <div class="session-title">{title_html} {src_tag}</div>
        <div class="session-meta">
          <span>{last_iso} <span style="color:#777">({last_rel})</span></span>
          {''.join(badges)}
          <span class="session-id">{sid8}…</span>
        </div>
      </div>
      <button class="restore-btn" data-cmd="{html.escape(restore_cmd)}">Restore</button>
    </div>"""


def render_acct_section(acct: str, sessions: list[dict], restored_ids: set[str], is_active: bool) -> str:
    sessions.sort(key=lambda m: to_ts(m.get("last")), reverse=True)
    total_turns = sum(m.get("turns", 0) for m in sessions)
    total_size = sum(m.get("size", 0) for m in sessions)
    latest = max((to_ts(m.get("last")) for m in sessions), default=0)
    latest_str = fmt_iso(latest) if latest else "(never)"
    cards = "\n".join(render_session_card(m, restored_ids) for m in sessions)
    active_marker = ' <span style="color:#34a853">● active</span>' if is_active else ""

    return f"""
    <div class="acct-section">
      <div class="acct-header{' active' if is_active else ''}">
        <h2><span class="acct-id">{acct[:8]}…</span>{active_marker}</h2>
        <div class="acct-meta">
          {len(sessions)} sessions · {fmt_size(total_size)} · {total_turns} turns total · last {latest_str}
        </div>
      </div>
      <div class="acct-body">{cards}</div>
    </div>"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT, help="output HTML path")
    ap.add_argument("--no-open", action="store_true", help="don't auto-open in browser")
    args = ap.parse_args()

    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 1

    sessions = collect_sessions(ROOT, "current") + collect_sessions(LEGACY, "legacy")
    if not sessions:
        print(f"# No sessions found in {ROOT} or {LEGACY}")
        return 0

    restored_ids = load_audit_log()

    # Group by accountId, detect active by latest mtime
    by_acct: dict[str, list[dict]] = {}
    for s in sessions:
        by_acct.setdefault(s["acct"], []).append(s)

    latest_per_acct = {a: max((to_ts(s.get("last")) for s in sl), default=0) for a, sl in by_acct.items()}
    active_acct = max(latest_per_acct, key=latest_per_acct.get) if latest_per_acct else None

    # Sort accounts: active first, then by latest activity desc
    sorted_accts = sorted(by_acct, key=lambda a: (a != active_acct, -latest_per_acct.get(a, 0)))

    sections = "\n".join(
        render_acct_section(a, by_acct[a], restored_ids, a == active_acct) for a in sorted_accts
    )

    total = len(sessions)
    total_size = sum(s.get("size", 0) for s in sessions)
    legacy_count = sum(1 for s in sessions if s.get("source") == "legacy")
    restored_count = sum(1 for s in sessions if s.get("session_id") in restored_ids)
    stats = (
        f"<strong>{total}</strong> sessions across <strong>{len(by_acct)}</strong> accountIds, "
        f"<strong>{fmt_size(total_size)}</strong> total"
    )
    if legacy_count:
        stats += f" · {legacy_count} from legacy storage"
    if restored_count:
        stats += f" · {restored_count} already restored"
    if active_acct:
        stats += f" · active accountId: <span class='acct-id' style='color:#34a853'>{active_acct[:8]}…</span>"

    out_html = (
        HTML_TEMPLATE.replace("__STATS__", stats)
        .replace("__CONTENT__", sections)
        .replace("__TIMESTAMP__", datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("__ROOT__", html.escape(str(ROOT)))
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out_html, encoding="utf-8")
    print(f"# Wrote {args.output}")
    print(f"# {total} sessions across {len(by_acct)} accounts ({fmt_size(total_size)})")

    if not args.no_open:
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(args.output)], check=False)
            elif sys.platform == "win32":
                os.startfile(str(args.output))
            else:
                subprocess.run(["xdg-open", str(args.output)], check=False)
            print(f"# Opened in default browser")
        except Exception as e:
            print(f"# Could not auto-open: {e}", file=sys.stderr)
            print(f"# Open manually: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
