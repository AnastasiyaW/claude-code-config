# Updates

Changelog for claude-code-skills. Newest first.

---

## 2026-04-09 (night)

### Updated: Principle 06 - DeerFlow 2.0 three-layer isolation deep dive

Expanded "Pattern B: Sandbox Isolation (DeerFlow 2.0)" from a brief overview to a full architectural walkthrough. Research source: deep dive into [bytedance/deer-flow](https://github.com/bytedance/deer-flow) README, architecture docs, and DeepWiki analysis.

New content:
- **Layer 1: Virtual Path Translation** (`ThreadDataMiddleware`) - per-thread directories with transparent `/mnt/user-data/*` mapping
- **Layer 2: Docker Container Isolation** (AioSandboxProvider / Kubernetes) - three provisioner modes, 5-10s cold start cost, seccomp/cgroup transparency gap flagged
- **Layer 3: LangGraph State Channel Isolation** - separate `ThreadState` per sub-agent, fan-out/fan-in pattern, unidirectional communication
- **Data flow walkthrough:** `task()` tool -> `SubagentExecutor` -> 3-worker pool -> SSE result, `MAX_CONCURRENT_SUBAGENTS=3`, 15-min timeout
- **Memory weakness** documented: global `memory.json` contamination reintroduces leakage that the isolation layers prevent. Mitigation: per-session memory sharding or append-only with provenance

### Added: Principle 04 - Tool Registry Pattern (Claw Code)

New section citing Claw Code's `rust/crates/tools/` as a reference implementation of declarative tool definitions. `ToolSpec { name, description, input_schema }` struct separates tool definition (data) from dispatch (runtime) from execution (side effect). Three benefits: tiny audit surface, isolated tool tests, new tools without prompt changes. Warning against shipping 200 tools "just in case" (each degrades LLM decision quality) - Claw Code ships 19 as the baseline.

### Added: Principle 10 - Hierarchical Permission Overrides (Claw Code)

New subsection under "Layer 3: Permission Boundaries" showing the Claw Code `PermissionPolicy { default_mode, per_tool_overrides }` structure with a `PermissionMode { Allow, Deny, Prompt }` enum. Cleaner than flat allow/deny lists for single-user setups. Explicit acknowledgment of what it does NOT solve: no RBAC, no resource quotas, no provenance - those require additional mechanisms. Includes a minimal TOML config example for adoption.

### Added: scripts/kvcache_stats.py

Working Python script to measure KV-cache hit rate across Claude Code sessions. Parses `~/.claude/projects/*/*.jsonl` session logs, aggregates `cache_creation_input_tokens` / `cache_read_input_tokens` / `input_tokens` / `output_tokens` from assistant messages, computes per-session and overall hit rate, estimates cost in USD using Claude Opus 4.6 pricing, and shows savings vs a no-cache baseline. Includes percentile distribution, top-N by tokens, worst hit rate detection. Supports filtering by project substring and time window.

Real-world results on a single workspace: 96.9% overall hit rate across 83 sessions in 7 days, $10,929 actual cost vs $78,160 without caching ($67,231 / 86% savings). Median per-session 89.7%. Validates Manus's claim that KV-cache is the dominant production metric.

Run: `python scripts/kvcache_stats.py --days 7 --project <substring>`

---

## 2026-04-09 (evening)

### Updated: Principle 10 - OWASP ASI01-ASI10 + fresh CVEs + 30-minute audit

Major update to the agent security principle based on OWASP Gen AI Security Project's [Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) (published December 2025, 100+ industry experts).

**New sections:**

1. **Full OWASP ASI01-ASI10 mapping** - explicit table showing which of our Attack Taxonomy items cover which OWASP risks, and four new sub-sections for the items our taxonomy did not previously address: ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent Trust Erosion, ASI10 Rogue Agent Behavior.

2. **Minimum Viable Security Audit (5 steps, 30 minutes)** - concrete shell commands for version check, environment hardening, MCP/tool inventory, hook audit, and provenance check. Catches ~70% of realistic attack vectors without architectural changes.

3. **Using RedCodeAgent defensively** - how to use the ICLR 2026 red-team agent ([arxiv 2510.02609](https://arxiv.org/html/2510.02609)) against your own setup. RedCodeAgent memory module discovered 82 unique vulnerabilities on OpenCodeInterpreter where baseline red-teaming found zero.

**Timeline additions (2026 real CVEs):**

- **CVE-2025-59944** (Cursor IDE, CVSS 8.0): case-sensitivity bypass in MCP config (`.cursor/mcp.json` vs `.Cursor/mcp.json`) leading to RCE via prompt injection. Fixed in Cursor v1.7.
- **Claude Code source leak (March 31, 2026):** 59.8 MB source map accidentally shipped in npm v2.1.88, exposed internal architecture to attackers.
- **CVE-2026-35020 / 35021 / 35022** (Claude Code CLI): three command injection CVEs with a shared root cause (unsanitized shell interpolation in TERMINAL env var lookup, editor path invocation, and auth helper). Discovered by Phoenix Security hours after the source leak, validated unpatched on v2.1.91 (production) as of April 3, 2026. CVSS 7.2-8.4.

**Why this matters for Claude Code users:** anyone on a Claude Code version at or before v2.1.91 needs to watch for the security advisory and upgrade via the native installer (not npm) when the patch ships.

---

## 2026-04-09

### Added: AGENTS.md at repo root

Linux Foundation / Agentic AI Foundation standard file. 70 lines, under the 150-line best-practice limit from the GitHub analysis of 2500+ repositories. Hybrid with CLAUDE.md: AGENTS.md is the universal entry point for any agent (Codex, Cursor, Claude Code), CLAUDE.md remains the Claude Code-specific overlay. Future-proofs the repo for when Claude Code adds native AGENTS.md support (issue anthropics/claude-code#6235).

### Updated: Principle 01 - SEMAG trace-similarity escalation

Added a new section on execution trace similarity as a stagnation signal for Generator-Evaluator loops. Based on [arxiv 2603.15707](https://arxiv.org/abs/2603.15707). When consecutive attempts produce near-identical runtime traces (rho > 0.85), the loop has stalled and should escalate through three levels: single-shot -> trace-guided debugging -> multi-agent discussion-decision with weighted voting. Explicitly rejects SEMAG's full Automatic Model Selector as too task-specific without difficulty measurements.

### Updated: Principle 02 - Reliability metrics + OpenClaw paid note

Added a new section on reliability as a distinct dimension from accuracy, based on [arxiv 2602.16666](https://arxiv.org/html/2602.16666v1). Extends the single PASS/FAIL verdict with a four-dimensional tuple (consistency, robustness, predictability, safety). Minimum viable adoption: multi-run consistency + prompt paraphrase robustness. Also added a note at the top: OpenClaw is now a paid third-party tool as of April 4, 2026, but the arxiv paper and the pattern remain freely usable.

### Updated: Principle 06 - Coordination Patterns (Paperclip vs DeerFlow)

Added a new section comparing two production-tested coordination approaches: Paperclip's shared-workspace pattern (43K stars, file-based handoff, scales to 50+ trusted agents) vs DeerFlow 2.0's sandbox-isolation pattern (44K stars, per-agent Docker, 10-15 agents with strict blast-radius control). Includes a decision table and a hybrid pattern.

### Updated: Principle 03 - Autoresearch scope limitations

Added SICA v2 findings from [arxiv 2504.15228](https://arxiv.org/abs/2504.15228). Three failure modes: base model saturation, reasoning interruption, path dependency. Revised scope guidance and a "signal to stop" rule: three consecutive iterations without improvement means stop.

### Updated: alternatives/context-management.md - Manus KV-cache insights

Comprehensive section on KV-cache hit rate as THE production metric. Four rules for cache-friendly context: stable prefixes, mask tools instead of swapping, filesystem as extended context, preserve errors. Includes the todo.md recitation trick (exploiting recency bias). Cross-table showing how KV-cache interacts with each of the four context management approaches.

### Updated: Principle 09 - Sapphire Sleet attribution + native installer note

Added Microsoft's Sapphire Sleet attribution alongside Google's UNC1069 attribution (same DPRK actor, different vendor naming). Added explicit Claude Code recommendation: use the native installer instead of npm to eliminate transitive dependency attack vectors entirely.

---

## 2026-04-08 (night update)

### Updated: Principle 12 - Added Trap 7 (Loss Asymmetry on Bipolar Residuals)
- **Critical discovery from visual inspection**: L2 loss silently ignores half of bipolar residual distributions (e.g., Dodge&Burn where dodge spots are +5% but burn spots are -2%)
- Metrics (MAE, PSNR) looked fine because the missed side contributes less to mean error — but visual contrast enhancement revealed model was producing "zero" for darker corrections
- New **Trap 7** section: cause, diagnosis, fix (L1/Huber instead of L2)
- Updated "Which Loss" section: L2 is wrong for bipolar residuals, Huber is safe default, Active weighting helps on dense/complex scenes
- Added diagnostic step #8: compare enhanced prediction vs enhanced GT side-by-side, check both sides of distribution
- Updated quick-reference config: `loss_fn: huber` (was L2)
- Key lesson: **don't trust metrics alone for low-signal tasks - always visually inspect with contrast enhancement ×5-10**

---

## 2026-04-08 (evening)

### Added: Principle 12 - Low-Signal Residual Training
- `principles/12-low-signal-residual-training.md` - 6 traps + fixes for ML tasks where targets have small deviations from a constant baseline
- Covers: "predict zero" attractor, PSNR metric lies, JPEG target poisoning, tanh saturation, subject background pollution, warmup/EMA timing
- Source: 4 rounds of retouch training failure + 7-config parallel sweep
- Includes known-good config (U-Net + EffB4, amp=5, no tanh, Huber/L2, warmup+delayed EMA)
- General applicability: any residual prediction task (denoise, color correction, enhancement)

---

## 2026-04-08

### Added: 3 new alternatives from Telegram research digest
- `alternatives/memory-strategies.md` - verbatim vs extraction vs hybrid, MemPalace 4-layer model, temporal validity, when to use ChromaDB
- `alternatives/token-economy.md` - Caveman Prompting (75% token savings), where to apply/avoid, quantitative benchmarks
- `alternatives/multi-agent-patterns.md` - Generator-Evaluator, Coordinator+Specialists, CORAL heartbeat, Proof Loop, implementation in Claude Code

### Updated: English Text Humanization Skill
- `skills/writing/humanize-english/SKILL.md` - upgraded sources from SEO blogs to peer-reviewed research
- Added Liang et al. (arxiv 2406.07016) data: 10 marker words, excess ratios (delve 25.2x, showcasing 9.2x)
- Added structural anti-patterns section (AI shape, symmetry, tone traps)
- Added co-evolution note (word lists go stale, principles > specific words)
- Replaced "humanizer tool" sources with academic papers + research data repos

### Added: Russian Text Humanization Skill
- `skills/writing/humanize-russian/SKILL.md` - new skill for Russian-language text naturalization
- Russian-specific markers: "является", "не просто..., а...", deverbal nouns (отглагольные существительные)
- English calque detection (word order, syntax patterns)
- Conversational elements dosing (частицы, вводные, оценочные)
- Checklist + comparison table RU vs EN detection differences
- Sources: gramota.ru, Habr 918226, Sber GigaCheck, Russian Wikipedia

---

## 2026-04-07

### Added: Alternative - Workspace Organization
- `alternatives/workspace-organization.md` - система из 3 навигационных .md файлов
- WORKSPACE.md (карта), PROJECTS.md (реестр), session-handoff (правило)
- Research Hub с тематическими подпапками (_inbox, agentic, ml, infra, security, product)
- Потоки данных: raw research → research/{тема}/ → knowledge pipeline → проекты
- Связь с Karpathy LLM Wiki, MemPalace, CORAL patterns

---

## 2026-04-04

### Added: Principle 11 - Research Pipeline
- Save research results to `.research/incoming/` after every research session
- Prevents duplicate work across sessions
- Creates a knowledge pipeline: research -> incoming -> review -> knowledge base
- Connected to Codified Context, Session Handoff, Autoresearch principles

---

## 2026-04-08

### Added: Manual handoff trigger phrases + ready-to-copy rule file

Natural-language trigger phrases ("prepare handoff", "save context for new chat", etc.) for writing `.claude/HANDOFF.md` on demand. Essential for migrating existing sessions that predate any hook-based automation.

- New file: [rules/session-handoff.md](rules/session-handoff.md) - drop-in rule with trigger phrases, HANDOFF.md format, session-start behavior, and rule-vs-hook rationale
- New README section: "Session Handoff - Moving Between Chats" with the trigger phrases and usage explanation for humans
- Updated [alternatives/session-handoff.md](alternatives/session-handoff.md): trigger-phrase variant added to Approach A (Manual HANDOFF.md)

The rule complements hook-based automation: hook handles forgetful users, rule handles deliberate session closure.

### Added: Principle 11 - Documentation Integrity

Fundamental solution to documentation drift for AI agents: validate all file references at session start via a SessionStart hook, not rules.

**Core insight**: rules are instructions of hope - the agent follows them only if it remembers and chooses to. Hooks are shell processes that run unconditionally. For guaranteed behaviors (validation, handoff, cleanup), use hooks, not rules.

The principle ships with a working Python validator (`scripts/validate_config.py`) that:
- Distinguishes real references (absolute paths, multi-segment with `/`) from examples (bare filenames like `foo.py`)
- Uses multi-strategy path resolution (absolute -> relative to file -> cwd -> workspace roots)
- Keeps false positives low via skip patterns for template placeholders

Drop the script into `~/.claude/scripts/` and register a `SessionStart` hook - the agent sees drift warnings automatically on every session start.

See [principles/11-documentation-integrity.md](principles/11-documentation-integrity.md) and [scripts/validate_config.py](scripts/validate_config.py).

---

## 2026-04-03

### Rewritten: README.md

Repositioned from "skills collection" to "configuration system for Claude Code agents". Focus on: what problems each principle solves (not abstract descriptions), alternatives as key feature (agent picks the right approach), security hardening section, principles by maturity level (L1-L3). Skills described as secondary/reference implementations.

### Added: Session Handoff comparison (Alternative)

Five approaches to seamless session transitions compared: Manual HANDOFF.md, Stop Hook (auto), Session Journal (living log), ContextHarness (framework), Memory Only (baseline). Sources: claude-handoff plugin, ContextHarness, JD Hodges patterns, GitHub issue #11455 community patterns.

Key insight: structured handoff (500-2000 tokens) beats raw conversation dump (50-100K tokens) by ~50x compression with higher signal. "What did NOT work" is the most valuable section - prevents the next session from repeating dead ends.

See [alternatives/session-handoff.md](alternatives/session-handoff.md).

---

## 2026-04-02

### Added: Research evidence to Codified Context (Principle 07)

Two contradictory studies on context files (AGENTS.md/CLAUDE.md): one shows -28.6% task time, other shows -3% success rate. Resolution: auto-generated context hurts, human-written non-inferable knowledge helps. Added "The Rule" - only include what the agent cannot derive from reading the code. ETH Zurich data: LLM-generated context = +20% cost, +2-4 extra reasoning steps.

### Added: Principle Map by Reasoning Level to README

Three-level taxonomy (arxiv 2601.12538, 2504.19678) maps to our 10 principles: L1 Foundational (single agent), L2 Self-Evolving (feedback + memory), L3 Collective (multi-agent). Helps users pick which principles to adopt first.

### Updated: Structured Reasoning accuracy to 93% (Principle 05)

Paper v2 results on real-world agent-generated patches: 78% -> 93% accuracy.

---

## 2026-04-01

### Added: axios@1.14.1 case study to Supply Chain Defense (Principle 09)

Real-world supply chain attack on the official `axios` npm package (~100M weekly downloads), attributed to DPRK-nexus threat actor UNC1069 by Google Threat Intelligence. Maintainer account hijacked, RAT deployed via postinstall hook. Exposure window: ~3 hours. `min-release-age=7` would have completely blocked the attack. Full timeline, attack chain, defense matrix, and IOCs documented. Sources: Elastic Security Labs, Snyk, Wiz, Google Cloud Blog.

### Added: Revision Trajectories + problems.md schema to Proof Loop (Principle 02)

Based on Agent-R (arxiv 2501.11425): failed-then-fixed trajectories are more valuable than clean passes. Added structured Evaluator feedback format (cut point + reflection + direction) and a concrete `problems.md` schema with criterion ID, reproduction steps, expected vs actual, affected files, and smallest safe fix. Improves the fix -> verify again cycle.

### Fixed: README principle count (9 -> 10)

README.md listed "9 architectural principles" and was missing Principle 10 (Agent Security) from the principles table. Updated to reflect all 10 principles.

### Added: "Deletion = re-verification" rule to Anti-Fabrication

Added the pattern: after executing a delete command, always verify the object is actually gone. Commands can exit 0 without doing anything (permissions, locks, wrong path). Part of the Anti-Fabrication section in Deterministic Orchestration.

---

## 2026-03-31

### Added: Agent Security (Principle 10)

Comprehensive defense guide against prompt injection and adversarial attacks on AI coding agents. Covers 7 attack categories (in-code injection, repo metadata, package metadata, MCP tool poisoning, web content injection, memory poisoning, sandbox escape) with real CVEs and incidents. Six-layer defense architecture from content isolation to monitoring. See [principles/10-agent-security.md](principles/10-agent-security.md).

### Added: Supply Chain Defense (Principle 09)

Package age gating as defense against supply chain attacks. Two config lines that block packages published less than 7 days ago:

```ini
# ~/.npmrc
min-release-age=7
```

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

Most malicious packages are caught within 1-3 days. The 7-day delay eliminates the attack window with near-zero friction to your workflow. See [principles/09-supply-chain-defense.md](principles/09-supply-chain-defense.md) for full details including per-manager configs, CI considerations, and defense-in-depth layers.

### Fixed: 6 skills were ZIP archives, not readable on GitHub

`diffusion-engineering`, `vlm-segmentation`, `flux2-klein-prompting`, `forensic-prompt-compiler`, `ios-development`, `frontend-design` - all now properly extracted with SKILL.md + references/ as readable markdown.

### Updated: Memento references replaced

The `mderk/memento` repo appears to have been removed from GitHub. All references updated to point to active alternatives: [task-orchestrator](https://github.com/jpicklyk/task-orchestrator), [inngest/agent-kit](https://github.com/inngest/agent-kit). The deterministic orchestration principles remain valid and well-documented.

### Freshness check: all 10 concepts reviewed

| Concept | Status |
|---------|--------|
| Generator-Evaluator | Current - now a standard primitive |
| Proof Loop | Current - watch formal verification + LLM space |
| Autoresearch | Very current - 21K stars, ecosystem explosion |
| HyperAgents | Current - Meta released code |
| HACRL | Current - conceptual pattern is actionable |
| Structured Reasoning | Current - 78%->88% accuracy validated |
| Codified Context | Current - 1M window adjusts urgency, not principle |
| Memento | Repo gone - principles live in alternatives |
| Context Engineering | Current - update for 1M context realities |
| Multi-Agent Decomposition | Current - trend toward adaptive routing |

---

## 2026-03-30

### Initial release

8 architectural principles, 4 alternative comparison docs, 10 skills, CLAUDE.md template. Covers: harness design, proof loops, autoresearch, deterministic orchestration, structured reasoning, multi-agent decomposition, codified context, skills best practices.
