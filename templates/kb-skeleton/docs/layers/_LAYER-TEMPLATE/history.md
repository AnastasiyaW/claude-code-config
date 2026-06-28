# <Layer name> -- History

Reverse-chronological evolution log. **Append at the top** when a feature
in this layer reaches `status: done` or when an ADR retires a rule.

Each entry is one paragraph covering:

- **Date** (YYYY-MM-DD)
- **Feature ID or ADR ID** (F-NNN, D-N)
- **What changed** (one sentence)
- **Why** (one sentence, pointing at the motivating finding/incident)
- **Links** to the feature doc and to any new invariants/decisions
  introduced

This file is the **single answer** to the question "how did this layer
get to its current shape?" If a future session asks that question,
they should not need to grep git log.

---

<!-- Newest entries first. Copy the block below per new entry. -->

## 2026-MM-DD -- F-NNN <feature title>

<!-- One paragraph. What shipped, why, what it enabled or retired. -->

What changed: <one sentence>.

Why: <one sentence with link to the originating finding, incident, or ADR>.

See: `features/feat-NNN-slug.md`. New invariants:
[IV-N](kb/invariants.md#iv-n). New decisions: [D-N](kb/decisions.md#d-n).

---

## 2026-MM-DD -- Layer created

What changed: this layer was created to consolidate <concern>.

Why: <originating need -- incident, code review finding, or scope
explosion in another layer>.

Initial invariants: <list IV-1, IV-2 ...>. Initial principles in scope:
<list P-NN references>.
