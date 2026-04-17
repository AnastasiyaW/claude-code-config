# templates/kb-skeleton -- drop-in knowledge base

A minimal, project-agnostic starter for the pattern described in
[principle 21 - Knowledge Base Enforcement](../../principles/21-knowledge-base-enforcement.md).

## What is in the box

```
kb-skeleton/
├── AGENTS.md                       # AAIF-standard entry, fill in
├── docs/kb/
│   ├── README.md                   # Meta-rules (keep as-is or tweak)
│   ├── INVARIANTS.md               # Empty table, add I-1, I-2 ...
│   ├── conventions.md              # Empty sections, fill per stack
│   ├── patterns.md                 # Empty sections, add recipes
│   ├── gotchas.md                  # Empty, grow organically
│   ├── decisions.md                # Empty ADR log
│   └── modules/
│       └── example.md              # One skeleton file, copy per module
├── scripts/
│   └── validate_kb.py              # Working validator, configure at top
└── .github/workflows/
    └── kb.yml                      # CI gate (GitHub Actions)
```

## Adoption in 15 minutes

1. **Copy the tree into your repo root.**

   ```bash
   cp -r kb-skeleton/AGENTS.md         <your-repo>/AGENTS.md
   cp -r kb-skeleton/docs               <your-repo>/docs
   cp -r kb-skeleton/scripts/validate_kb.py  <your-repo>/scripts/
   cp -r kb-skeleton/.github            <your-repo>/.github
   ```

2. **Fill `AGENTS.md`:** project one-liner, quick commands, source-of-truth docs.

3. **Configure `validate_kb.py`:** update the constants at the top
   (`REPO_ROOT`, source-area list) to match your project layout.

4. **Grow `INVARIANTS.md`** as your next review or first bug finds a
   rule worth codifying. Skeleton starts empty with a single example.

5. **Wire CI:** `.github/workflows/kb.yml` is already a working
   GitHub Actions file; just commit it.

6. **Start referencing.** Every test that locks a rule gets a
   docstring like `"regression: <rule name>"`. Every entry in
   `INVARIANTS.md` points at the test.

## What is NOT here

- Project-specific invariants (obviously).
- Opinionated per-module docs (you write one per area of your
  codebase).
- Language-specific conventions (the `conventions.md` skeleton just
  lists the *section titles* you should cover).

## Why this shape

See [principle 21](../../principles/21-knowledge-base-enforcement.md)
for the full rationale. Short version: review findings have three
durable forms -- fix, test, invariant -- and without all three, the
expensive review artifact evaporates into commit history within
weeks.

The kb-skeleton forces the third form to exist from day one.
