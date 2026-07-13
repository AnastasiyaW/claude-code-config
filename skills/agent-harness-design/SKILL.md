---
name: agent-harness-design
description: Designing agent harnesses and tool systems — risk taxonomy for tools, permission decisions, draft/commit pattern, structured tool results, agent budgets (10 types), context trust labels against prompt injection, plan-artifact, approval records, observability and traces, evals (13 categories), event model, streaming buffering, 3rd-party skill install checklist, agentic RAG, self-improving SOP loops, model policy, reasoning effort, and Programmatic Tool Calling adoption gates. Use when building a new Agent SDK app, custom orchestrator, MCP server, Cloudflare Worker with tool calls, agentic RAG pipeline, model router, or model-tier policy; when designing tools and permissions; when writing an agent loop; or when you need trust labels for external content. Do NOT use for improving or auditing an already-built harness (use harness-audit / harness-design instead), nor for ordinary Claude Code sessions where the harness is already given.
---

# Agent Harness Design

Eleven operational reference sheets for designing a safe, observable agent harness. They are **situational** — load only the one(s) relevant to the current task from `references/` (this is why they live in a skill rather than always-on rules: building an agent harness is occasional, so the detail should not bloat every session's context).

- `references/agent-tool-design.md` — 15-class risk taxonomy, 7-type permission decision object, draft/commit naming, structured tool results, deferred tool loading, hosted vs client tools, connector code-execution pattern.
- `references/context-trust-labels.md` — trusted / semi_trusted / untrusted labels + verbatim boundary statement; prompt-injection defense.
- `references/agent-budgets.md` — 10 mandatory budget types every agent loop must declare.
- `references/agent-evals.md` — 13 eval categories + 13 adversarial test cases + when to add regression evals.
- `references/agent-observability.md` — 16 trace fields per model call, 7-question audit, 6-step incident response.
- `references/agentic-rag-model-policy.md` — self-improving agentic RAG state, specialist roles, evaluation vectors, Pareto selection, OpenAI model/effort policy, and Programmatic Tool Calling adoption gates.
- `references/agent-plan-artifact.md` — planning mode, plan artifact format (10 fields), plan-validate-execute.
- `references/agent-approval-records.md` — approval request/result JSON schemas, scope/expiration, no self-approval.
- `references/agent-streaming.md` — buffering for incremental tool calls when stream=True; abort handling; output guardrail modes.
- `references/agent-event-model.md` — 13 typed events for harness state persistence (replay/audit/compaction/evals).
- `references/agent-skill-install-checklist.md` — pre/during/post install + audit + incident response for 3rd-party skills.

Source: distilled from the `agents-best-practices` skill (Denis Sergeevitch, MIT) + Anthropic harness-design engineering. Read the specific reference before applying — do not work from this index alone.
