# Claude Code Skills & Principles

Curated skills, architectural principles, and decision frameworks for Claude Code.

A collection of battle-tested `.claude/skills/` and a universal `CLAUDE.md` distilled from real production work -- multi-agent orchestration, AI/ML pipelines, code review, frontend craft, and more.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/AnastasiyaW/claude-code-skills.git

# Copy skills you need into your project
cp -r claude-code-skills/skills/deep-review ~/.claude/skills/

# Or copy the full CLAUDE.md as your global config
cp claude-code-skills/CLAUDE.md ~/.claude/CLAUDE.md
```

Skills live in `~/.claude/skills/<skill-name>/SKILL.md`. Claude Code picks them up automatically.

---

## Skills Catalog

| Category | Skill | Description |
|---|---|---|
| Development | `deep-review` | Parallel competency-based code review with 8 specialist reviewers: security, performance, architecture, database, concurrency, error-handling, frontend, testing |
| AI/ML | `diffusion-engineering` | Diffusion model engineering -- UNet, DiT, Flow Matching, Flux architectures, LoRA, schedulers, memory optimization |
| AI/ML | `flux2-lora-training` | LoRA training pipelines for FLUX.2 Klein 9B and Qwen Image Edit models |
| AI/ML | `flux2-klein-prompting` | Prompt engineering techniques for FLUX.2 Klein image generation |
| AI/ML | `vlm-segmentation` | Vision-Language Models + segmentation -- SAM2/3, Florence-2, YOLO-World, GPU deployment |
| AI/ML | `forensic-prompt-compiler` | Reverse-engineer existing images into reproducible generation prompts |
| Frontend | `frontend-design` | Production-grade web interfaces with high design quality, not template defaults |
| Architecture | `harness-design` | Multi-agent harness patterns -- Generator-Evaluator, Sprint Contracts, context management |
| iOS | `ios-development` | iOS application development -- Swift, SwiftUI, UIKit, MVVM/TCA, Metal/GPU compute |
| Writing | `humanize-english` | Transform AI-generated text into natural-sounding prose that passes detection |

---

## Principles Overview

The `CLAUDE.md` file encodes 10 architectural principles for AI-assisted development. Each one addresses a specific failure mode observed in real agent workflows.

| # | Principle | Core Idea |
|---|---|---|
| 1 | **Harness Design** | Generator and Evaluator must be separate agents. Models praise their own work (self-evaluation bias). Source: Anthropic Engineering. |
| 2 | **Proof Loop** | `spec freeze -> build -> evidence -> fresh verify -> fix -> loop`. Agents cannot self-certify completion -- durable artifacts required. Source: OpenClaw-RL. |
| 3 | **Autoresearch** | Read -> Change ONE thing -> Test mechanically -> Keep/Discard -> Repeat. Any measurable output can be improved automatically. Source: Karpathy. |
| 4 | **Deterministic Orchestration** | Shell Bypass (mechanical tasks skip the LLM), Relay Pattern (one task at a time), Findings Taxonomy (structured knowledge capture). |
| 5 | **Structured Reasoning** | Replace free-form chain-of-thought with: Premises -> Execution Trace -> Conclusions -> Rejected Paths. Eliminates planning hallucinations. |
| 6 | **Multi-Agent Decomposition** | Coordinator distributes tasks, specialized sub-agents execute. Coordination via shared artifacts in repo, not conversation history. |
| 7 | **Codified Context** | Context is infrastructure, not documentation. CLAUDE.md = runtime config. Memory = persistent state. JIT loading over full-context dumps. |
| 8 | **Skills Best Practices** | Skill descriptions are model triggers, not human docs. Mandatory Gotchas section. Critical validations belong in scripts, not words. |
| 9 | **Supply Chain Defense** | Gate fresh packages with `min-release-age=7` (npm) and `exclude-newer = "7 days"` (uv). Most poisoned packages are caught within days. |
| 10 | **Agent Security** | Defense against prompt injection and adversarial attacks. 7 attack categories (in-code injection, repo metadata, MCP poisoning, etc.) with real CVEs. Six-layer defense architecture. |

### Principle Map by Reasoning Level

Based on the three-level agentic reasoning taxonomy (arxiv 2601.12538, 2504.19678):

| Level | Focus | Principles |
|---|---|---|
| **L1: Foundational** | Single agent, planning, tool use | 04 Deterministic Orchestration, 05 Structured Reasoning, 08 Skills |
| **L2: Self-Evolving** | Self-improvement via feedback + memory | 03 Autoresearch, 07 Codified Context, 02 Proof Loop |
| **L3: Collective** | Multi-agent coordination, knowledge sharing | 01 Harness Design, 06 Multi-Agent Decomposition |
| **Cross-cutting** | Security and supply chain | 09 Supply Chain Defense, 10 Agent Security |

Start with L1 for any project. Add L2 when tasks repeat and optimization matters. Use L3 only when a task exceeds reliable solo-agent performance.

---

## Alternative Approaches

The `alternatives/` directory contains comparison documents for key architectural decisions:

- **Orchestration** -- Memento vs Roo Code vs manual skill chains
- **Code Review** -- deep-review skill vs CodeRabbit vs Semgrep vs manual PR review
- **Optimization** -- Autoresearch vs HyperAgent vs manual iteration
- **Context Management** -- Codified Context vs vanilla CLAUDE.md vs .cursorrules

Each document follows the same structure: what the approach does, when to pick it, known tradeoffs.

---

## Recommended External Tools

These complement the skills and principles in this repo:

- **[gstack](https://github.com/nichochar/gstack)** -- Dev workflow skills for Claude Code: /review, /qa, /ship, /investigate, /design-review, /retro, and more.
- **[hookify](https://github.com/AstroMined/hookify)** -- Git hooks generator for Claude Code. Pre-commit validation, lint, format.
- **[Semgrep](https://semgrep.dev/)** -- Static analysis rules. Pairs well with `deep-review` for automated security/quality gates.
- **[task-orchestrator](https://github.com/jpicklyk/task-orchestrator)** -- MCP-based task orchestration with dependency ordering and gate-checked transitions.

---

## Contributing

1. Fork the repo
2. Add or improve a skill in `skills/<category>/<skill-name>/SKILL.md`
3. Follow the Skills Best Practices from `CLAUDE.md`:
   - Description = trigger for the model, not human-readable summary
   - Include `## Gotchas` with real failure cases
   - Include `## Troubleshooting` with symptom -> cause -> fix
   - Keep SKILL.md under 5000 words; details go in `references/`
4. Open a PR with a clear description of what the skill does and when to use it

For principles or alternatives, open an issue first to discuss the addition.

---

## Updates

See [UPDATES.md](UPDATES.md) for the changelog.

---

## License

MIT
