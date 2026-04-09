# Managing Context in Long Sessions

## Problem

Context windows are finite. As a session progresses, the model accumulates conversation history, code snippets, tool outputs, and intermediate results. Eventually, quality degrades: the model forgets earlier decisions, contradicts itself, loses track of the plan, or starts "context anxiety" -- prematurely wrapping up work because it senses the window is filling.

This is not a theoretical concern. Sessions over 30 minutes routinely lose important context. Sessions over 2 hours are unreliable without explicit context management.

## Quick Comparison

| Aspect | A: JIT Loading | B: Full Context Upfront | C: Compaction + Re-injection | D: Fresh Sessions |
|--------|---------------|------------------------|-----------------------------|--------------------|
| **Context efficiency** | High | Low | Medium | High |
| **Setup discipline** | High (must persist to files) | None | Low | High (must write handoff) |
| **Session continuity** | Good (via files) | Perfect (until window fills) | Partial (compaction loses nuance) | None (by design) |
| **Max effective duration** | Hours | 30-45 minutes | 1-2 hours | Unlimited (via chaining) |
| **Recovery from degradation** | Re-read files | Not possible | Re-inject from files | Start fresh |
| **State durability** | Excellent (in repo) | None (in memory only) | Medium (depends on what was compacted) | Excellent (in handoff) |
| **Overhead per step** | Read/write files | None | Periodic compaction | Session setup |
| **Best for** | Multi-hour focused work | Quick tasks <30 min | Medium tasks, exploration | Multi-day projects |

---

## A: JIT Loading (Codified Context)

**Source:** [2602.20478] Codified Context: Infrastructure for AI Agents in a Complex Codebase

**Core idea:** Load only what is needed for the current step. Store results in files, not in conversation. After compaction, re-inject only critical state from those files. Treat context as infrastructure, not documentation.

**Key principles:**
- CLAUDE.md is runtime config for the agent, not a wiki for humans
- `.claude/rules/` is conditional context injection, not a reference guide
- Memory files are persistent state, not notes
- PLAN.md, TODO.md, DECISIONS.md are structured handoff, not logs

**Context engineering pipeline:**
```
rules -> state -> JIT retrieval -> pruning -> compaction policy -> re-inject -> isolation
```

**Practice:**
- Each step reads only the files it needs (not the entire project)
- Results of each step go into files (plan.md, state.json), not chat history
- After compaction, re-inject: current plan state, active decisions, known gotchas
- Sub-agents get explicit `context_hint` -- only what they need, nothing more

**Pros:**
- [+] Most token-efficient -- only relevant context is loaded at any moment
- [+] State survives compaction, session restarts, even machine reboots (it is in files)
- [+] Scales to multi-hour sessions without degradation
- [+] Forces good engineering practice -- decisions are documented, state is explicit
- [+] Sub-agent isolation is natural -- pass the file, not the entire conversation

**Cons:**
- [-] Requires discipline -- every step must read from and write to files
- [-] Overhead per step (file read/write) adds latency and token cost
- [-] Must decide upfront what to persist and what to discard
- [-] If you forget to persist something, it is lost after compaction
- [-] Initial setup cost to establish the file structure and conventions

**When to choose:** Default approach for any session expected to last more than 30 minutes. Projects with multiple contributors (files are shared artifacts). Tasks that span multiple sessions. Any work where losing context would mean redoing significant effort.

---

## B: Full Context Upfront

**Core idea:** Load everything relevant at the start of the session. The model has all the context it needs from the beginning. Simple, no file management, no context switching.

**Typical setup:** Paste the entire CLAUDE.md, relevant code files, the task description, and constraints into the initial prompt or have them auto-loaded.

**Pros:**
- [+] Simplest approach -- no context management overhead
- [+] Model has maximum information from the start
- [+] No risk of missing context that was not loaded
- [+] No file read/write overhead per step
- [+] Works perfectly for short, focused tasks

**Cons:**
- [-] Wastes tokens on context that may never be relevant
- [-] Causes context anxiety -- model sees the window filling up and starts rushing
- [-] Quality degrades past ~30-45 minutes as the window fills with tool outputs
- [-] No recovery from degradation -- cannot "unload" irrelevant context
- [-] Conversation history displaces the initial context as the session progresses
- [-] Does not scale to complex projects with large codebases

