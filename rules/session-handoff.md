# Session Handoff - Seamless Transitions Between Sessions

Drop this file into `.claude/rules/session-handoff.md` (project-local) or
`~/.claude/rules/session-handoff.md` (global) to enable manual handoff triggers.

## Manual trigger

When the user sends one of these phrases (or a close equivalent), immediately
write `.claude/HANDOFF.md` following the format below and stop working until
the user confirms.

**Trigger phrases:**

- "prepare handoff"
- "save context for new chat"
- "write handoff"
- "handoff this session"
- "we're closing, write handoff"
- "hand off this conversation"

**What to do when triggered:**

1. Write `.claude/HANDOFF.md` with the real content of the current session,
   not a template.
2. If the session covered multiple areas, group by topic instead of one flat
   list.
3. Always fill the "what did NOT work" section, even if everything succeeded -
   include false positives, near-misses, or discarded approaches.
4. Keep the file under 1500 tokens. It is a briefing, not a log.
5. After writing, tell the user: "Handoff written to .claude/HANDOFF.md, [N]
   lines. You can open a new chat now."
6. **Do NOT continue working** after writing the handoff. The user is closing
   the session.

**What NOT to include:**

- Raw tool call history or intermediate file reads
- Narrative of "I did X, then Y, then Z" - describe what is *currently true*,
  not what you did
- Duplicated content from CLAUDE.md or memory

## At session start

Check for `.claude/HANDOFF.md`. If it exists:

1. Read it silently.
2. Briefly summarize to the user in 3-5 lines: goal, current state, next step.
3. Ask: continue from the handoff, or start a new task?
4. Archive the handoff to `.claude/handoff-history/YYYY-MM-DD-HHMM.md` after
   incorporating it.
5. Keep the last 10 archives; delete older ones.

## At session end (long sessions over 15 minutes)

If the user has not explicitly triggered a handoff, write one before ending
the session anyway. This complements the Stop hook automation - if the hook
is not configured or fails to fire, the rule provides a fallback.

## HANDOFF.md format

```markdown
# Session Handoff - YYYY-MM-DD HH:MM

## Goal
What we were trying to accomplish and why.

## Done
- Concrete results with absolute file paths
- Grouped by topic if multiple areas

## What did NOT work
- Approach A - failed because [specific reason, with error message if any]
- Library B - version 2.x has [specific issue], fell back to 1.9

## Current state
- Working: [features/endpoints verified]
- Broken: [what's failing, with the actual error]
- Blocked: [what is waiting on external dependency]

## Key decisions
- Chose X over Y because [reason]
- Deferred Z until [condition]

## Next step
[A single concrete action to begin the next session - not a list]
```

## Why rules, not hooks

A `Stop` hook can force handoff writing mechanically, but requires the user
to configure `~/.claude/settings.json` with a Python script. This rule works
immediately in any session because Claude reads `.claude/rules/*.md` as part
of the system prompt.

**Use both:** the rule handles deliberate triggers and older sessions started
before automation was added. The hook handles forgetful users and guarantees
handoff for very long sessions.

See [alternatives/session-handoff.md](../alternatives/session-handoff.md) for
all 5 approaches (manual, hook, journal, framework, memory-only) compared
with pros, cons, and when-to-choose guidance.
