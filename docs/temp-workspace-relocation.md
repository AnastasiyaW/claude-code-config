# Temp Workspace Relocation

`relocate_temp_workspace.py` moves an existing scratch tree to another drive
without silently changing callers that still use the old path.

## Safety contract

- Default mode is report-only. `--apply` is required for copying.
- The target drive is checked for source bytes plus a configurable reserve
  (`--reserve-gib`, one GiB by default).
- Copying uses Windows `robocopy` when available (`/E`, `/COPY:DAT`, `/XJ`, one
  retry) and verifies source stability, file count, total bytes, and every file
  size before cutover.
- A live workspace may change during a copy. The script repeats additive sync
  and verification up to `--max-sync-attempts` (three by default), then fails
  closed without removing the source if no stable snapshot is reached.
- Cutover first renames the source to a reversible sibling backup, creates and
  verifies a junction, and restores the backup if link creation fails.
- The old copy is removed only with the explicit `--purge-source` flag after
  verification. Without it, the sibling backup remains for rollback.
- Unknown temporary entries are never inferred to be disposable; use the
  separate policy-driven cleanup script for approved reproducible artifacts.

## Windows example

```powershell
python scripts/relocate_temp_workspace.py `
  --source <system-temp-workspace> `
  --target <data-drive>\agent-temp\legacy-workspace `
  --apply --purge-source --link junction --max-sync-attempts 5 --json
```

For a dry run, omit `--apply`. To preserve a rollback copy, omit
`--purge-source`.
