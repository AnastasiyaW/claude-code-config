# <Layer name> -- Invariants

Layer-scoped hard rules. Same format as the project-wide
`docs/kb/INVARIANTS.md` (principle 21), but the scope is **this layer
only**. Project-wide invariants that happen to be enforced inside this
layer live in the project KB, not here -- reference them from a
feature doc instead.

Each rule has: a unique ID (`IV-N`), a one-line statement, a reason
pointing at the review finding or incident that motivates it, where it
is enforced in code, and the regression test that fails if it is
broken.

## Identity and format

- IDs are stable per layer (`IV-1`, `IV-2`, ...). Never reuse a retired
  ID. Use **layer-scoped IDs** -- `IV-1` in `L-security` is different
  from `IV-1` in `L-data`. References across layers should disambiguate:
  `L-security IV-1`.
- **Reason** always names a review finding, incident, ADR, or feature
  ID (F-NNN).
- **Enforced in** names the file with line range when specific.
- **Test** names the regression test (`path::name`) that fails on
  violation.

## Example entry (replace with your first real invariant)

### IV-1 -- <short rule statement>

**Statement:** <one sentence saying what MUST be true>.

**Reason:** F-NNN finding. <Brief note of what went wrong without this
rule>.

**Enforced in:** `<path/to/file.py>:<start>-<end>`.

**Test:** `<tests/test_file.py>::<test_name>`.

<!-- Copy the block above per new invariant. Keep the ID sequence
monotonic; once retired, do not reuse. -->

---

## Adding invariants

Same rules as project-wide invariants (see principle 21):

- Source: code review finding shipped with fix + test, or postmortem
  "prevent recurrence" item, or feature-doc IV-N that earned
  layer-wide scope after appearing in 2+ features.
- Anti-patterns: style preferences (those belong in `patterns.md`),
  aspirations ("we should X more often"), rules without a regression
  test.
