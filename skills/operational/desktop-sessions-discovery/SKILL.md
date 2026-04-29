---
name: desktop-sessions-discovery
description: Discover, search, and selectively restore Claude desktop app sessions hidden across multiple accountIds. Use when user mentions "missing sessions after account switch", "lost desktop sessions", "where do my old sessions live", or runs multiple Claude accounts on the same machine.
---

# Claude Desktop Sessions Discovery Toolkit

Claude desktop app (Mac/Windows native) stores sessions per `<accountId>/<orgId>/`. When you switch accounts, old sessions become invisible in UI — they remain on disk but `LocalSessionManager.loadSessions()` only reads the active accountId folder.

This is GitHub issue [#48511](https://github.com/anthropics/claude-code/issues/48511), open since April 2026 with no Anthropic fix. Issue [#26452](https://github.com/anthropics/claude-code/issues/26452) has 40 comments documenting the same loss.

This skill is a community workaround. Use at your own risk — see Caveats.

## Storage paths (reverse-engineered, NOT in official Anthropic docs)

| Install type | Path |
|---|---|
| **Win32 .exe install** (recommended) | `%APPDATA%\Claude\claude-code-sessions\<acct>\<org>\local_<sid>.json` |
| **Windows MSIX (Microsoft Store)** | `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code-sessions\<acct>\<org>\` — see issue [#48362](https://github.com/anthropics/claude-code/issues/48362) (atomic-rename bug breaks this entirely) |
| **macOS** | `~/Library/Application Support/Claude/claude-code-sessions/<acct>/<org>/local_<sid>.json` |
| Legacy (pre-Feb 2026) | same path, but folder name was `local-agent-mode-sessions/` |

Source: bundled JS `.vite/build/index.js` line 771: `const $6t="claude-code-sessions"`. May change in any release.

## Schema of `local_*.json`

```json
{
  "sessionId": "uuid",
  "cliSessionId": "uuid",
  "cwd": "C:\\path\\to\\project",
  "originCwd": "...",
  "createdAt": <unix ms timestamp OR ISO string>,
  "lastActivityAt": <unix ms timestamp OR ISO string>,
  "model": "claude-opus-4-7-...",
  "effort": "default",
  "isArchived": false,
  "title": "Human-readable title shown in UI",
  "permissionMode": "default",
  "remoteMcpServersConfig": [],
  "completedTurns": 12
}
```

NB: timestamp format is inconsistent — some sessions use Unix ms (int), others ISO string. Parser must handle both.

## Three operations

### 1. Inventory — full picture

Script: `scripts/sessions_inventory.py`

Scans all `<accountId>/<orgId>/local_*.json`, prints grouped table with title/cwd/size/lastActivityAt sorted by recency. Includes cross-account view (which projects appear in multiple accountIds — useful when same user worked on the same project under different accounts).

### 2. Find — search by title/cwd substring

Script: `scripts/sessions_find.py`

```bash
python sessions_find.py "<query>"                  # substring in title or cwd
python sessions_find.py "<query>" --account <prefix>  # filter by accountId
python sessions_find.py --since 2026-04-01         # date filter
python sessions_find.py --untitled                  # parse-failed or empty
```

Output is top-N matches sorted by recency, with copy-pasteable restore command.

### 3. Restore — selective single-session migration

Script: `scripts/sessions_restore.py`

```bash
python sessions_restore.py <sid8>             # auto-detect active accountId
python sessions_restore.py <sid8> --to <acct> # explicit target
python sessions_restore.py <sid8> --dry-run   # plan only
```

Behaviour:
1. Find source session by sessionId substring (8 chars usually unique)
2. Detect active accountId by latest mtime (heuristic)
3. Copy `local_<sid>.json` into `<targetAcct>/<sameOrgId>/`
4. **Verify** byte-for-byte match before declaring success (proof loop)
5. Append to `~/.claude/desktop-migrations.jsonl` audit log
6. Source kept as backup, never deleted

After restore: **restart Claude desktop app** to see session in UI.

## Caveats and risks

### v2.1.9+ regression (issue [#18645](https://github.com/anthropics/claude-code/issues/18645))
Anthropic added validation that blocks sessions "not originally created on the current machine". Cross-account migration on the SAME machine appears to work as of April 2026, but cross-machine copies are broken. Anthropic likely tightens validation further in upcoming releases.

### VM bundle architecture coming (issue [#54428](https://github.com/anthropics/claude-code/issues/54428))
Next desktop architecture moves storage to `vm_bundles/claudevm.bundle/sessiondata.img` (disk-image format). When released, file-copy migration of `local_*.json` may stop working entirely. This toolkit has finite shelf life.

### MSIX install fatal bug (issue [#48362](https://github.com/anthropics/claude-code/issues/48362))
If you installed Claude desktop from Microsoft Store, `fs.rename('.tmp', '.json')` fails with EXDEV inside MSIX sandbox — sessions never persist at all. Switch to Win32 .exe install.

### Mass merge wrecks UI usability
With 700+ sessions in one accountId, the app's session list becomes unreadable. Prefer selective restore one-at-a-time when you actually need a specific thread.

## Recommended long-term

Drift serious work into Claude Code CLI. CLI sessions live in `~/.claude/projects/<slug>/<UUID>.jsonl`, are account-agnostic, stable storage, open JSONL format, survive desktop app reorgs. Use desktop app for quick UI but not for long-running projects.

## Files

- `scripts/sessions_inventory.py` — full table
- `scripts/sessions_find.py` — search
- `scripts/sessions_restore.py` — selective copy with verify and audit log

## License

Public domain. This is a community workaround for an Anthropic bug; share freely.

## See also

- claude-sync (CLI only): https://github.com/tawanorg/claude-sync
- claude-session-restore (CLI only): https://github.com/ZENG3LD/claude-session-restore
- CLI multi-account guide: https://medium.com/@buwanekasumanasekara/setting-up-multiple-claude-code-accounts-on-your-local-machine-f8769a36d1b1
