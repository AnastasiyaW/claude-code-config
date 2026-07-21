# NotebookLM MCP Workflow

## Selected implementation

The selected bridge is [PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp), pinned to `2.0.0`.
It runs a visible Chrome profile and communicates over stdio by default. The
recommended profile is `minimal`:

- `get_health`
- `list_notebooks`
- `select_notebook`
- `get_notebook`
- `ask_question`

Responses can request `none`, `inline`, `footnotes`, or `json` citations. The
bridge also attaches provenance metadata, but provenance is not independent
verification.

## Codex configuration

```text
codex mcp add notebooklm --env NOTEBOOKLM_PROFILE=minimal --env NOTEBOOKLM_AI_MARKER=true -- npx.cmd --yes notebooklm-mcp@2.0.0
```

The `.cmd` suffix is important on this Windows host because PowerShell execution
policy blocks the `npm.ps1` and `npx.ps1` shims.

## First run

```text
get_health
setup_auth(show_browser=true)       # only after the user agrees and logs in
get_health
list_notebooks
select_notebook(notebook_id=...)
ask_question(question=..., source_format=footnotes)
```

`setup_auth` is interactive and must not be run as a hidden background task.
On this host the observed v2.0.0 layout is `%LOCALAPPDATA%/notebooklm-mcp/Data`
for the persistent Chrome profile and library, and
`%APPDATA%/notebooklm-mcp/Config` for settings. The verifier reads only path
metadata; it never reads cookies, tokens, or browser databases.

## Account separation

Use separate aliases/profiles when the user has more than one Google account.
Cookie isolation is provided by separate Chrome profiles, not encryption. Keep
the account alias in a research note only when it is useful for reproducibility;
never record cookies or tokens.

## Why not the broad CLI

`jacob-bd/notebooklm-mcp-cli` offers a convenient Codex skill installer, but its
documented MCP surface is broad. The chosen minimal profile is better for this
harness because the server is present only when a large stable corpus needs
grounded retrieval. More tools are not automatically more capability when the
agent is managing a tight context budget.

## Verification boundary

Configuration verification proves only that Codex can discover the pinned server
and that local runtime prerequisites exist. It does not prove Google login,
NotebookLM availability, source freshness, or answer correctness. A live
`get_health` call and a cited question are separate acceptance criteria.

## Useful references

- [NotebookLM MCP repository](https://github.com/PleasePrompto/notebooklm-mcp)
- [NotebookLM MCP configuration](https://raw.githubusercontent.com/PleasePrompto/notebooklm-mcp/main/docs/configuration.md)
- [Google NotebookLM Help](https://support.google.com/notebooklm/answer/16164461?hl=en)
