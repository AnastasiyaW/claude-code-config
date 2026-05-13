# <Layer name> -- Patterns

Layer-scoped reusable recipes. Each pattern earned its place by
appearing in 2+ features. Speculative ideas live in feature docs as
PC-N (feature-local principles) until they prove out.

## Identity and format

- IDs are stable per layer (`PT-1`, `PT-2`, ...). Never reuse retired IDs.
- Each entry has: when to use, the recipe, file pointers to current
  uses, and references to the invariants the pattern preserves.

## PT-1 -- <short pattern name>

**Use when:** <one-line trigger condition>.

**Recipe:**

```
<code snippet, pseudocode, or step list>
```

**Currently used in:**

- `<path/to/file.py>:<line>` -- F-NNN.
- `<path/to/file.py>:<line>` -- F-MMM.

**Preserves invariants:** [IV-N](invariants.md#iv-n).

**Alternative considered:** <approach we rejected, with one-line reason>.

<!-- Copy the block above per new pattern. -->