**When to choose:** Quick tasks under 30 minutes. The total context (CLAUDE.md + relevant code + task) fits comfortably in the window with room for conversation. You are doing exploration or a one-off task where context management overhead is not justified.

---

## C: Compaction with Re-injection

**Core idea:** Let the system compact conversation history naturally. After compaction, re-inject critical state from files that were written during the session. Balances continuity with freshness.

**Practice:**
- Work normally, let conversation history accumulate
- Before expected compaction (or after it happens), ensure critical state is in files
- After compaction, re-read: current plan, active decisions, known issues
- Continue with the refreshed (but lighter) context

**Pros:**
- [+] Low overhead during normal work -- no constant file management
- [+] Maintains conversational continuity better than fresh sessions
- [+] Re-injection recovers the most important context after compaction
- [+] Good balance between effort and effectiveness for medium-length sessions
- [+] Natural fit for Claude Code's built-in compaction behavior

**Cons:**
- [-] Compaction can lose nuance -- subtle decisions or rejected alternatives may disappear
- [-] You must anticipate what to save before compaction happens (often unpredictable)
- [-] Re-injection requires knowing what was lost (hard to know what you do not know)
- [-] Partial context after compaction can lead to contradicting earlier decisions
- [-] Less reliable than JIT loading for critical state preservation

**When to choose:** Sessions of 1-2 hours where JIT loading feels like too much overhead. Exploratory work where you do not know upfront what will be important. When you are already working and realize the session is going longer than expected (retrofit context management).

---

## D: Context Reset (Fresh Sessions)

**Core idea:** Start a new session for each major step. Pass state between sessions via structured handoff artifacts -- documents that contain everything the next session needs to know. Each session gets perfectly clean context, zero degradation.

**Handoff artifact structure:**
```
# Handoff: [Task Name]
## Current State: what has been done
## Next Step: what to do now
## Active Decisions: choices made and why
## Known Issues: gotchas, rejected approaches
## Files Modified: what changed and where
## Verification Status: what has been tested
```

**Pros:**
- [+] Cleanest context every time -- no degradation, no accumulated noise
- [+] Unlimited effective duration -- chain as many sessions as needed
- [+] Each session is focused on one step, not the entire history
- [+] Handoff artifacts become permanent project documentation
- [+] Natural checkpoint/resume -- pick up from any handoff artifact

**Cons:**
- [-] Loses conversational nuance -- the next session does not "remember" how you discussed things
- [-] Handoff writing is overhead (5-10 minutes per transition)
- [-] Slower setup per session (model must read and internalize the handoff)
- [-] Risk of losing context that was not included in the handoff
- [-] Multiple short sessions cost more than one long session (per-session overhead)

**When to choose:** Multi-day projects where sessions span hours or days. Tasks with natural breakpoints (build phase, test phase, deploy phase). When you need auditable records of progress. When context degradation in long sessions is causing errors.

---

## KV-Cache as the Production Metric (Manus Insight)

**Source:** [Context Engineering for AI Agents: Lessons from Building Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) by Yichao 'Peak' Ji

All four approaches above focus on "what fits in the window." Manus's production experience (fourth framework rewrite, averaging 100:1 input:output token ratio) shows this is the wrong frame. The right metric is **KV-cache hit rate**, and the right optimization is **prefix stability**.

### Why KV-cache dominates

On cached tokens, Claude API pricing is roughly 10x cheaper than uncached (~$0.30/M vs ~$3.00/M). On a 50-tool-call task with 100:1 input:output ratio, the cache hit rate is not a minor optimization - it is **the** cost and latency driver. Production Claude Code sessions routinely hit 92-99% cache rates when prefixes are stable. When a regression drops cache hits to 36% (as happened in Claude Code v2.1.62), users felt the equivalent of reprocessing the entire context every turn.

### The four rules for cache-friendly context

1. **Stable prefixes.** Put the most stable content first. Timestamps, random IDs, or "current time" values in the cached section invalidate the cache on every call. If you need a timestamp, put it at the end.

