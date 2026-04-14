# Claude Code Configuration System

**Setup in 10 seconds:** paste this into your Claude Code chat and hit Enter:

```
https://github.com/AnastasiyaW/claude-code-config — look through everything here, pick what fits my project, and set it up
```

A practical configuration kit for Claude Code agents. Drop it into your project and your agent immediately gets battle-tested architectural principles, security hardening, and decision frameworks - instead of figuring them out from scratch every session.

This is not a collection of tips. It is a **system** that teaches your agent *how to work* - when to use one agent vs many, how to verify its own output, how to manage context across long sessions, how to not get poisoned by malicious packages.

---

## What This Gives You

**17 Architectural Principles** - each one prevents a specific failure mode observed in real agent workflows:

- **Self-evaluation bias?** Separate Generator and Evaluator agents ([Harness Design](principles/01-harness-design.md))
- **Agent claims "done" but it's broken?** Require durable proof artifacts ([Proof Loop](principles/02-proof-loop.md))
- **Need to improve a prompt/skill/config?** Automated Read-Change-Test loop ([Autoresearch](principles/03-autoresearch.md))
- **LLM skips steps in complex workflows?** Shell scripts for mechanical tasks, one step at a time ([Deterministic Orchestration](principles/04-deterministic-orchestration.md))
- **Wrong debugging conclusions?** Structured Premises-Trace-Conclusions format ([Structured Reasoning](principles/05-structured-reasoning.md))
- **Task too big for one agent?** Coordinator + specialized sub-agents ([Multi-Agent Decomposition](principles/06-multi-agent-decomposition.md))
- **Context degrades in long sessions?** Treat CLAUDE.md as runtime config, not docs ([Codified Context](principles/07-codified-context.md))
- **Supply chain attack?** Two config lines block packages younger than 7 days ([Supply Chain Defense](principles/09-supply-chain-defense.md))
- **Prompt injection via repo/MCP/web?** Six-layer defense with real CVEs ([Agent Security](principles/10-agent-security.md))
- **Docs reference files that no longer exist?** SessionStart hook validates every reference ([Documentation Integrity](principles/11-documentation-integrity.md)) - ships with a working validator script
- **Multi-agent infrastructure overhead?** Separate brain from hands with lazy provisioning ([Managed Agents](principles/14-managed-agents.md))
- **Agent cuts corners on critical rules?** Absolute prohibitions with incident history ([Red Lines](principles/15-red-lines.md))
- **Long-running project lost its history?** Condensed timeline per project, alongside handoffs ([Project Chronicles](principles/16-project-chronicles.md))
- **Skill is a monolithic wall of text?** Split into Direction, Blueprints, Solutions ([DBS Framework](principles/17-dbs-skill-creation.md))

**Ready-to-use hooks** that enforce rules mechanically, not probabilistically:

| Hook | Event | What It Does |
|---|---|---|
| [session-drift-validator](hooks/session-drift-validator.py) | `SessionStart` | Validates file references in CLAUDE.md at session start |
| [destructive-command-guard](hooks/destructive-command-guard.py) | `PreToolUse` | Blocks `rm -rf`, `git push --force`, `DROP TABLE` |
| [secret-leak-guard](hooks/secret-leak-guard.py) | `PreToolUse` | Prevents committing API keys, tokens, passwords |
| [session-handoff-reminder](hooks/session-handoff-reminder.py) | `Stop` | Reminds to write handoff before closing long sessions |
| [session-handoff-check](hooks/session-handoff-check.py) | `SessionStart` | Shows recent handoffs from previous sessions |

**Starter templates** for common project types: [web-app](templates/CLAUDE-web-app.md), [ML project](templates/CLAUDE-ml-project.md), [library](templates/CLAUDE-library.md), [code review](templates/REVIEW.md), [project chronicle](templates/chronicle.md), [memory files](templates/memory-project.md).

**Your agent picks the approach that fits.** The [alternatives/](alternatives/) directory compares 2-5 approaches for each problem, with pros, cons, and "when to choose" guidance:

| Problem | Approaches Compared |
|---|---|
| [Multi-step orchestration](alternatives/orchestration.md) | Harness Design, Proof Loop, Deterministic Orchestration, Prompt-only |
| [Code review](alternatives/code-review.md) | Sequential checklist, Parallel competency, Cross-model, LLM + static |
| [Iterative optimization](alternatives/optimization.md) | Autoresearch, HyperAgent, Manual, Eval-driven |
| [Context in long sessions](alternatives/context-management.md) | JIT Loading, Full Context Upfront, Compaction, Fresh Sessions |
| [Session transitions](alternatives/session-handoff.md) | Manual HANDOFF.md, Auto hooks, Session Journal, ContextHarness, Memory |

---

## How This Works

**For the agent (you):** When this repo is connected to your project, you get access to all principles and skills automatically. Use them as decision frameworks - when facing a choice (one agent vs many? how to verify? how to manage context?), check the relevant principle or alternative comparison.

**New:** [HOW-IT-WORKS.md](HOW-IT-WORKS.md) - technical deep dive into how each technology actually works, with real measurements.

**Structure:**
- `principles/` - 17 standalone architectural principles. Read the one that matches your current problem.
- `alternatives/` - side-by-side comparisons of 2-5 approaches per problem. Pick the approach that fits.
- `hooks/` - ready-to-use Python scripts for session management and safety guards.
- `templates/` - starter CLAUDE.md and REVIEW.md files for different project types.
- `skills/` - domain-specific knowledge (AI/ML, frontend, iOS, code review). Loaded on demand.
- `scripts/` - diagnostic utilities (config validator, KV-cache stats).
- `CLAUDE.md` - compact summary of all principles for global config.

