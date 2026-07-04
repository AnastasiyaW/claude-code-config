#!/usr/bin/env python3
"""Validate local ready-for-agent ticket Markdown files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "## Status",
    "## Parent",
    "## What To Build",
    "## Acceptance Criteria",
    "## Verification",
    "## Blocked By",
    "## Notes",
]

CHECKBOX_RE = re.compile(r"(?m)^- \[ \] .+")
READY_RE = re.compile(r"(?im)^## Status\s+ready-for-agent\s*$")
COMMAND_HINT_RE = re.compile(
    r"(?i)(pytest|npm\s+test|pnpm\s+test|bun\s+test|ctest|cmake|cargo\s+test|"
    r"go\s+test|python\s+.+\.py|verify|audit|manual review|artifact|screenshot|"
    r"report|log|diff|hash|snapshot)"
)
HORIZONTAL_HINT_RE = re.compile(
    r"(?i)\b(all|entire)\s+(backend|frontend|ui|api|tests?|docs?|database|schema)\b"
)


def section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    next_match = re.search(r"(?m)^## ", text[start + len(heading):])
    if not next_match:
        return text[start + len(heading):].strip()
    end = start + len(heading) + next_match.start()
    return text[start + len(heading):end].strip()


def validate_ticket(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing heading {heading}")

    status = section(text, "## Status")
    if "ready-for-agent" not in status:
        errors.append("status must contain ready-for-agent")

    ac = section(text, "## Acceptance Criteria")
    if not CHECKBOX_RE.search(ac):
        errors.append("acceptance criteria must contain at least one '- [ ]' item")

    verification = section(text, "## Verification")
    if not COMMAND_HINT_RE.search(verification):
        errors.append("verification must name a command, artifact check, or manual-review gate")

    what = section(text, "## What To Build")
    if HORIZONTAL_HINT_RE.search(what):
        errors.append("ticket looks like a horizontal layer slice; use a vertical tracer bullet")

    if not section(text, "## Blocked By"):
        errors.append("blocked-by section must say None or list dependencies")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickets-dir", required=True)
    parser.add_argument("--json", action="store_true", help="emit JSON result")
    args = parser.parse_args()

    root = Path(args.tickets_dir)
    tickets = sorted(root.glob("TICKET-*.md"))
    problems = {}
    if not tickets:
        problems[str(root)] = ["no TICKET-*.md files found"]
    for ticket in tickets:
        errors = validate_ticket(ticket)
        if errors:
            problems[str(ticket)] = errors

    result = {
        "tickets_dir": str(root),
        "ticket_count": len(tickets),
        "ok": not problems,
        "problems": problems,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif problems:
        print("validate_agent_tickets: FAIL")
        for path, errors in problems.items():
            print(f"- {path}")
            for err in errors:
                print(f"  - {err}")
    else:
        print(f"validate_agent_tickets: OK ({len(tickets)} tickets)")

    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
