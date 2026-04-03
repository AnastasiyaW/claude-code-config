# Claude Code Configuration System

A practical configuration kit for Claude Code agents. Drop it into your project and your agent immediately gets battle-tested architectural principles, security hardening, and decision frameworks - instead of figuring them out from scratch every session.

This is not a collection of tips. It is a **system** that teaches your agent *how to work* - when to use one agent vs many, how to verify its own output, how to manage context across long sessions, how to not get poisoned by malicious packages.

---

## What This Gives You

**10 Architectural Principles** - each one prevents a specific failure mode observed in real agent workflows:

- **Self-evaluation bias?** Separate Generator and Evaluator agents ([Harness Design](principles/01-harness-design.md))
- **Agent claims "done" but it's broken?** Require durable proof artifacts ([Proof Loop](principles/02-proof-loop.md))
- **Need to improve a prompt/skill/config?** Automated Read-Change-Test loop ([Autoresearch](principles/03-autoresearch.md))
- **LLM skips steps in complex workflows?** Shell scripts for mechanical tasks, one step at a time ([Deterministic Orchestration](principles/04-deterministic-orchestration.md))
- **Wrong debugging conclusions?** Structured Premises-Trace-Conclusions format ([Structured Reasoning](principles/05-structured-reasoning.md))
- **Task too big for one agent?** Coordinator + specialized sub-agents ([Multi-Agent Decomposition](principles/06-multi-agent-decomposition.md))
- **Context degrades in long sessions?** Treat CLAUDE.md as runtime config, not docs ([Codified Context](principles/07-codified-context.md))
- **Supply chain attack?** Two config lines block packages younger than 7 days ([Supply Chain Defense](principles/09-supply-chain-defense.md))
- **Prompt injection via repo/MCP/web?** Six-layer defense with real CVEs ([Agent Security](principles/10-agent-security.md))

**Your agent picks the approach that fits.** The [alternatives/](alternatives/) directory compares 2-5 approaches for each problem, with pros, cons, and "when to choose" guidance:

| Problem | Approaches Compared |
|---|---|
| [Multi-step orchestration](alternatives/orchestration.md) | Harness Design, Proof Loop, Deterministic Orchestration, Prompt-only |
| [Code review](alternatives/code-review.md) | Sequential checklist, Parallel competency, Cross-model, LLM + static |
| [Iterative optimization](alternatives/optimization.md) | Autoresearch, HyperAgent, Manual, Eval-driven |
| [Context in long sessions](alternatives/context-management.md) | JIT Loading, Full Context Upfront, Compaction, Fresh Sessions |
| [Session transitions](alternatives/session-handoff.md) | Manual HANDOFF.md, Auto hooks, Session Journal, ContextHarness, Memory |

---

## Quick Start

```bash
# Clone
git clone https://github.com/AnastasiyaW/claude-code-skills.git

# Option 1: Copy the full CLAUDE.md as your global config
cp claude-code-skills/CLAUDE.md ~/.claude/CLAUDE.md

# Option 2: Copy specific principles you need
# (each principle is a standalone .md file)

# Option 3: Copy skills you need
cp -r claude-code-skills/skills/development/deep-review ~/.claude/skills/
```

The CLAUDE.md encodes all 10 principles. Principles are standalone files you can read, adapt, or cherry-pick. Skills are `.claude/skills/<name>/SKILL.md` files that Claude Code picks up automatically.

---

## Principles by Maturity Level

Start with L1 for any project. Add L2 when tasks repeat and optimization matters. L3 only when solo agent is not enough.

| Level | Focus | Principles |
|---|---|---|
| **L1: Foundational** | Single agent, planning, tool use | Deterministic Orchestration, Structured Reasoning, Skills Best Practices |
| **L2: Self-Evolving** | Feedback loops, memory, optimization | Autoresearch, Codified Context, Proof Loop |
| **L3: Collective** | Multi-agent coordination | Harness Design, Multi-Agent Decomposition |
| **Cross-cutting** | Security | Supply Chain Defense, Agent Security |

Based on three-level agentic reasoning taxonomy (arxiv 2601.12538, 2504.19678).

---

## Security Hardening

Two principles specifically address agent security:

**Supply Chain Defense** - most poisoned npm/PyPI packages are caught within 1-3 days. Two config lines create a 7-day buffer:
```ini
# ~/.npmrc
min-release-age=7
```
```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

**Agent Security** - covers 7 real attack categories with documented CVEs: in-code prompt injection, repo metadata poisoning, package metadata, MCP tool poisoning, web content injection, memory poisoning, sandbox escape. Includes a six-layer defense architecture.

---

## Skills Catalog

Skills are practical tools for specific domains. They are secondary to the principles - think of them as reference implementations.

| Category | Skill | What It Does |
|---|---|---|
| Development | `deep-review` | 8 parallel specialist reviewers (security, perf, arch, DB, concurrency, errors, frontend, tests) |
| AI/ML | `diffusion-engineering` | UNet, DiT, Flow Matching, Flux architectures, LoRA, schedulers, memory optimization |
| AI/ML | `flux2-lora-training` | LoRA training for FLUX.2 Klein 9B and Qwen Image Edit |
| AI/ML | `flux2-klein-prompting` | Prompt engineering for FLUX.2 Klein |
| AI/ML | `vlm-segmentation` | VLM + segmentation: SAM2/3, Florence-2, YOLO-World |
| AI/ML | `forensic-prompt-compiler` | Reverse-engineer images into reproducible prompts |
| Frontend | `frontend-design` | Production-grade interfaces, not template defaults |
| Architecture | `harness-design` | Multi-agent patterns: Generator-Evaluator, Sprint Contracts |
| iOS | `ios-development` | Swift, SwiftUI, UIKit, MVVM/TCA, Metal/GPU |
| Writing | `humanize-english` | Transform AI text into natural prose |

---

## Complementary Tools

These work well alongside the principles:

- **[gstack](https://github.com/nichochar/gstack)** - dev workflow skills: /review, /qa, /ship, /investigate, /design-review
- **[hookify](https://github.com/AstroMined/hookify)** - git hooks generator for Claude Code
- **[Semgrep](https://semgrep.dev/)** - static analysis, pairs with deep-review
- **[task-orchestrator](https://github.com/jpicklyk/task-orchestrator)** - MCP task orchestration with dependency ordering

---

## This Repo Is Updated Regularly

Principles are updated with new research findings, real-world incidents, and community patterns. Security sections track actual CVEs and attack chains. See [UPDATES.md](UPDATES.md) for the full changelog.

---

## Contributing

1. Fork the repo
2. Add/improve a skill (`skills/<category>/<name>/SKILL.md`) or principle (`principles/`)
3. Skill descriptions = triggers for the model, not human summaries. Include `## Gotchas` from real failures
4. For principles or alternatives: open an issue first

---

## License

MIT
