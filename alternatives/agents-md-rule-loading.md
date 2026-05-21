# Rule Corpus Loading: Always-On Blob vs JIT

How should a project's instruction corpus -- AGENTS.md, CLAUDE.md, and a `rules/`
directory -- be loaded into an agent's context? Always, in full? Or on demand?

## The evidence this matters

Gloaguen, Mündler, Müller, Raychev, Vechev (2026), "Evaluating AGENTS.md: Are
Repository-Level Context Files Helpful for Coding Agents?" (arXiv 2602.11988) tested
coding agents with and without repository context files. Finding: context files -- both
auto-generated and human-written -- **reduced task success rate** versus no repository
context, while **increasing cost by 20%+**. Mechanism: context files push agents toward
**broader exploration** (more file traversal, more testing). The paper's conclusion:
"unnecessary requirements from context files make tasks harder; human-written context
files should describe only minimal requirements."

Caveat on caching: prompt caching makes always-loaded content *cheap* (cache reads are
~10x cheaper) but not *harmless*. The success-rate degradation is a behavioral effect --
a cached requirement is still a requirement the model serves. Caching solves the cost
axis, not attention dilution.

## Verified loading mechanics (Claude Code, code.claude.com/docs/en/memory)

- Files in a `rules/` directory **without frontmatter load unconditionally**, every
  session.
- `paths:` YAML frontmatter scopes a rule to file globs -- it loads only when the agent
  reads a matching file. It is the only conditional-activation field.
- Skills use **progressive disclosure**: the `description` is always in context (enables
  triggering); the body and `references/` load only when the skill activates.
- `@path` imports load **at launch** alongside the file that references them -- they help
  organization but do **not** reduce context.

## Approach A -- Always-on blob

**Source:** default behavior -- drop everything into AGENTS.md / CLAUDE.md / `rules/`.
**Core idea:** all guidance present every session; nothing to retrieve.

**Pros:** zero retrieval logic; guidance guaranteed visible.
**Cons:** directly the failure mode the paper measures -- standing "requirements" cause
scope expansion, +20% cost, lower success. Attention dilution scales with corpus size.
Verbose human-written docs that restate code add semantic noise and drift out of sync.

**When to choose:** only for genuinely always-relevant content -- safety guardrails and
the few core methodology rules that apply to every task. Keep it small.

## Approach B -- Path-scoped rules

**Source:** `paths:` frontmatter.
**Core idea:** a rule loads only when the agent touches a file matching its glob.

**Pros:** zero cost until a matching file is read; good fit for rules correlated with a
file type (frontend conventions -> `**/*.{css,tsx}`).
**Cons:** only works when the trigger *is* a file read. Topic-bound guidance that is not
file-correlated (cloud ops, API conventions, research workflow) has no reliable glob.

**When to choose:** guidance that maps cleanly to file types.

## Approach C -- Skills as JIT + lean indexed root

**Source:** skill progressive disclosure + an index in a lean root file.
**Core idea:** topic-bound guidance becomes a skill -- its one-line description stays in
context, its body loads only on trigger. The root file shrinks to always-on core plus an
index naming where each topic lives.

**Pros:** the only JIT mechanism for topic-bound (non-file-correlated) guidance. N skill
descriptions cost ~N short lines; N rule files cost N full files. The index keeps
everything discoverable -- nothing is lost, only deferred.
**Cons:** a skill helps only if its description triggers reliably -- a weak description
means the guidance silently never loads. Safety-critical guidance must NOT be skill-gated
(a missed trigger = an absent safety rule). Requires up-front restructuring.

**When to choose:** any large, topic-diverse instruction corpus.

## Recommendation

Tier the corpus -- do not pick a single mechanism:

1. **Always-on core** (root file + a handful of unconditional rules): safety, billing,
   the core methodology that genuinely applies to every task. Keep the root file lean
   (Claude Code docs target under 200 lines) and trim verbosity.
2. **Path-scoped rules**: guidance correlated with file types.
3. **Skills**: topic-bound operational and domain guidance -- description triggers, body
   loads on demand.
4. **Index** in the root file: a map naming every skill / path-rule / principle, so
   nothing is lost -- only deferred.

Worked example: a 39-file always-loaded rule corpus restructured to ~10 always-on and
path-scoped rules + ~10 skills + a ~150-line indexed root file -- topic guidance moved to
JIT without losing any content.

**Open validation:** this is an A/B-testable claim -- same task set, blob vs tiered-JIT
config, measure out-of-scope file reads + tokens + success rate. Caching obscures the
cost axis; the behavioral axis is the one to measure. Treat the recommendation as
evidence-backed but pending local confirmation.

## Relationship to other docs

- [context-management.md](context-management.md) -- JIT loading vs full context within a
  *session*; this doc is about the *instruction corpus* specifically.
- [principle 07 - Codified Context](../principles/07-codified-context.md) -- context as
  infrastructure; JIT loading principle.
- [principle 08 - Skills Best Practices](../principles/08-skills-best-practices.md) --
  writing skill descriptions that trigger reliably (critical for Approach C).
