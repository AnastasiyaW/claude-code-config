# Principle 14: Managed Agents

## The Problem

Building multi-agent systems requires managing infrastructure: container orchestration, session state, tool provisioning, sandbox isolation. Teams reinvent this for every project, spending more time on plumbing than on the actual agent logic.

## The Paradigm

**Separate the brain from the hands.** The "brain" (planning, reasoning, decision-making) runs as your primary agent. The "hands" (code execution, file operations, web browsing) run as managed sub-agents with their own sandboxed environments.

Source: Anthropic Engineering - "Managed Agents" (April 8, 2026)

## The Mechanism

### Core Interface

```
execute(name: str, input: str) -> str
```

Every managed agent exposes a single function. The brain agent calls it with natural language input and gets a string result back. No tool schemas, no parameter negotiation - just text in, text out.

### Architecture: Brain / Hands / Session

| Layer | Role | Lifetime |
|---|---|---|
| **Brain** | Planning, reasoning, task decomposition | Per-conversation |
| **Hands** | Code execution, file ops, browsing, tool use | Per-task (spun up/down) |
| **Session** | State persistence, file system, installed tools | Across multiple hand invocations |

**Key insight:** Sessions are lazily provisioned. The first `execute()` call triggers environment setup (container, tools, credentials). Subsequent calls reuse the warm session. This gives p50 TTFT -60%, p95 -90%+ compared to eager provisioning.

### When Managed Agents vs DIY

| Factor | Use Managed Agents | Build Your Own |
|---|---|---|
| Sandbox isolation needed | Yes - get it free | Must build container orchestration |
| Tool set is standard (code, browse, files) | Yes - pre-built | Custom tools need custom agents |
| Cost sensitivity | $0.08/session-hour + tokens | Self-hosted can be cheaper at scale |
| Vendor lock-in tolerance | Acceptable | Unacceptable - use Agent SDK |
| Team size | Small teams, fast iteration | Large teams with infra capacity |

### Extended Decision Matrix: 12 criteria for Managed vs Self-Built Harness

When deciding between Anthropic Managed Agents (or any provider's managed offering) vs a self-built harness following [principle 01](01-harness-design.md):

| Criterion | Managed Agents | Self-built (principle 01 + 29) |
|---|---|---|
| **Standard workload** (code exec, web browse, file ops in sandbox) | ✅ preferred — no infra investment | overhead unjustified |
| **Custom tools** that need tenant-specific permissions | ❌ no access to your permission model | ✅ required |
| **Regulated data** (HIPAA, GDPR, financial) | ❌ data leaves your trust boundary | ✅ required |
| **Custom audit / compliance** logging beyond provider's defaults | ❌ provider's audit, not yours | ✅ required |
| **Financial / payment / billing** actions | ❌ provider lacks domain-specific approval flow | ✅ required |
| **Communication sends** through your SMTP / Twilio / messaging stack | ❌ no access to your credentials | ✅ required |
| **Identity / access management** changes (key rotation, permission grants) | ❌ provider isn't part of your IAM trust chain | ✅ required |
| **Multi-tenant isolation** with per-tenant boundaries | ❌ provider doesn't know your tenant model | ✅ required |
| **Quick prototype / POC** with standard tools | ✅ ship in days, not weeks | over-engineered for prototype |
| **Sustained high-volume** workload where $0.08/session-hour adds up | self-hosted may be cheaper at scale | ✅ amortize infra cost |
| **Vendor lock-in tolerance low** (regulated industries, sovereign cloud, multi-cloud strategy) | ❌ provider-specific runtime | ✅ portable |
| **Team has no infra capacity** (no SRE, no Kubernetes expertise) | ✅ infrastructure handled for you | ❌ becomes operational burden |

**Rule of thumb:** Start with Managed Agents when ≥3 «✅ Managed» columns hit, and your workload doesn't touch any «❌ Managed» row. As soon as one «❌ Managed» row applies (regulated data, custom audit, financial actions, tenant model, IAM), you need a self-built harness for at least that portion.

**Hybrid pattern (common in production):** Use Managed Agents for **standard sub-tasks** (research, web browse, code execution in sandbox) **invoked by** a self-built brain that owns business authorization, approval flow, audit log, and tenant-specific permissions. The managed agent is treated as just-another-tool from the self-built brain's perspective — with the same risk taxonomy, approval gating, and trust boundary rules from [rules/agent-tool-design.md](../rules/agent-tool-design.md) applied to its results.

### Relationship to Other Patterns

**vs Harness Design (Principle 01):** Managed Agents implement the Generator-Evaluator pattern at infrastructure level. The brain = generator, hands = executor. But the evaluator role still needs explicit design - Managed Agents don't auto-evaluate quality.

**vs Multi-Agent Decomposition (Principle 06):** Managed Agents handle the "how do I run multiple agents" problem. Decomposition principles handle the "what should each agent do" problem. They compose: use Principle 06 to design the split, Managed Agents to execute it.

**vs Proof Loop (Principle 02):** Managed Agents provide isolated execution environments, but don't enforce verification. Add proof loop on top: after a managed agent claims completion, spin up a fresh agent to verify.

### Claude Code Integration

In Claude Code, managed agents map to Agent tool sub-agents:

```
Agent(
  prompt="Review this PR for security issues",
  subagent_type="general-purpose",
  isolation="worktree"  # Isolated copy of repo
)
```

For team-based coordination, Claude Code's built-in Agent Teams (behind feature flag, v2.1.89+) provide:
- `TeamCreate` - create a task list and team
- `SendMessage` - inter-agent communication
- `TaskUpdate` - shared task tracking

**Note (April 2026):** Analysis of Claude Code internals (510K lines TypeScript) reveals a fully-implemented swarm orchestration system (`TeamCreateTool`) behind a feature flag. This signals Anthropic is moving toward built-in coordination. External orchestrators should be complementary, not competing.

### Self-Hosted Alternatives

| Tool | Approach | Best For |
|---|---|---|
| CrewAI | Role-based multi-agent, Python | Teams with custom tool needs |
| Docker Agent SDK | Container-based isolation | Full control, any model |
| Hermes (self-learning) | Self-improving agent loops | Research, optimization |
| tama | Minimal agent coordinator | Simple task distribution |

### HiClaw Pattern (Alibaba/AgentScope)

HiClaw uses Matrix protocol for inter-agent communication. Notable design:
- **Worker tokens only** - agents get scoped tokens, real credentials stay in the gateway
- **Permission scoping** - each agent sees only the tools it needs
- Relevant for registries that manage multiple agents with different trust levels

## Gotchas

1. **Lazy provisioning can surprise you.** First call to a managed agent takes 2-10s for environment setup. Plan for this latency in user-facing workflows.

2. **Session state is not conversation state.** Files written in a managed agent session persist across `execute()` calls, but the agent's conversation memory does not. Pass context explicitly.

3. **Cost compounds.** Each managed agent session incurs $0.08/hour + token costs. A harness with 5 agents running 30 minutes = $0.40 in session fees alone, plus ~$5-20 in tokens.

4. **Brain agent still needs guardrails.** Managed Agents sandbox the hands, not the brain. The brain can still hallucinate task decompositions, skip verification, or misinterpret results.

## Sources

- Anthropic Engineering: "Managed Agents" (April 8, 2026)
- Claude Code Agent Teams documentation
- HiClaw / AgentScope (Alibaba): Matrix protocol inter-agent communication
- PaddoDev: Claude Code internals analysis - TeamCreateTool feature flag
