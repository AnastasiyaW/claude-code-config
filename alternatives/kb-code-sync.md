# KB-Code Sync: API Drift Detection

Date: 2026-04-12

## Problem

When using a Knowledge Base (KB) as code documentation, KB articles define API signatures (classes, functions, structs) BEFORE code is written. As implementation progresses, APIs diverge from KB specs:
- Function names change
- Parameters added/removed
- Modules renamed
- Gotchas discovered that aren't in KB

Without automated detection, KB becomes stale and misleading.

## Solution: Three-way linkage

```
KB article (spec)  <->  .h file (implementation)  <->  test file (verification)
```

Script `kb_code_sync.py` scans KB articles for C++ code blocks, extracts symbols (class/struct/function names), and checks:
1. **Is it in code?** - grep .h/.cpp files for the symbol
2. **Is it tested?** - grep test files for the symbol
3. **Report drift** - symbols in KB but not in code, or in code but untested

## Output Example

```
KB-Code Sync Report
==================================================
KB symbols found:    59
Present in code:     21/59
Covered by tests:    15/59

NOT IN CODE (38):
  engine/graduated-backdoor.md: SecurityScore     # Phase 2, not yet
  converter/trustmark-watermark.md: EmbedWatermark # Phase 5, not yet

IN CODE BUT UNTESTED (6):
  ApplyFinalConv (inverse_scramble.h)
  GeneratePolyCoeffs (scramble.h)

Code coverage:  36%
Test coverage:  25%
```

## Integration

Add to SessionStart hook in `.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hook_command": "python .claude/scripts/kb_code_sync.py",
        "description": "Check KB-Code API sync (drift detection)"
      }
    ]
  }
}
```

Agents see sync report at session start - know what's implemented, what's not, what needs tests.

## Key Design Decisions

- **KB is source of truth for API design** - write KB article BEFORE code
- **Code must match KB** - if implementation differs, update KB (not silently diverge)
- **Tests verify linkage** - symbol in KB + symbol in code + symbol in test = fully linked
- **Percentage is a roadmap** - 36% code coverage = 64% of KB specs not yet implemented (expected in Phase 1)

## When to Use

- Projects with KB/documentation-first development
- Multi-agent setups where different agents implement different modules
- Any project where specs drift from implementation

## Files

- `kb_code_sync.py` - the sync checker script (pure Python, no deps)
- Works with any MkDocs-style KB with cpp code blocks
- Module mapping configurable via `MODULE_MAP` dict
