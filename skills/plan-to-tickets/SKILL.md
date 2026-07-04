---
name: plan-to-tickets
description: Use when a large plan, PRD, feature, refactor, research plan, or multi-step coding task must be split into small ready-for-agent tickets with acceptance criteria, verification commands, blockers, and vertical tracer-bullet slices. Do not use for small tasks that should be implemented directly, single-bug fixes, or chat-only summaries.
---

# Plan To Tickets

Turn a large plan into small, independently executable tickets. Use this before handing a broad plan to agents, before long autonomous work, or when the user asks for tickets/issues/slices.

## Output Location

If no issue tracker is explicitly selected, write local tickets under:

`<project>/.agent/tickets/<YYYY-MM-DD>-<slug>/`

Each ticket is one Markdown file:

`TICKET-001-short-slug.md`

## Required Ticket Shape

Each ticket must include these headings exactly:

- `## Status`
- `## Parent`
- `## What To Build`
- `## Acceptance Criteria`
- `## Verification`
- `## Blocked By`
- `## Notes`

`## Status` must contain `ready-for-agent` only when all acceptance criteria and verification steps are concrete.

`## Acceptance Criteria` must contain checklist items (`- [ ] ...`).

`## Verification` must contain at least one command, script, test, artifact check, or explicit manual-review gate.

## Slicing Rules

- Prefer vertical tracer bullets: a narrow complete path through the required layers, not "all backend" then "all UI" then "all tests".
- A ticket must be independently verifiable.
- Put prefactoring first only when it makes a later slice smaller or safer.
- Keep dependencies explicit in `## Blocked By`; write `None` when it can start immediately.
- Do not include stale-prone file paths unless the path is already a stable contract or current codebase evidence.
- Do not publish external tracker issues unless the user asked for that tracker.

## Workflow

1. Read the plan/spec and current repo context needed to avoid fake tickets.
2. Draft ticket files in dependency order.
3. Run the validator:

```powershell
python "$env:USERPROFILE\.claude\claude-code-config\scripts\validate_agent_tickets.py" --tickets-dir <ticket-dir>
```

4. Fix every validator failure before claiming the ticket split is ready.
5. Report the ticket directory and the count of ready tickets.

## Gotchas

- Horizontal tickets overload later agents. If a ticket cannot be verified alone, split it differently.
- "Implement feature" is not an acceptance criterion. ACs must describe observable behavior or artifacts.
- "Run tests" alone is weak verification. Name the test command or the artifact that proves success.
- Do not use this to postpone work. Ticketization is for large plans; small tasks should be implemented directly.