---

## Principles by Maturity Level

Start with L1 for any project. Add L2 when tasks repeat and optimization matters. L3 only when solo agent is not enough.

| Level | Focus | Principles |
|---|---|---|
| **L1: Foundational** | Single agent, planning, tool use | Deterministic Orchestration, Structured Reasoning, Skills Best Practices, DBS Skill Creation |
| **L2: Self-Evolving** | Feedback loops, memory, optimization | Autoresearch, Codified Context, Proof Loop |
| **L3: Collective** | Multi-agent coordination | Harness Design, Multi-Agent Decomposition, Managed Agents |
| **Cross-cutting** | Security + Integrity | Supply Chain Defense, Agent Security, Documentation Integrity, Red Lines |
| **Cross-cutting** | Session + Project Continuity | Codified Context, Project Chronicles, Research Pipeline |

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

## Session Handoff - Moving Between Chats

When a Claude Code session gets long, or you want to continue tomorrow on a different machine, or your current chat predates any automation you've set up - just tell the agent to prepare a handoff.

**Type one of these phrases and hit Enter:**

- `prepare handoff`
- `save context for new chat`
- `write handoff`
- `handoff this session`

The agent writes a handoff file with:
- What was the goal
- What got done
- **What did NOT work** (the most valuable part - prevents repeating dead ends)
- Current state (working / broken / blocked)
- Key decisions and why
- The single next step

Then it stops. Close the chat. Open a new one in the same directory. The new session reads the handoff automatically (if you set up the `SessionStart` hook) or you can paste the file as your first message.

**Two storage modes - pick one:**

| Mode | When to use | Storage |
|---|---|---|
| **Single-file** (default, simpler) | One chat at a time | `.claude/HANDOFF.md` |
| **Multi-session** (opt-in) | You run multiple Claude Code chats simultaneously on the same project | `.claude/handoffs/<unique>.md` + append-only `INDEX.md` |

Single-file works for ~80% of users. Switch to multi-session only if you've actually hit last-writer-wins data loss from parallel chats. See [rule file](rules/session-handoff.md) for both protocols and [principle 18](principles/18-multi-session-coordination.md) for the theory behind the multi-session append-only invariant.

**Why a phrase and not a button:** the trigger lives in `.claude/rules/session-handoff.md` as plain markdown. No plugin install, no settings file, no hook. Works in any Claude Code session immediately. This is essential for migrating *existing* sessions that were started before you configured anything.

Copy the ready-made rule file from [rules/session-handoff.md](rules/session-handoff.md) into your project's `.claude/rules/` (or `~/.claude/rules/` for global) and you're done.

**For automation nerds:** pair this with a `Stop` hook that blocks long-session closure until a handoff is written. See [alternatives/session-handoff.md](alternatives/session-handoff.md) for all 5 approaches compared.

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
| Video | `product-meaning-extractor` | Deep product analysis: JTBD, StoryBrand, positioning, customer voice bank |
| Video | `video-narrative-arc` | 5 narrative templates (10s-90s) with beat-by-beat timing and emotional arcs |
| Video | `script-evaluator` | Score scripts on 6 dimensions, detect flatness patterns |
| Video | `remotion-production-guide` | Complete Remotion reference: animations, springs, typography, 3D, export |
| Video | `video-post-production` | FFmpeg patterns for audio, captions, color, platform export |
| Writing | `humanize-english` | Transform AI text into natural English prose |
| Writing | `humanize-russian` | Transform AI text into natural Russian prose |

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

---

## 中文简介

面向 Claude Code 智能体的实战配置系统。包含 17 个架构原则、12+ 对比方案、16 个技能、5 个即用型 Hook 脚本和 7 个项目模板。

**核心功能:**
- `principles/` - 17 个独立架构原则，每个解决一个具体失败模式
- `alternatives/` - 每个问题 2-5 种方案对比，附决策表
- `hooks/` - 5 个即用型 Hook 脚本（漂移检测、安全防护、会话交接）
- `templates/` - 适用于不同项目类型的 CLAUDE.md 起始模板 + 记忆和项目编年史模板
- `skills/` - 领域技能（AI/ML、视频制作、前端、iOS、写作、代码审查）

**安装:** `claude plugin install https://github.com/AnastasiyaW/claude-code-config` 或直接复制所需文件。

**灵感来源:** 部分设计理念受到中国工程社区的启发，包括红线(红线)模式、规范驱动开发(OpenSpec)、经验库模式。

---

## Описание на русском

Система конфигурации для Claude Code агентов. 17 архитектурных принципов, 12+ сравнений подходов, 16 навыков, 5 hook-скриптов и 7 шаблонов.

**Что внутри:**
- `principles/` - 17 принципов, каждый предотвращает конкретный тип отказа
- `alternatives/` - сравнение 2-5 подходов для каждой проблемы с таблицей решений
- `hooks/` - 5 готовых скриптов (валидация drift, защита от деструктивных команд, утечка секретов, handoff)
- `templates/` - стартовые CLAUDE.md для web-app, ML, library + шаблоны memory и хроник
- `skills/` - доменные навыки (AI/ML, видео, фронтенд, iOS, письмо, код-ревью)

**Установка:** `claude plugin install https://github.com/AnastasiyaW/claude-code-config` или копирование нужных файлов.

---

## License

MIT
