# How It Works - Technical Deep Dive

How each technology in this configuration system actually works, with real examples and measurements.

If you read the [README](README.md) and thought "okay but HOW does this work mechanically?" - this page is for you.

---

## Rules: Conditional Context Injection

**The problem:** A 582-line CLAUDE.md loaded into every session wastes context on irrelevant instructions. SSH rules during article writing. Formatting rules during debugging.

**The mechanism:** Claude Code's `.claude/rules/` directory contains rule files that are loaded based on file path patterns. Each file has a glob pattern in its name or frontmatter - the rule only enters context when the agent works with matching files.

```
.claude/rules/
  session-handoff.md        # always loaded (no pattern)
  memory-format.md          # always loaded
  research-copies.md        # loaded when research tasks detected
```

**What actually happens at runtime:**
1. Agent receives a task
2. Claude Code checks which rule files match the current working context
3. Only matching rules are injected into the system prompt
4. The rest never consume tokens

**Measured impact:** 9 rule files, 561 lines total. In a typical session, 3-4 are active (200-250 lines). The other 300+ lines never enter context.

---

## Memory: A Wiki-Graph in Flat Files

**The problem:** Each session starts from scratch. The agent does not know your servers, your project decisions, your past mistakes.

**The mechanism:** 78 markdown files with YAML frontmatter, linked by `[[wiki-links]]`. No database. No vector store. Just files that git can version.

```yaml
# Example: reference_gpu_servers.md
---
name: GPU training servers
description: Connection details for cloud GPU instances
type: reference
created: 2026-03-15
---

GPU servers for training and inference.
- gpu-train-01: training, 8x H200
- gpu-infer-01: inference, 4x H200

## Related
- [[docker_production_image]] - container running on these servers
- [[project_lora_training]] - training happens here
```

**How loading works:**

```
MEMORY.md (index file)
  |
  +-- "Always Load" section (27 files)
  |     user_profile, server configs, active rules, feedback
  |
  +-- "On Demand" section (51 files)
        projects, tools, methodology - loaded when topic is relevant
```

The agent reads `MEMORY.md` at session start. The "Always Load" entries are read immediately. The "On Demand" entries are read only when the agent encounters a related topic.

**The graph:** 178 cross-links between 78 files. Hub node: server infrastructure (10 connections). Average connectivity: 2.3 links per file. 81% of files are connected to at least one other file.

**Why not a vector database?** Three reasons:
1. Files are greppable - you can search with `grep`, not just semantic similarity
2. Files are in git - full version history, diffs, blame
3. Files are readable by any agent - no SDK, no setup, no embedding model

---

## Handoffs: Session-to-Session State Transfer

**The problem:** You close a chat. Open a new one. The new chat has no idea what you just spent two hours working on.

**The mechanism:** When a session ends (or the user says "prepare handoff"), the agent writes a structured summary to `.claude/handoffs/`.

```
.claude/handoffs/
  2026-04-09_14-32_373d1618.md   # session 1
  2026-04-09_15-01_b858f500.md   # session 2
  2026-04-09_16-47_ab154a15.md   # session 3
  INDEX.md                        # append-only index
```

**What a handoff contains:**

```markdown
# Session Handoff - 2026-04-09 14:32

## Goal
Fix drift validator false positives on template paths

## Done
- Updated validate_config.py: skip patterns for {{placeholder}} paths
- Added multi-strategy resolution: absolute -> relative -> cwd -> workspace

## Did NOT work (and why)
- Tried regex-only filtering: too many false negatives on real paths
- Path.exists() alone: fails on paths relative to other files

## Current state
- Working: validator catches real drift, skips templates
- Broken: nothing
- Blocked: nothing

## Next step
Run validator against 3 other projects to confirm false positive rate
```

**The critical section is "Did NOT work."** Without it, the next session will repeat the same dead ends. This is the highest-value section of any handoff - it prevents the most expensive kind of wasted work.

**Why not a single file?** Multiple Claude Code sessions can run in parallel on the same project. A single `HANDOFF.md` means the last writer wins - all other sessions' context is lost. The multi-file format with unique filenames (timestamp + session ID) is collision-free.

**Compression ratio:** A 2-hour session produces ~100K tokens of conversation. The handoff is ~1,500 tokens. That is 67x compression with higher signal density.

---

## Hooks: Code That Runs When Rules Would Be Forgotten

**The problem:** A rule in the prompt says "validate file references before starting work." After 20 minutes and 50 tool calls, the agent has forgotten this rule. Context pressure pushes it out.

**The insight:** Rules are prompts for a non-deterministic mechanism. Hooks are code.

