#!/usr/bin/env python3
"""PreToolUse: require a closure audit before writing handoff files.

Handoffs are the legitimate exception to "finish the task now". That exception
is easy to abuse: an agent can write a handoff while silently leaving related
work half-open. This hook blocks handoff writes unless the handoff contains an
explicit Closure Audit section.

Watched files:
- .claude/HANDOFF.md
- .claude/handoffs/<project-slug>/*.md
- ~/.claude/handoffs/<project-slug>/*.md

INDEX.md and archive folders are ignored.

Bypass:
- CLAUDE_ALLOW_INCOMPLETE_HANDOFF=1
- <!-- claude-bypass: incomplete-handoff -->
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import allow, block, bypass, log, read_event  # noqa: E402


REQUIRED_LABELS = {
    "Primary request status": re.compile(r"^\s*[-*]?\s*\**Primary request status\**\s*:", re.I | re.M),
    "Acceptance/checklist verified": re.compile(r"^\s*[-*]?\s*\**Acceptance/checklist verified\**\s*:", re.I | re.M),
    "Related/scope-adjacent tasks checked": re.compile(r"^\s*[-*]?\s*\**Related/scope-adjacent tasks checked\**\s*:", re.I | re.M),
    "Unfinished related tasks": re.compile(r"^\s*[-*]?\s*\**Unfinished related tasks\**\s*:", re.I | re.M),
    "Why not continuing now": re.compile(r"^\s*[-*]?\s*\**Why not continuing now\**\s*:", re.I | re.M),
}

HEADING_RE = re.compile(r"^##\s+(Closure Audit|Аудит закрытия)\s*$", re.I | re.M)
NEXT_HEADING_RE = re.compile(r"^##\s+", re.M)
PRIMARY_STATUS_RE = re.compile(
    r"^\s*[-*]?\s*\**Primary request status\**\s*:\s*"
    r"(COMPLETE|BLOCKED-[A-Z0-9_-]+|HANDOFF-NEAR-CONTEXT-LIMIT|USER-REDIRECTED)\b",
    re.I | re.M,
)
UNFINISHED_RE = re.compile(
    r"^\s*[-*]?\s*\**Unfinished related tasks\**\s*:\s*(?P<value>.+)$",
    re.I | re.M,
)
TRACKER_RE = re.compile(
    r"\b(PROBLEMS\.md|feature_list\.json|issue\s*#?\d+|ticket\s*#?\d+|"
    r"backlog|task[-_ ]?inbox|DECISIONS\.md|BLOCKED-[A-Z0-9_-]+)\b",
    re.I,
)
BAD_EVASION_RE = re.compile(
    r"\b(todo later|later maybe|next session maybe|not checked|unknown|tbd|"
    r"unclear|probably done|seems done|should be fine)\b",
    re.I,
)


def _tool_path(tool_input: dict) -> str:
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if value:
            return str(value)
    return ""


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def is_handoff_path(path: str) -> bool:
    p = _norm(path).lower()
    if not p.endswith(".md"):
        return False
    if p.endswith("/index.md") or "/archive/" in p or "/handoff-history/" in p:
        return False
    if p.endswith("/.claude/handoff.md") or p.endswith(".claude/handoff.md"):
        return True
    return "/.claude/handoffs/" in p


def apply_edit(original: str, tool_name: str, tool_input: dict) -> str | None:
    """Best-effort reconstruction of post-edit content for Edit/MultiEdit."""
    if tool_name == "Write":
        return str(tool_input.get("content", ""))

    content = original
    edits = []
    if tool_name == "Edit":
        edits = [{
            "old_string": str(tool_input.get("old_string", "")),
            "new_string": str(tool_input.get("new_string", "")),
            "replace_all": bool(tool_input.get("replace_all", False)),
        }]
    elif tool_name == "MultiEdit":
        raw_edits = tool_input.get("edits", [])
        if isinstance(raw_edits, list):
            edits = raw_edits
    else:
        return None

    for edit in edits:
        old = str(edit.get("old_string", ""))
        new = str(edit.get("new_string", ""))
        if old == "":
            return None
        if edit.get("replace_all"):
            if old not in content:
                return None
            content = content.replace(old, new)
        else:
            if old not in content:
                return None
            content = content.replace(old, new, 1)
    return content


def closure_section(content: str) -> str | None:
    match = HEADING_RE.search(content)
    if not match:
        return None
    start = match.start()
    next_match = NEXT_HEADING_RE.search(content, match.end())
    end = next_match.start() if next_match else len(content)
    return content[start:end]


def validate_closure_audit(content: str) -> list[str]:
    errors: list[str] = []
    section = closure_section(content)
    if section is None:
        return [
            "missing required `## Closure Audit` section",
            "add the mandatory fields from rules/session-handoff.md before writing the handoff",
        ]

    for label, pattern in REQUIRED_LABELS.items():
        if not pattern.search(section):
            errors.append(f"missing Closure Audit field: {label}:")

    if not PRIMARY_STATUS_RE.search(section):
        errors.append(
            "Primary request status must be COMPLETE, BLOCKED-<reason>, "
            "HANDOFF-NEAR-CONTEXT-LIMIT, or USER-REDIRECTED"
        )

    unfinished = UNFINISHED_RE.search(section)
    if unfinished:
        value = unfinished.group("value").strip()
        if not re.search(r"\b(NONE|нет|no unfinished|nothing open)\b", value, re.I):
            if not TRACKER_RE.search(value):
                errors.append(
                    "Unfinished related tasks is not NONE and does not cite a durable tracker "
                    "(PROBLEMS.md, feature_list.json, issue/ticket, backlog, task-inbox, or BLOCKED-*)"
                )

    bad = BAD_EVASION_RE.search(section)
    if bad:
        errors.append(f"Closure Audit contains evasive/uncertain wording: {bad.group(0)!r}")

    return errors


def main() -> None:
    event = read_event()
    tool_name = str(event.get("tool_name", ""))
    if tool_name not in {"Write", "Edit", "MultiEdit"}:
        allow()

    tool_input = event.get("tool_input", {}) or {}
    path = _tool_path(tool_input)
    if not path or not is_handoff_path(path):
        allow()

    target = Path(path)
    original = ""
    if tool_name in {"Edit", "MultiEdit"}:
        try:
            original = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            log("BLOCK", "handoff_closure_audit", "cannot_read", "handoff", path)
            block(
                f"Cannot validate handoff edit because the existing file is unreadable: {path}.\n"
                "Use Write with the full handoff content, including `## Closure Audit`."
            )

    content = apply_edit(original, tool_name, tool_input)
    if content is None:
        log("BLOCK", "handoff_closure_audit", "cannot_reconstruct", "handoff", path)
        block(
            f"Cannot validate resulting handoff content for {tool_name} on {path}.\n"
            "Use one atomic Write with the full handoff content, including `## Closure Audit`."
        )

    if bypass("incomplete-handoff", content, env_name="CLAUDE_ALLOW_INCOMPLETE_HANDOFF"):
        log("WARN", "handoff_closure_audit", "bypass", "handoff", path)
        allow()

    errors = validate_closure_audit(content)
    if not errors:
        allow()

    log("BLOCK", "handoff_closure_audit", "missing_closure_audit", "handoff", path)
    reason = (
        f"Handoff write blocked for {path}.\n\n"
        "A handoff is allowed only after a closure audit proves the current task and "
        "scope-adjacent tasks were handled honestly.\n\n"
        "Problems:\n"
        + "\n".join(f"  - {err}" for err in errors)
        + "\n\nRequired section:\n"
        "## Closure Audit\n"
        "- Primary request status: COMPLETE | BLOCKED-<external-reason> | "
        "HANDOFF-NEAR-CONTEXT-LIMIT | USER-REDIRECTED\n"
        "- Acceptance/checklist verified: <tests/checks/evidence, or explicit blocker>\n"
        "- Related/scope-adjacent tasks checked: <what adjacent work was checked>\n"
        "- Unfinished related tasks: NONE | <durable tracker + reason>\n"
        "- Why not continuing now: NONE | <external blocker/context limit/user redirect>\n"
    )
    block(reason)


if __name__ == "__main__":
    main()
