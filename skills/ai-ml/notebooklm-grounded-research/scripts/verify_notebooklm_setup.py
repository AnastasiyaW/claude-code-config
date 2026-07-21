#!/usr/bin/env python3
"""Read-only verifier for the pinned NotebookLM MCP setup."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


PINNED_VERSION = "notebooklm-mcp@2.0.0"


def _command_available(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _codex_config_path() -> Path:
    home = os.environ.get("CODEX_HOME")
    if home:
        return Path(home) / "config.toml"
    return Path.home() / ".codex" / "config.toml"


def _read_server(config_path: Path) -> tuple[dict, str | None]:
    if not config_path.is_file():
        return {}, f"Codex config is missing: {config_path}"
    try:
        import tomllib

        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return {}, f"Cannot read Codex config: {exc}"
    server = (data.get("mcp_servers") or {}).get("notebooklm")
    if not isinstance(server, dict):
        return {}, "mcp_servers.notebooklm is not configured"
    return server, None


def verify() -> dict:
    config_path = _codex_config_path()
    server, config_error = _read_server(config_path)
    command = str(server.get("command", ""))
    args = [str(value) for value in server.get("args", [])]
    env = {str(key): str(value) for key, value in (server.get("env") or {}).items()}
    command_ok = command.lower() in {"npx", "npx.cmd"}
    version_ok = PINNED_VERSION in args
    profile_ok = env.get("NOTEBOOKLM_PROFILE") == "minimal"
    marker_ok = env.get("NOTEBOOKLM_AI_MARKER", "").lower() == "true"
    node = _command_available("node", "node.exe")
    npx = _command_available("npx.cmd", "npx", "npx.exe")

    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    local_appdata = Path(
        os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    )
    config_root = appdata / "notebooklm-mcp" / "Config"
    data_root = local_appdata / "notebooklm-mcp" / "Data"
    browser_profile = data_root / "chrome_profile"
    settings = config_root / "settings.json"
    library = data_root / "library.json"
    auth_state = browser_profile.is_dir() or settings.is_file()
    config_ok = not config_error and command_ok and version_ok and profile_ok and marker_ok
    status = "ready_for_auth" if config_ok and not auth_state else "configured"
    if config_ok and auth_state:
        status = "auth_state_present_needs_live_health_check"
    if not config_ok:
        status = "not_configured"

    return {
        "status": status,
        "config_path": str(config_path),
        "config_error": config_error,
        "server": {
            "command_is_npx": command_ok,
            "pinned_version": version_ok,
            "minimal_profile": profile_ok,
            "ai_marker": marker_ok,
        },
        "runtime": {"node": node, "npx": npx},
        "local_paths": {
            "config_root": str(config_root),
            "data_root": str(data_root),
            "browser_profile_exists": browser_profile.is_dir(),
            "settings_exists": settings.is_file(),
            "library_exists": library.is_file(),
            "secrets_read": False,
        },
        "next_step": (
            "Run a live get_health call; if unauthenticated, ask the user to run visible setup_auth."
            if config_ok
            else "Register the pinned minimal MCP server, then run this verifier again."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    result = verify()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(f"[notebooklm] {result['status']}")
        print(f"[notebooklm] config: {result['config_path']}")
        print(f"[notebooklm] next: {result['next_step']}")
    return 0 if result["status"] != "not_configured" else 2


if __name__ == "__main__":
    sys.exit(main())