**The mechanism:** Claude Code hooks are Python scripts triggered by events:

| Event | When It Fires | Example |
|---|---|---|
| `SessionStart` | New session opens | Validate config references |
| `PreToolUse` | Before any tool call | Block `rm -rf /`, catch secrets |
| `Stop` | Session about to close | Remind to write handoff |

**Real example - the drift validator hook:**

```python
# hooks/session-drift-validator.py (simplified)
# Event: SessionStart

import re, os, sys

def find_file_references(text):
    """Extract paths that look like real file references."""
    patterns = [
        r'(?:/[\w.-]+){2,}',           # /absolute/paths
        r'~/[\w./-]+',                  # ~/home paths
        r'[\w.-]+/[\w.-]+/[\w.-]+',     # multi-segment relative
    ]
    refs = set()
    for p in patterns:
        refs.update(re.findall(p, text))
    return refs

def validate(config_path):
    text = open(config_path).read()
    refs = find_file_references(text)
    missing = [r for r in refs if not os.path.exists(r)]
    if missing:
        print(f"[drift] {len(missing)} broken references:")
        for m in missing:
            print(f"  - {m}")

# Runs automatically at every session start
validate("CLAUDE.md")
for rule in glob(".claude/rules/*.md"):
    validate(rule)
```

**What happens when the hook fires:**
1. Agent starts a new session
2. Claude Code runs `session-drift-validator.py` before the agent sees any user input
3. If broken references are found, the output appears in the agent's context
4. Agent knows about drift *before* it acts on stale information

**The hierarchy:**
- **Hook** = shell process. Runs every time, no exceptions. Cannot be "creatively interpreted."
- **Rule** = text in a prompt. Works when the model remembers and chooses to follow it.
- **Hope** = nothing. The default state of most CLAUDE.md files.

If something must happen with certainty, it must be a hook.

**Real example - destructive command guard:**

```python
# hooks/destructive-command-guard.py
# Event: PreToolUse (Bash)

BLOCKED = [
    r'rm\s+-rf\s+/',
    r'git\s+push\s+--force',
    r'DROP\s+TABLE',
    r'git\s+reset\s+--hard',
]

def check(command):
    for pattern in BLOCKED:
        if re.search(pattern, command, re.IGNORECASE):
            return {"decision": "block",
                    "reason": f"Blocked: matches '{pattern}'"}
    return {"decision": "allow"}
```

This hook intercepts every Bash command *before execution*. The agent never gets a chance to "decide" whether the rule applies.

---

## KV-Cache: Why Prompt Structure Matters More Than Prompt Content

**The problem:** Claude API charges ~$15/M for fresh input tokens but ~$1.50/M for cached tokens. A 10x price difference. In a tool-heavy session with 1000+ turns, this is the difference between $100 and $1,000.

**The mechanism:** Claude's KV-cache stores computed attention states for token sequences. If a subsequent request starts with the same token prefix, those computations are reused.

**What kills the cache:**

```
BAD: Every request starts differently
  Turn 1: "Current time: 14:32:05. You are Claude..."
  Turn 2: "Current time: 14:32:47. You are Claude..."
  -> Cache miss on every turn (timestamp changed the prefix)

GOOD: Stable prefix
  Turn 1: "You are Claude... [stable rules] ... Current time: 14:32:05"
  Turn 2: "You are Claude... [stable rules] ... Current time: 14:32:47"
  -> Cache hit on everything before the timestamp
```

**Four rules for cache-friendly context:**

1. **Stable prefixes.** CLAUDE.md, rules, tool definitions - put them first. Timestamps, session-specific data - at the end.
2. **Define all tools once.** Adding or removing tools between turns rewrites the prefix. Define all tools upfront, mask unavailable ones.
3. **Results go to files, not context.** A 10,000-token tool output in context bloats every subsequent turn. Write to a file, put a pointer in context.
4. **Keep errors in context.** Failed attempts cost ~5% extra tokens but save ~40% retry cycles. The model learns from its own mistakes within a session.

**Our measurement:**

```
96.9% KV-cache hit rate across 83 sessions (7 days)
$10,929 actual cost
$78,160 cost without caching
$67,231 saved (86%)
```

Script: [`scripts/kvcache_stats.py`](scripts/kvcache_stats.py)

---

## Context Fill: Does Quality Degrade at 40%?

A common claim: "40%+ context fill leads to quality degradation." We measured this.

**Setup:** 169 sessions, 45,501 turns, 1M context window, 14-day window.

**Results:**