2. **Mask tools, do not swap them.** Resist the temptation to "add tools when needed, remove them when done." Every tool definition swap rewrites the prompt prefix and burns the cache. Instead, define all tools once in the cached section, and use a state machine + logit masking at decode time to make disallowed tools have probability -infinity. Same prompt, different behavior.

3. **Filesystem as extended context.** When the context would grow large, write intermediate results to files (`.agent/state.json`, `notes.md`, `findings/`), and keep the in-prompt reference to a pointer. The file is read on demand via a tool call, not embedded. This matches our Proof Loop artifacts pattern.

4. **Preserve errors in context.** Counterintuitively, failed actions and stack traces should stay in the prompt, not be hidden. The model sees its mistake and does not repeat it. Context cost is small (~5% overhead); recovery benefit is large (~40% fewer retry cycles in Manus measurements).

### The todo.md recitation trick (attention hack)

LLMs suffer from "lost in the middle" - information at the midpoint of a context window is ~30% less likely to be used than information at the start or end. Manus exploits this with a **self-updating todo.md** at the end of the context:

```markdown
# Current Task Progress [updated every 5 tool calls]

## Goal
[unchanged, high-level]

## Completed
- [x] Step 1
- [x] Step 2

## In Progress
- [ ] Step 3 (blocked on X)

## Next 3 Steps
1. ...
2. ...
3. ...
```

The agent rewrites this file every 5-10 tool calls. Because it lives at the end of the context, it benefits from "recency bias" - the model actually attends to it. The refresh is small and cache-friendly (~300 tokens). Side benefit: it is also a natural audit trail for session handoff.

### Interaction with the four approaches above

| Approach | KV-cache interaction |
|---|---|
| **A: JIT Loading** | Compatible. Files loaded on demand are cached for the rest of the session. The trick is loading them at stable, predictable points so the prefix structure is repeatable. |
| **B: Full Context Upfront** | Highest cache hit rate initially, but the large prefix is brittle - any edit invalidates everything. Best for short, focused tasks where no edits are expected. |
| **C: Compaction + Re-injection** | Compaction rewrites the prefix, which always invalidates the cache. Use only when the cache hit was already declining from context bloat - compaction trades cache for capacity. |
| **D: Fresh Sessions** | Each new session rebuilds the cache from scratch. This is a cost, but the benefit is a known-clean prefix. Amortizes well if handoff artifacts are stable across sessions. |

### Measuring KV-cache in your own sessions

- Claude API returns cache hit metrics in the response object (`cache_creation_input_tokens` vs `cache_read_input_tokens`)
- Claude Code dashboards expose per-session cache statistics
- Third-party observability: LangSmith, Helicone have cache tracking
- Rule of thumb: below 80% hit rate on a multi-call session, something is wrong with your prefix stability

### What not to do

- Do **not** add current timestamps at the top of CLAUDE.md or AGENTS.md - it invalidates cache on every session
- Do **not** dynamically inject tool definitions based on task state - use masking instead
- Do **not** dump raw tool outputs verbatim - truncate or summarize before adding to context
- Do **not** reorder sections in CLAUDE.md unless you are also willing to take the cache hit

---

## Recommendation

**Choose based on expected session duration:**

- **Under 30 minutes:** B (Full Context Upfront). Do not bother with context management. Load what you need, get the work done.

- **30 minutes to 2 hours:** A (JIT Loading) as default. Write state to files as you go. When compaction happens, you have everything you need to re-inject.

- **Over 2 hours:** D (Fresh Sessions). Break the work into phases. Write a handoff artifact at each transition. Each session starts clean and focused.

- **Unexpected long session:** C (Compaction + Re-injection). If you started with B and the session went longer than expected, start writing critical state to files and use re-injection after compaction.

**The key insight:** Context management is not about the model's capability -- it is about information persistence. Files persist. Conversation history does not (not reliably, not across compaction, not across sessions). The more important the information, the sooner it should be in a file.

**Anti-patterns to avoid:**
- Loading the entire codebase "just in case" (wastes tokens, triggers anxiety)
- Relying on conversation history for decisions made 50 messages ago (it may be compacted)
- Telling the model to "remember" something instead of writing it to a file
- Using one endless session for a multi-hour task without any state persistence
