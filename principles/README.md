# Architectural Principles for AI Agent Systems

A collection of 9 battle-tested principles for building reliable, high-quality AI agent workflows. Each principle is self-contained and can be adopted independently, but they compose well together.

---

## Principles Overview

### [01 - Harness Design](01-harness-design.md)

Multi-agent architecture patterns for long-running AI applications. Separates generation from evaluation to overcome self-evaluation bias. Defines when a solo agent suffices and when the 20x cost of a full harness is justified.

**When to use:** Building any multi-step AI workflow where quality matters more than speed. Designing evaluation systems. Planning agent architectures.

**Source:** Anthropic Engineering -- "Harness design for long-running apps"

---

### [02 - Proof Loop](02-proof-loop.md)

A rigorous verification protocol where agents cannot self-certify completion. Requires durable artifacts (test outputs, logs, verdict files) as proof, verified by a fresh session that never saw the build process.

**When to use:** Any task where "it works on my machine" is not acceptable. Critical deployments. Tasks requiring audit trails. Multi-agent handoffs where trust boundaries matter.

**Source:** OpenClaw-RL paper (arxiv 2603.10165) + DenisSergeevitch/repo-task-proof-loop

---

### [03 - Autoresearch](03-autoresearch.md)

Iterative self-optimization through automated experimentation. Read one thing, change one thing, test mechanically, keep or discard, repeat. Scales from linear hill-climbing to branching version graphs with meta-optimization.

**When to use:** Improving any artifact with a measurable score -- prompts, skills, code coverage, latency, bundle size. NOT for subjective tasks without scriptable evaluation.

**Source:** Andrej Karpathy (github.com/karpathy/autoresearch) + HyperAgents paper [2603.19461]

---

### [04 - Deterministic Orchestration](04-deterministic-orchestration.md)

The principle that LLMs should never execute deterministic processes. Mechanical tasks (test, lint, format, detect) run as shell scripts; the LLM only handles creative/reasoning work. State lives in files, not in the agent's memory.

**When to use:** Any workflow with mechanical steps mixed with reasoning steps. Building skills with multi-step processes. Designing CI/CD-like agent pipelines.

**Source:** Deterministic orchestration patterns for AI coding agents

---

### [05 - Structured Reasoning](05-structured-reasoning.md)

Replaces free-form chain-of-thought with semi-formal reasoning: Premises, Execution Trace, Conclusions, Rejected Paths. Eliminates "planning hallucinations" where the model builds plausible but incorrect reasoning chains.

**When to use:** Debugging with non-obvious root causes. Architecture decisions with more than 2 options. Performance optimization. Security review. NOT needed for simple CRUD tasks.

**Source:** [2603.01896] Agentic Code Reasoning (Mar 2026)

---

### [06 - Multi-Agent Task Decomposition](06-multi-agent-decomposition.md)

Strategies for breaking complex tasks across multiple specialized agents. Defines when single-agent is sufficient (function-level) versus when multi-agent coordination is needed (system-level), and how to structure the coordinator.

**When to use:** Tasks touching more than 3 files. Cross-cutting concerns (security, performance, accessibility). System-level refactoring. Large feature implementations.

**Source:** [2603.14703] Multi-Agent System Optimization + [2603.13256] Training-Free Multi-Agent Coordination

---

### [07 - Codified Context](07-codified-context.md)

Treats project context as runtime infrastructure rather than documentation. CLAUDE.md is a runtime config, rules are conditional context injection, memory files are persistent state. Introduces JIT context loading to manage the context window efficiently.

**When to use:** Any project with AI agents. Setting up CLAUDE.md and memory systems. Managing context across long sessions. Designing handoff artifacts between agent sessions.

**Source:** [2602.20478] Codified Context: Infrastructure for AI Agents in a Complex Codebase

---

### [08 - Skills Best Practices](08-skills-best-practices.md)

Practical guide for creating reliable, discoverable Claude Code skills. Covers description-as-trigger design, mandatory sections (Gotchas, Troubleshooting), file structure conventions, and the principle that critical validations must be scripts, not prose.

**When to use:** Creating or updating any skill in `.claude/skills/`. Reviewing existing skills for quality. Designing skill libraries.

**Source:** Production experience across multiple Claude Code deployments

---

### [09 - Supply Chain Defense](09-supply-chain-defense.md)

Protect against malicious package updates by gating fresh packages. Set `min-release-age=7` (npm) and `exclude-newer = "7 days"` (uv) globally. Most poisoned packages are detected within 1-3 days; 7-day delay eliminates the attack window with near-zero friction.

**When to use:** Always. Every development machine, every CI runner. Override only for critical security patches that need immediate deployment.

**Source:** Industry practice in response to escalating open-source supply chain attacks (2024-2026)

---

## Decision Matrix

Use this table to pick the right principle for your situation:

| Situation | Primary Principle | Supporting Principles |
|---|---|---|
| "Agent output quality is inconsistent" | 01 Harness Design | 02 Proof Loop |
| "How do I verify the agent actually did it?" | 02 Proof Loop | 04 Deterministic Orchestration |
| "I want to improve my prompt/skill automatically" | 03 Autoresearch | 02 Proof Loop (final verification) |
| "Agent keeps forgetting steps in a process" | 04 Deterministic Orchestration | 07 Codified Context |
| "Debugging is going in circles" | 05 Structured Reasoning | 04 Deterministic Orchestration |
| "Task is too big for one agent" | 06 Multi-Agent Decomposition | 01 Harness Design |
| "Agent loses context between sessions" | 07 Codified Context | 04 Deterministic Orchestration |
| "My skills are hard to discover/maintain" | 08 Skills Best Practices | 07 Codified Context |
| "Solo agent works but quality plateaus" | 01 Harness Design | 03 Autoresearch |
| "Need audit trail for compliance" | 02 Proof Loop | 05 Structured Reasoning |
| "Multi-file refactoring keeps breaking things" | 06 Multi-Agent Decomposition | 02 Proof Loop |
| "Agent invents false claims about completion" | 02 Proof Loop | 04 Deterministic Orchestration |
| "Worried about malicious dependency updates" | 09 Supply Chain Defense | 04 Deterministic Orchestration |

### Composition Patterns

These principles are designed to layer:

1. **Optimization + Verification:** Use Autoresearch (03) for iterative improvement, then Proof Loop (02) for final sign-off.
2. **Decomposition + Evaluation:** Use Multi-Agent Decomposition (06) to split the work, Harness Design (01) to evaluate each piece.
3. **Context + Orchestration:** Use Codified Context (07) for state management, Deterministic Orchestration (04) for process control.
4. **Reasoning + Verification:** Use Structured Reasoning (05) to analyze, Proof Loop (02) to prove the analysis is correct.
