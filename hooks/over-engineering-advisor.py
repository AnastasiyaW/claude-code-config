#!/usr/bin/env python3
"""PostToolUse(Write|Edit|MultiEdit): advisory nudge on large / dependency-adding code changes.

Makes the quality-code / anti-over-engineering (YAGNI) principle a PERMANENT
MECHANICAL layer, not just an always-on rule that decays under context pressure.

Design (research-backed 2026-06-16):
  * NON-BLOCKING by construction. It emits an advisory only — it NEVER blocks, so
    it cannot cause under-delivery or fight the finish-the-task / completeness canon
    (a legitimately large *complete* feature must never be gated). A hard lint-gate
    was explicitly rejected for this reason.
  * Checks ONLY reliable mechanical signals: a large net addition to a code file,
    or a new dependency in a manifest. Fuzzy "abstraction smells" (factory-for-one,
    interface-with-one-impl, speculative config) are deliberately NOT auto-classified
    here — they need semantic judgment; left to the model + the /ponytail-review skill.
  * Scoped to code files + dependency manifests. Docs/markdown/data are skipped
    (consolidating a big doc is not over-engineering).

Evidence: AI agents measurably over-produce code (GitClear 211M-line study, 2025);
always-on minimalism is non-monotonic so enforcement must advise, not gate
(arXiv 2601.22025). The 80-94% marketing numbers are unverified; the durable,
evaluable win is "smallest solution that FULLY satisfies the task".

Tunables: CLAUDE_BLOAT_EDIT_LINES (default 150), CLAUDE_BLOAT_NEWFILE_LINES (300).
Bypass: CLAUDE_ALLOW_BLOAT=1 or a `# claude-bypass: bloat` marker in the content.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import bypass, log, read_event  # noqa: E402

CODE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".c", ".h",
    ".hpp", ".cpp", ".cc", ".cs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".m", ".mm", ".lua", ".sh", ".ps1", ".vue", ".svelte",
}
DEP_MANIFESTS = {
    "package.json", "requirements.txt", "pyproject.toml", "go.mod", "cargo.toml",
    "gemfile", "build.gradle", "pom.xml", "pubspec.yaml", "composer.json",
}

EDIT_LIMIT = int(os.environ.get("CLAUDE_BLOAT_EDIT_LINES", "150"))
NEWFILE_LIMIT = int(os.environ.get("CLAUDE_BLOAT_NEWFILE_LINES", "300"))


def _allow() -> None:
    sys.exit(0)


def _advise(text: str) -> None:
    # PostToolUse advisory: surface as additional context, do NOT block.
    out = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0)


def _lines(s: str) -> int:
    return str(s).count("\n") + (1 if s else 0)


def main() -> None:
    event = read_event()
    tool = event.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        _allow()

    ti = event.get("tool_input", {}) or {}
    fp = str(ti.get("file_path", ""))
    if not fp:
        _allow()
    name = Path(fp).name.lower()
    ext = Path(fp).suffix.lower()

    blob = str(ti.get("content", "")) + str(ti.get("new_string", ""))
    for e in ti.get("edits", []) or []:
        blob += str(e.get("new_string", ""))
    if bypass("bloat", blob):
        _allow()

    # 1. New dependency in a manifest
    if name in DEP_MANIFESTS:
        added = str(ti.get("content", "")) or str(ti.get("new_string", "")) or blob
        if added.strip():
            log("ADVISE", "over_engineering", "advise", "new_dependency", fp)
            _advise(
                "[minimalism] " + name + " changed — adding a dependency? Per quality-code: "
                "prefer stdlib / a native platform feature / an already-installed dependency "
                "before adding a new one for what a few lines can do. If the dependency is "
                "genuinely the minimal correct choice, proceed."
            )
        _allow()

    if ext not in CODE_EXT:
        _allow()

    # 2. Large addition to a code file
    if tool == "Write":
        net = _lines(ti.get("content", ""))
        threshold, signal = NEWFILE_LIMIT, "large_file"
    elif tool == "MultiEdit":
        net = sum(_lines(e.get("new_string", "")) - _lines(e.get("old_string", ""))
                  for e in (ti.get("edits", []) or []))
        threshold, signal = EDIT_LIMIT, "large_multiedit"
    else:  # Edit
        net = _lines(ti.get("new_string", "")) - _lines(ti.get("old_string", ""))
        threshold, signal = EDIT_LIMIT, "large_addition"

    if net < threshold:
        _allow()

    log("ADVISE", "over_engineering", "advise", signal + f"(~{net}L)", fp)
    _advise(
        "[minimalism] ~" + str(net) + " lines into " + name + ". Per quality-code (YAGNI "
        "ladder): is this the SMALLEST solution that FULLY does the task? Could stdlib / a "
        "native feature / an existing dependency / fewer lines cover it, or is any of it "
        "unrequested abstraction? This targets OVER-building only — never under-deliver or "
        "cut a required branch. If the task genuinely needs this size, proceed."
    )


if __name__ == "__main__":
    main()
