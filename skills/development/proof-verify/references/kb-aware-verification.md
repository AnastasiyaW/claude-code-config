# KB-Aware Verification

When a project has a knowledge base (wiki, docs, .kb/), the verifier should check not only acceptance criteria from PLAN.md but also conformance to project knowledge base.

## What This Adds

Standard verification: "does the code do what the plan says?"
KB-aware verification: "does the code do it THE WAY the project does things?"

## How It Works

### In PLAN.md: KB Reference Section

```markdown
## Knowledge Base Reference
- `docs/architecture.md` - system architecture, component boundaries
- `docs/coding-standards.md` - naming, error handling, logging patterns
- `.kb/patterns/` - approved patterns for common tasks
- `CLAUDE.md` - project-level rules and constraints
```

### Verifier Prompt Extension

Add to the standard verifier prompt:

```
ADDITIONAL: This project has a knowledge base. After checking each AC,
also verify conformance:

1. Read the KB sections listed in PLAN.md "Knowledge Base Reference"
2. For each changed file, check:
   - Naming conventions match KB standards
   - Error handling follows KB patterns
   - Architecture boundaries respected
   - No anti-patterns from KB "Don't do" sections
3. Add a "KB Conformance" section to VERDICT.md:

## KB Conformance

### Coding Standards
**Status:** CONFORM | DEVIATE
**Deviations:** [list specific deviations with file:line]

### Architecture
**Status:** CONFORM | DEVIATE
**Deviations:** [list boundary violations]

### Patterns
**Status:** CONFORM | DEVIATE
**Deviations:** [list where approved patterns were not used]
```

### Where Knowledge Bases Live

Projects typically store KB in one of:

| Location | Format | Example |
|---|---|---|
| `docs/` | Markdown files | Architecture, API docs, guides |
| `.kb/` | Structured knowledge | Patterns, decisions, conventions |
| `CLAUDE.md` | Agent config | Rules, constraints, red lines |
| `.claude/rules/` | Conditional rules | Context-specific guidelines |
| `wiki/` or `.wiki/` | Wiki-style KB | Cross-linked knowledge articles |
| `codebase-kb/` | Generated KB | Auto-extracted code docs |

The verifier reads ALL listed KB sources before checking code.

### Example: Verifier Catches Convention Violation

Plan says: "AC3: API endpoint returns user data"
Verifier runs the check: PASS - endpoint works.

But KB says: `docs/coding-standards.md` → "All API responses wrapped in `{data: ..., meta: {...}}`"
The new endpoint returns raw `{name: "...", email: "..."}` without wrapper.

VERDICT: AC3 PASS, but KB Conformance DEVIATE:
```
### KB Conformance - Coding Standards
**Status:** DEVIATE
**Deviations:**
- src/api/users.py:42 - Response not wrapped in standard {data, meta} envelope
  KB reference: docs/coding-standards.md line 78
```

This catches things that ACs miss - because ACs test functionality, not style.

## When to Skip KB Check

- Prototype / spike (explicitly marked in PLAN.md constraints)
- KB is outdated (verifier flags this instead)
- Greenfield project with no KB yet
