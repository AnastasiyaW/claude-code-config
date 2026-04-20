# Principle 16 - Project Chronicles

## Problem

Handoffs solve the tactical problem: "what should the next session do?" But for long-running projects that span weeks or months, a different question emerges: **"how did we get here?"**

Individual handoffs are session-scoped - they capture the state at one point in time. After 20+ handoffs, the history becomes a pile of files with no narrative thread. New sessions can pick up where the last one left off, but they can't understand:
- Why approach A was abandoned in favor of B
- What the key turning points were
- Which dead ends were already explored (and why they failed)
- How the project's direction evolved over time

This is the same problem commit history has vs a CHANGELOG: one records every change, the other tells the story.

## Solution: Project Chronicles

A **chronicle** is a single file per long-running project that accumulates condensed entries at each significant milestone. It sits between handoffs (tactical, session-scoped) and project documentation (static, rarely updated).

```
.claude/chronicles/
├── search-engine.md      ← one chronicle per project
├── mobile-app.md
├── knowledge-base.md
└── ...
```

### Chronicle vs Handoff vs Documentation

| Aspect | Handoff | Chronicle | Documentation |
|---|---|---|---|
| **Scope** | One session | Entire project lifetime | Current state |
| **Question answered** | "What's next?" | "How did we get here?" | "How does it work?" |
| **Updated** | Every session | At milestones | When things change |
| **Lifespan** | Days | Months | Permanent |
| **Detail level** | Tactical (ports, commands) | Strategic (decisions, turns) | Reference (APIs, configs) |
| **Reader** | Next session's agent | Any future session | Humans and agents |

### Entry Format

Each chronicle entry is 3-7 lines - a digest, not a log:

```markdown
### 2026-04-11 — Model training reached target quality
Trained lightweight CNN (127K params) for image correction task.
- Decision: chose smaller diffusion backbone for inference, separate CNN for fast path
- Result: median error 1.99 (target was <2.5)
- Did NOT work: transformer-based approach - too heavy for target VRAM constraint
- Handoff: session-3
```

**What to include:**
- Decisions and their reasons ("chose X because Y")
- Turns/pivots ("started with A, switched to B because...")
- Quantitative results ("loss 1.99, baseline was 3.2")
- What did NOT work (saves future sessions from repeating dead ends)
- Cross-project connections ("this affects project Y")

**What NOT to include:**
- Tactical details (specific ports, SSH commands, container IDs)
- Routine updates without information value
- Full logs or command outputs - just the essence

## Integration with Handoffs

### Writing: Handoff → Chronicle

When writing a handoff for a long-running project:

1. Add a `**Project:** <slug>` field to the handoff
2. After writing the handoff, append a condensed entry to `.claude/chronicles/<slug>.md`
3. If no chronicle exists yet, create one from the template

The chronicle entry is NOT a copy of the handoff - it's a condensed strategic summary. A 100-line handoff might produce a 5-line chronicle entry.

### Reading: Chronicle → Context

When starting a session on a long-running project:

1. Read the chronicle (if it exists)
2. Briefly tell the user: "Chronicle: last entry from DD.MM - [essence]"
3. This gives strategic context without reading all historical handoffs

### Long-Running Project Identification

Mark projects as long-running in your memory/tracking system. A project is long-running if:
- It spans multiple weeks of intermittent work
- It has had 3+ handoffs
- It accumulates results over time rather than having a single "done" state
- Multiple sessions contribute to it without a clear end date

## Chronicle File Format

```markdown
# Chronicle: {Project Name}

**Path:** {absolute path to project}
**Status:** ACTIVE | PAUSED | DONE
**Started:** YYYY-MM-DD

## Timeline

### YYYY-MM-DD — {milestone title}
{What happened, 3-7 lines}
- Decision: ...
- Result: ...
- Did NOT work: ...
- Handoff: {handoff-id}

### YYYY-MM-DD — {next milestone}
...
```

## When to Add an Entry

Not every session deserves a chronicle entry. Add one when:

1. **A phase completes** - "Phase 1 done, moving to Phase 2"
2. **A significant decision is made** - "chose CNN over ViT because of VRAM constraint"
3. **A pivot happens** - "approach A failed, switching to B"
4. **A quantitative milestone is reached** - "accuracy hit target threshold"
5. **A dead end is confirmed** - "library X doesn't support Y, explored all alternatives"

Do NOT add entries for:
- Routine work sessions with no new insights
- Minor bug fixes or config changes
- Sessions that only continued existing work without decisions

## Scaling

Chronicles are append-only and grow over time. For very long projects (50+ entries):
- Consider splitting into phases: `my-project-phase1.md`, `my-project-phase2.md`
- Or add a "Summary" section at the top that condenses older entries
- Old entries remain valuable as searchable history even if not read in full

## Chronicles and Handoff Rollups

Chronicles and rollup handoffs solve adjacent problems and should be used together on long projects.

| Artifact | Purpose | When written |
|---|---|---|
| **Handoff** | "What should the next session do?" | End of every session |
| **Rollup handoff** | "Summarize handoffs 1..N so new sessions do not read all of them" | When handoff pile exceeds ~20 entries |
| **Chronicle entry** | "Why did the project go this way?" | At milestones / pivots / dead-end confirmations |
| **Chronicle** (whole file) | "How did we get here?" | Exists for the project lifetime |

The useful workflow:

1. Session writes a handoff (always).
2. If a milestone or pivot happened, session **also** appends a chronicle entry pointing at the handoff.
3. When the handoff pile gets too big, a session writes a rollup handoff covering handoffs 1..N. The rollup's `covers:` list should line up with the chronicle entries that cite those handoffs — if a chronicle entry cites handoff H and H is subsumed by a rollup, the chronicle entry's "Handoff: H" reference still resolves (the raw file is kept, just marked `rolled_up_into: ...`).

See [alternatives/session-handoff.md §F (Rollup Handoffs)](../alternatives/session-handoff.md) for the rollup pattern in detail (frontmatter layout, session-start protocol, attribution to MF0-1984 which introduced the `covered_until_message_id` pointer that this pattern borrows).

**When not to use rollups:** small projects (< 10 handoffs), short-lived work (< 2 weeks), or projects where reading every handoff is the point (onboarding material, audit trail). Rollups are a scale mitigation, not always a win.

## Relationship to Other Principles

- **Codified Context (07):** Chronicles are another form of codified context - project knowledge that persists across sessions
- **Deterministic Orchestration (04):** Chronicle entries follow a fixed format, not free-form narrative
- **Session Handoff (alternatives):** Chronicles complement handoffs, they don't replace them
- **Research Pipeline (13):** Research findings that affect a project should be noted in its chronicle
