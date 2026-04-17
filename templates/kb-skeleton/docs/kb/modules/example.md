# modules/<area> -- `<path/to/module>`

<!-- Copy this file once per significant area of the codebase. Rename
to match the directory / package name. The validator expects
`docs/kb/modules/<area>.md` to exist for every `<area>/` under your
source root (configurable at top of validate_kb.py). -->

Brief: 2-3 sentences about what this module is, who uses it, and the
boundary it defends.

## Public API

<!-- Table or list of what this module exports. Reference file +
line number so the validator can verify the reference. -->

| Name | Signature / type | Purpose |
|------|------------------|---------|
| `foo` | `async def foo(x: int) -> Foo` | Does X. |
| `Bar` | `class Bar` | Represents Y. |

## Contracts / invariants

<!-- Bullet list referencing invariant IDs from INVARIANTS.md that
govern this module. Do NOT duplicate the invariants -- reference them. -->

- **I-N**: short tag.
- **I-M**: short tag.

## Use sites

<!-- Where public names of this module are imported. Concrete paths,
not just "various handlers". -->

- `path/to/caller1.py:42-48` -- uses `foo()` for ...
- `path/to/caller2.py:120` -- uses `Bar` to ...

## Extending

<!-- Pointer to patterns.md::P-N plus module-specific notes. -->

See `patterns.md` SS **P-N** for the general recipe.

Module-specific notes:

- If you add a new public name, remember to update the Public API
  table above.
- If the new name touches a sensitive contract (secret handling,
  audit row, etc.), add or reference an invariant.

## Common mistakes

- Mistake 1 (one-liner with fix pointer).
- Mistake 2.
- Mistake 3.
