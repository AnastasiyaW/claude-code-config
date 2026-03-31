# Iterative Code/Prompt Optimization

## Problem

You have a measurable output -- test pass rate, latency, prompt accuracy, bundle size, coverage percentage -- and you want to improve it systematically. The naive approach (make changes, hope they help) wastes time and often regresses. How do you improve iteratively without getting stuck in local optima or losing track of what worked?

## Quick Comparison

| Aspect | A: Autoresearch (Linear) | B: HyperAgent (Branching) | C: Manual Iteration | D: Eval-Driven Development |
|--------|-------------------------|--------------------------|--------------------|--------------------------|
| **Automation** | Fully automated | Fully automated | Human-driven | Semi-automated |
| **Exploration strategy** | Linear (one path) | Branching (parallel paths) | Judgment-based | Goal-defined, strategy-free |
| **Cost per iteration** | ~$0.10 | ~$0.10-0.50 | Human time | ~$0.10-1.00 |
| **Cost for 100 iterations** | ~$10 | ~$50 | 20+ hours | ~$10-100 |
| **Local optima risk** | High | Low | Medium | Medium |
| **Causality tracking** | Clear (one change) | Complex (version graph) | Mental model | Implicit |
| **Setup effort** | Low (eval script) | High (version graph infra) | None | Medium (eval suite) |
| **Best for** | Known-metric optimization | Research/ML experiments | Subjective quality | Defining "done" first |

---

## A: Autoresearch (Linear)

**Source:** Andrej Karpathy (github.com/karpathy/autoresearch, Mar 2026) + uditgoenka/autoresearch (Claude Code plugin)

**Core idea:** Read the current state. Change ONE thing. Test mechanically. If the metric improved and nothing broke, keep. Otherwise, discard (git revert). Repeat. Simple, clear causality, overnight automation.

**Three conditions for applicability:**
1. Numerical scoring -- binary pass/fail criteria aggregated to a percentage
2. Automated evaluation -- eval scripts without human involvement
3. Single-file mutation -- one target file changes per iteration

**Key rules:**
- One change per iteration (atomicity = clear causality)
- Mechanical verification only (metrics, not opinions -- agents game subjective scales)
- Git = memory (`experiment:` commits, git revert on failure)
- Guard mechanism: Verify (metric improved?) + Guard (nothing broke?)
- 3-6 binary assertions (<3 = loopholes, >6 = checklist gaming)

**Pros:**
- [+] Simple to implement -- eval script + mutation loop
- [+] Clear causality -- you know exactly which change caused which improvement
- [+] Cheap (~$0.10 per cycle, $5-25 overnight for 50-100 experiments)
- [+] Runs unattended -- set it up, go to sleep, review results in the morning
- [+] Git history becomes a record of what worked and what did not
- [+] Works for prompts, code, configs, templates -- anything with a measurable score

**Cons:**
- [-] Linear exploration -- only follows one path, gets stuck in local optima
- [-] Cannot discover that a fundamentally different approach would score better
- [-] Single-file constraint means you cannot optimize cross-file interactions
- [-] Requires a good eval script -- garbage eval in = garbage optimization out
- [-] Blind to subjective quality (readability, maintainability, elegance)

**When to choose:** You have a clear numeric metric and an automated way to measure it. The optimization target is a single file (prompt, config, function). You want hands-off overnight improvement. The search space is narrow enough that linear exploration will find improvements.

---

## B: HyperAgent (Branching Version Graph)

**Source:** [2603.19461] HyperAgent paper + Contree microVM infrastructure

**Core idea:** Instead of linear keep/discard, maintain a tree of experiments. `select_next_parent` picks the most promising branch to explore next. Every ~20 iterations, meta-optimize: analyze which types of changes produced gains, update the mutation strategy itself.

**Evolution levels:**
- Level 1 (Autoresearch): Linear keep/discard
- Level 2: Branching version graph with parallel exploration
- Level 3: Meta-optimization of mutation strategy every ~20 iterations
- Level 4: Multi-task transfer -- patterns from one optimization carry to another

**Infrastructure (Contree):**
- `result_image` UUID = immutable snapshot of each state
- `disposable=false` = save a promising branch
- `wait=false` x N = explore 3-5 mutations in parallel
- `set_tag` = mark the best parent for next iteration

