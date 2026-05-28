#!/usr/bin/env python3
"""SessionStart hook: verify CLI prerequisites of enabled plugins exist in PATH.

Silent failure pattern: a Claude Code plugin can be enabled in
`settings.json` while its hooks shell out to an external CLI
(semgrep, gh, stripe, language servers, etc.). If that CLI is
missing, the hook exits with a non-zero status — Claude Code
typically logs it and continues, so the user gets no warning
that a protection layer is effectively a no-op.

This script reads `~/.claude/settings.json`, looks at `enabledPlugins`,
and for each plugin with a known CLI requirement checks whether the
CLI is in PATH. Missing → printed to stdout (which SessionStart hooks
display).

Wire it via `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/scripts/verify_plugin_prerequisites.py",
        "statusMessage": "Verifying plugin CLI prerequisites..."
      }]
    }]
  }
}
```

To extend the map: open the target plugin's `hooks/hooks.json` and
`.mcp.json` under `~/.claude/plugins/cache/<plugin>/<version>/`. If
any `command` field invokes an external binary (not a bundled
`python3 ${CLAUDE_PLUGIN_ROOT}/...` script), add the binary to
`PLUGIN_CLI_REQUIREMENTS`.

Related rule: `rules/silent-failure-detection.md`.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Plugin → list of required CLI executables. Conservative: only plugins
# whose own hooks.json or .mcp.json invoke a documented external CLI.
PLUGIN_CLI_REQUIREMENTS: dict[str, list[str]] = {
    # `semgrep mcp -k ...` in hooks.json + MCP server entry in .mcp.json
    "semgrep@claude-plugins-official": ["semgrep"],
    # github plugin uses gh for the underlying commands
    "github@claude-plugins-official": ["gh"],
    # stripe plugin uses the stripe CLI
    "stripe@claude-plugins-official": ["stripe"],
    # LSP plugins shell out to language servers
    "pyright-lsp@claude-plugins-official": ["pyright-langserver"],
    "clangd-lsp@claude-plugins-official": ["clangd"],
    "gopls-lsp@claude-plugins-official": ["gopls"],
    "php-lsp@claude-plugins-official": ["php"],
}

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def load_enabled_plugins() -> set[str]:
    if not SETTINGS_PATH.exists():
        return set()
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {pid for pid, enabled in data.get("enabledPlugins", {}).items() if enabled}


def check_cli_available(cli: str) -> bool:
    # shutil.which respects PATHEXT on Windows (.exe / .bat / .cmd)
    return shutil.which(cli) is not None


def main() -> int:
    enabled = load_enabled_plugins()
    findings: list[tuple[str, str]] = []  # (plugin, missing_cli)

    for plugin_id, required_clis in PLUGIN_CLI_REQUIREMENTS.items():
        if plugin_id not in enabled:
            continue
        for cli in required_clis:
            if not check_cli_available(cli):
                findings.append((plugin_id, cli))

    if findings:
        print("=" * 60)
        print("PLUGIN PREREQUISITE WARNING - silent-failure risk")
        print("=" * 60)
        print("The following plugins are enabled but their required CLI")
        print("is NOT in PATH. Their hooks will fail silently on every")
        print("invocation, leaving you with no protection from them.")
        print()
        for plugin, cli in findings:
            print(f"  X  {plugin}")
            print(f"     missing CLI: `{cli}`")
        print()
        print("Fix: install the missing CLI(s) or disable the plugin")
        print("     in ~/.claude/settings.json enabledPlugins block.")
        print("See rules/silent-failure-detection.md for context.")
        print("=" * 60)

    # Always exit 0 - this is informational, not blocking.
    return 0


if __name__ == "__main__":
    sys.exit(main())
