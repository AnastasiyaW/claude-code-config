# INVARIANTS -- hard rules that must hold across the codebase

Every rule here is load-bearing. Breaking one does not just produce
uglier code -- it restores a defect that a review found and that a
regression test locks in. When you want to deviate, **add an ADR to
`decisions.md` first**.

Each rule has: a unique ID, a one-line statement, a reason (pointing
at the review finding or incident that motivates it), where it is
enforced, and the regression test that fails if it is broken.

## Identity and format

- IDs are stable (`I-1`, `I-2`, ...). Never reuse a retired ID.
- **Reason** always names a review finding, incident, or ADR.
- **Enforced** names the file with line range when specific.
- **Test** names the regression test (`path::name`) that fails on
  violation.

## Example entry (replace with your first real invariant)

### I-1 -- <short rule statement>

**Statement:** <one sentence saying what MUST be true>.

**Reason:** <review finding ID, incident, or ADR reference>. <Brief
note of what went wrong without this rule>.

**Enforced in:** `<path/to/file.py>:<start>-<end>`.

**Test:** `<tests/test_file.py>::<test_name>`.

<!-- Copy the block above per new invariant. Keep the ID sequence
monotonic; once retired, do not reuse. -->

---

## Adding invariants

Source material:

- After a code review, any finding that ships with a fix and a test is
  eligible.
- After an incident, the postmortem's "prevent recurrence" section
  usually has one.
- After a sub-agent review round, consensus findings (multiple agents
  flagged same issue) are strong candidates.

Anti-patterns to avoid:

- **Style preferences** disguised as invariants. Style belongs in
  `conventions.md`, which may also be enforced but is advisory.
- **Aspirations** ("we should use X more often"). An invariant is
  a binary must/must-not.
- **Rules without a regression test.** If the rule cannot be
  expressed as a failing test, it is probably a convention.
