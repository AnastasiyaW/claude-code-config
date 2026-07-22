# Temporary Workspace Cleanup

Use a dedicated non-system drive for agent scratch storage. Keep the old path as
a junction when compatibility matters, so existing tools do not need a blind
path migration.

`cleanup_temp_workspace.py` is intentionally conservative:

- default mode is a report-only dry run;
- only explicit policy patterns can become candidates;
- a candidate needs an allowed lifecycle label, `safe_to_delete: true`, a
  rebuild/source-of-truth description, and an expired TTL;
- unknown entries and entries with `.active`, `.in-use`, `.lock`, `RUNNING`, or
  `running.pid` are kept;
- `--apply` deletes only candidates and verifies each path is gone.

Example:

```powershell
python scripts/cleanup_temp_workspace.py `
  --root <D-drive>\agent-temp\legacy-c-tmp `
  --policy <D-drive>\agent-temp\cleanup-policy.json `
  --json
```

The archive is not a source of truth. Code, manifests, and research remain in
Git; temporary outputs are disposable only when their policy says how to
rebuild them. Windows Storage Sense may handle the OS `%TEMP%` tree separately;
this script is for the explicitly managed agent scratch tree.