**Pros:**
- [+] Escapes local optima by exploring multiple branches simultaneously
- [+] Meta-optimization learns which mutation types work (imp@50: 0 -> 0.63 in ~200 iterations)
- [+] Parallel exploration via Contree microVMs -- 3-5 experiments at once
- [+] Full isolation and zero-cost rollback per experiment
- [+] Emergent behaviors: agents spontaneously create persistent memory and tracking tools

**Cons:**
- [-] Complex infrastructure -- requires Contree microVMs or equivalent version graph system
- [-] Higher cost per iteration due to parallel branches ($0.10-0.50 vs $0.10)
- [-] Version graph adds debugging complexity (which branch caused which outcome?)
- [-] Overkill for simple optimization problems with narrow search spaces
- [-] Meta-optimization needs ~200 iterations to show significant benefit

**When to choose:** Research or ML experiments where local optima are a real problem. The search space is large and multi-dimensional. You have Contree or equivalent infrastructure for parallel isolated execution. The optimization target justifies hundreds of iterations.

---

## C: Manual Iteration

**Core idea:** Human reviews results, forms a hypothesis about what to change, makes the change, reviews results again. The oldest optimization method. Highest judgment quality, lowest throughput.

**Pros:**
- [+] Best judgment quality -- humans understand context that metrics cannot capture
- [+] Can change strategy radically based on insight ("this whole approach is wrong")
- [+] No infrastructure needed
- [+] Can optimize for subjective quality (readability, UX, design coherence)
- [+] Catches when the metric itself is wrong (optimizing the wrong thing)

**Cons:**
- [-] Slow -- a human makes maybe 5-10 iterations per hour
- [-] Does not scale -- you cannot run 100 experiments overnight
- [-] Human fatigue degrades judgment quality over time
- [-] Causality tracking depends on human memory and discipline
- [-] Expensive (human time is the most expensive resource)

**When to choose:** The quality criteria are subjective and cannot be reduced to a script. The optimization requires strategic thinking (architecture decisions, UX design). You are in early exploration and do not yet know what metric to optimize. The number of iterations needed is small (<20).

---

## D: Eval-Driven Development

**Core idea:** Write evals first, then iterate until they pass. Instead of defining an optimization strategy, define what "good" looks like. The eval suite becomes the specification. How you get there matters less than whether you arrive.

**Process:**
1. Define 3-6 binary assertions that together mean "this is good enough"
2. Run the current state against evals -- get a baseline score
3. Make changes (any strategy: manual, autoresearch, or just intuition)
4. Run evals again -- did the score improve?
5. Repeat until all evals pass

**Pros:**
- [+] Forces clarity about what "good" means before you start optimizing
- [+] The eval suite is a durable artifact -- reusable, shareable, version-controlled
- [+] Strategy-agnostic -- pair with A (autoresearch) or C (manual) as needed
- [+] Prevents over-optimization of the wrong metric
- [+] 3-6 assertions sweet spot: enough to be meaningful, few enough to avoid gaming

**Cons:**
- [-] Requires good eval design -- bad evals lead to bad optimization
- [-] Not all quality dimensions are easily scriptable
- [-] Eval creation is upfront work before any "productive" optimization begins
- [-] Evals themselves need maintenance as requirements evolve
- [-] Does not tell you how to improve -- only whether you have improved

**When to choose:** As a first step before choosing any optimization strategy. You are not sure what "better" means yet. You want to share the definition of quality with a team. The optimization will be automated (evals are required for autoresearch).

---

## Recommendation

**Recommended progression:**

1. **Start with D (Eval-Driven Development).** Before optimizing anything, define what "good" looks like. Write 3-6 binary assertions. Run them. Get a baseline. This step is never wasted -- the evals become infrastructure for everything that follows.

2. **Automate with A (Autoresearch) for single-metric improvement.** Once you have evals, autoresearch can run overnight. $5-25 buys you 50-100 experiments with clear causality tracking. This is the sweet spot for most practical optimization: prompts, configs, single functions.

3. **Use B (HyperAgent) only for research-grade problems.** When the search space is large, local optima are a real problem, and you have the infrastructure for parallel exploration. Most engineering optimization does not need this -- save it for ML experiments or prompt engineering at scale.

4. **Keep C (Manual Iteration) for judgment calls.** When the metric is wrong, when the approach needs rethinking, or when subjective quality matters. Humans are best at knowing when to stop optimizing and start over.

**Combination that works well:**
- D (define evals) -> A (automate overnight) -> C (human reviews the best result and decides next direction) -> A (automate again)
- This cycle of machine-speed exploration with human-judgment steering is more effective than either alone