| Fill Level | Turns | Avg Output | Tool Use% | End Turn% |
|---|---|---|---|---|
| 0-20% | 23,373 | 246 | 89.0% | 11.0% |
| 20-40% | 14,745 | 246 | 87.0% | 13.0% |
| 40-60% | 5,926 | 284 | 86.1% | 13.9% |
| 60-80% | 1,457 | 305 | 89.1% | 10.9% |

**Interpretation:**
- Output length *increases* at higher fill levels (longer sessions = more complex tasks)
- Tool use stays stable (86-89%) across all fill levels
- End turn% shows no clear upward trend
- No evidence of degradation up to 72% fill on 1M context

**What the research says:**

- **"Lost in the Middle"** ([Liu et al., 2023](https://arxiv.org/abs/2307.03172)): 30%+ accuracy drop when relevant info is in positions 5-15 of 20 documents. This is a *positional* effect (middle suffers most), not a fill-level effect.
- **"Context Rot"** ([Chroma Research, 2025](https://research.trychroma.com/context-rot)): Tested 18 frontier models. A 200K-window model degrades measurably at ~50K tokens (25% fill). Models become "unreliable around 130K" (~65% fill). No clean "40% threshold" - degradation is gradual and model-specific.
- **Manus blog** ([manus.im](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)): Focuses on cache hit rate as cost metric, not quality threshold. No "40%" number.

**Our caveats:**
- This is Claude Opus 4.6 with 1M context. On a 200K model, 40% = 80K tokens - closer to where Chroma saw degradation.
- Our proxy metrics (output length, tool use ratio) are imperfect. A model could write longer but worse responses.
- Sessions that hit 60%+ fill are rare (19 of 169), so upper buckets have less statistical power.
- Context Rot research found degradation is task-dependent: simple retrieval holds up better than complex reasoning.

**Verdict:** The "40% = degradation" claim is an oversimplification. Degradation is real but gradual, positional (middle suffers most), and highly task-dependent. On 1M context with Opus 4.6, our proxy metrics show no degradation up to 72% fill. On smaller windows, watch for quality changes earlier.

Script: [`scripts/context_degradation.py`](scripts/context_degradation.py)

---

## Chronicles: Strategic History for Long-Running Projects

**The problem:** After 20 handoffs over 3 weeks, you know what to do *next* but not *why the project is in its current state*.

**The mechanism:** One markdown file per project in `.claude/chronicles/`. Each entry is 3-7 lines of strategic digest - not a handoff copy.

```markdown
# Chronicle: color-checker

**Status:** ACTIVE
**Started:** 2026-03-25

## Timeline

### 2026-03-25 - Started with LUT-based approach
Tried 3D LUT interpolation for color transfer between photos.
- Decision: LUT approach can not handle non-linear color relationships
- Pivot: switching to neural approach (lightweight CNN)

### 2026-04-02 - CNN training reached target
Trained 127K-param CNN, median deltaE 1.99 (target was <2.5).
- Decision: BK-SDM-Tiny for diffusion, separate CNN for fast inference
- Dead end: ViT-based approach too heavy for 2GB VRAM constraint

### 2026-04-11 - Optimal Transport baseline
Added OT-based method as a fast baseline (no training needed).
- Finding: OT works well for global correction, CNN better for local
- Next: hybrid approach - OT for global, CNN for local refinement
```

**How it connects to handoffs:**
- Handoff = "what's next" (tactical, session-scoped, 1-2 days)
- Chronicle = "how we got here" (strategic, project-scoped, weeks/months)
- When writing a handoff for a long-running project, also append a condensed entry to the chronicle

---

## Skills: Knowledge Bundles with Trigger Descriptions

**The problem:** The agent has access to general knowledge but not domain expertise. It does not know your specific deployment quirks, your model training recipes, your code review standards.

**The mechanism:** Each skill is a markdown file in `skills/<category>/<name>/SKILL.md` with an optional `references/` folder for supporting material.

**The key insight:** The skill description is a **trigger for the model**, not documentation for humans.

```
BAD:  "Helps with servers."
GOOD: "Use when: ComfyUI hangs, GPU health check needed,
       SSH tunnel not connecting, VRAM out of memory."
```

The model reads all skill descriptions and decides which ones to load based on the current task. A vague description means the skill never gets activated. A specific one with trigger phrases means the model loads it exactly when needed.

**Structure of a good skill:**

```
skills/ai-ml/flux2-lora-training/
  SKILL.md           # Core knowledge (<5000 words)
    ## When to Use   # Trigger phrases
    ## The Process   # Step-by-step
    ## Gotchas       # Real failures (mandatory)
    ## Troubleshooting  # Symptom -> cause -> fix
  references/
    dataset-prep.md  # Detailed reference material
    config-guide.md  # Loaded only when needed
  scripts/
    validate.py      # Deterministic checks
```

**DBS Framework for creating skills from research:**
- **Direction** (-> SKILL.md): decision logic, step-by-step processes, error handling
- **Blueprints** (-> references/): templates, taxonomies, static reference data
- **Solutions** (-> scripts/): deterministic code that should not go through the LLM

---

## Supply Chain Defense: One Line That Blocked a Nation-State Attack

**The mechanism:** One configuration line:

```ini
# ~/.npmrc
min-release-age=7
```

Packages published less than 7 days ago are not installed. Period.

**Why this works:** Most malicious packages are detected within 1-3 days. The 7-day delay lets the security community catch them before they reach your machine.

**Real incident:** On March 31, 2026, DPRK-linked group Sapphire Sleet compromised the official `axios` npm package (~100M weekly downloads). They published versions 1.14.1 and 0.30.4 with a backdoor. The exposure window was 3 hours (00:21-03:29 UTC).

`min-release-age=7` would have blocked both versions completely. The attack was detected within hours, but anyone who installed during that 3-hour window was compromised.

**For Python (uv):**

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

**Cost:** Occasionally you wait a week for a brand-new package. **Benefit:** You are immune to the most common class of supply chain attacks.

---

## Multi-Session Coordination: When Parallel Chats Share a Workspace

**The problem:** You open two Claude Code chats in the same project. Chat 1 starts training a model on GPU 2. Chat 2, not knowing, starts its own training on GPU 2. One crashes with an out-of-memory error. Or worse: both save their handoff to `.claude/HANDOFF.md` and the later one silently wipes the earlier one.

**The mechanism:** Two different kinds of shared state need two different mechanisms, and mixing them loses data.

**Type 1 - Append-only (handoffs, logs, findings):** each session writes its own file with a unique name. No session ever reads-then-writes another session's file. Conflict-free by construction.
```
.claude/handoffs/
  2026-04-09_14-32_373d1618.md    # chat 1
  2026-04-09_15-01_b858f500.md    # chat 2
  INDEX.md                         # append-only log of who wrote what
```

**Type 2 - Mutable (GPU/port/container ownership):** exactly one session can hold the resource. Others must see "taken" and back off. Uses a lock file per resource with a heartbeat timestamp.
```
.claude/locks/
  gpu_host-a_3.lock    # session_id, task, started, heartbeat
```

**Why not one shared table for both:** two sessions editing one file race on every write. Anthropic's own `.claude.json` hit this exact bug - 8+ reports of corrupted state from concurrent writes, hotfixed in v2.1.61. Per-resource files keep the conflict window tiny.

**Take protocol for a lock:**
1. Check if the lock file exists and heartbeat is fresh (< N hours ago)
2. If stale, verify the process is actually dead before reclaiming (nvidia-smi, ps, lsof)
3. Write the lock file with your session_id and started timestamp
4. Update heartbeat every 30-60 min while working
5. On release: `rm` the file and verify it's gone

**When this matters:** only if you run multiple Claude Code chats simultaneously on the same project. Most users work one chat at a time - they need nothing beyond a single `.claude/HANDOFF.md`. The multi-session mode is opt-in, documented in the [handoff rule](rules/session-handoff.md) and the [principle](principles/18-multi-session-coordination.md).

**Ecosystem context:** isolation solutions (git worktrees, sandboxes, Anthropic Agent Teams) are well-covered. Shared-state coordination across interactive chats is a gap - [Issue #19364](https://github.com/anthropics/claude-code/issues/19364) proposed a `session.lock` primitive but it is not implemented. The principle fills this gap using 40-year-old distributed-systems patterns (heartbeats, canonical resource names, append-only logs).

---

## All Scripts in This Repo

| Script | What It Measures | Run |
|---|---|---|
| [`kvcache_stats.py`](scripts/kvcache_stats.py) | KV-cache hit rate, cost savings | `python scripts/kvcache_stats.py --days 7` |
| [`context_degradation.py`](scripts/context_degradation.py) | Context fill vs quality metrics | `python scripts/context_degradation.py --days 14` |
| [`validate_config.py`](scripts/validate_config.py) | Broken file references in configs | `python scripts/validate_config.py` |
| [`cross_reference_check.py`](scripts/cross_reference_check.py) | Internal consistency: links, numbering, anti-pattern leaks | `python scripts/cross_reference_check.py` |

---

## Further Reading

- [Principles README](principles/README.md) - decision matrix: pick the right principle for your situation
- [Alternatives](alternatives/) - 2-5 approaches compared for each problem
- [Templates](templates/) - starter CLAUDE.md files for different project types
