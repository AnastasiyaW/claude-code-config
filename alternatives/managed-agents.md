# Managed Agents vs Self-Hosted - when to run agents on Anthropic infra vs your own

## Problem

Long-running AI agents need: sandbox containers, crash recovery, session persistence, scaling. Building this yourself takes weeks. But the managed alternative costs more and locks you in.

## Three Deployment Models

### 1. Claude Code CLI (Interactive)

Your machine, your filesystem, your rules. Best for daily coding.

```
claude "fix the auth bug"     # local, Pro plan ($20/mo flat)
```

- Full hook/skill/CLAUDE.md ecosystem
- No container isolation (runs on your FS)
- Session dies when terminal closes
- Cannot serve other users

### 2. Agent SDK (Self-Hosted Automation)

Claude Code as a library. Your infra, your containers, your scaling.

```python
from claude_code_sdk import query
result = await query(prompt="run the test suite", options={
    "allowed_tools": ["Bash", "Read", "Edit"],
    "system_prompt": "CI agent for project X",
})
```

- Multi-provider: Claude API, Bedrock, Vertex, Azure Foundry
- You provide containers (Docker, microVM, Contree)
- You handle crash recovery, scaling, observability
- Full customization, no vendor lock beyond Claude model

### 3. Managed Agents (Anthropic Cloud)

Anthropic runs the containers. You define the agent, they handle the rest.

```bash
curl -X POST https://api.anthropic.com/v1/agents \
  -H "anthropic-beta: managed-agents-2026-04-01" \
  -d '{"name": "code-reviewer", "model": "claude-sonnet-4-6-20260409",
       "instructions": "Review PRs for security issues",
       "tools": [{"type": "bash"}, {"type": "text_editor"}]}'
```

- $0.08/session-hour + standard API token costs
- Container auto-provisioned, isolated per session
- Session survives disconnections (server-side event log)
- Claude-only, Anthropic-infra-only

## Architecture: Brain / Hands / Session

Managed Agents separate three concerns that are usually entangled:

| Component | What | Key benefit |
|-----------|------|------------|
| **Brain** | Claude + system prompt + tools | Stateless, scales horizontally |
| **Hands** | Container sandbox | **Lazy-provisioned** on first tool call |
| **Session** | Append-only event log | Durable, lives outside context window |

**Performance impact of lazy provisioning:**
- p50 TTFT: -60% (container doesn't spin up until needed)
- p95 TTFT: -90%+ (worst-case latency drastically reduced)

## Cost Analysis

### Token Costs (same across all three)

| Model | Input | Cache hits | Output |
|-------|-------|-----------|--------|
| Opus 4.6 | $5/MTok | $0.50/MTok | $25/MTok |
| Sonnet 4.6 | $3/MTok | $0.30/MTok | $15/MTok |
| Haiku 4.5 | $1/MTok | $0.10/MTok | $5/MTok |

### Total Cost Comparison

| Scenario | CLI | Agent SDK | Managed Agents |
|----------|-----|-----------|---------------|
| Solo dev, daily use | $20/mo (Pro) | N/A | N/A |
| PR reviews, 20 PRs/day | ~$25/mo (Sonnet API) | Same | Same + $0.08/hr |
| 1 agent, 8 hrs/day | N/A | Compute + tokens | $19.20/mo runtime + tokens |
| 24 agents, 8 hrs/day | N/A | VPS $20-50 + tokens | **$461/mo runtime** + tokens |
| 24/7 single agent | N/A | VPS $5-20 + tokens | **$58/mo runtime** + tokens |

**Break-even:** if maintaining your container infra costs >$440/mo in engineering time, Managed Agents saves money. Otherwise self-hosted wins on cost.

## Decision Matrix

| Signal | Use CLI | Use Agent SDK | Use Managed Agents |
|--------|---------|--------------|-------------------|
| Interactive coding | Best | Overkill | Overkill |
| CI/CD automation | No | Best | Works, costlier |
| Product for users | No | Best if you have infra team | Best if you don't |
| Long-running (hours) | Session fragile | You handle persistence | Built-in persistence |
| Data privacy critical | Full local control | Full control | Data through Anthropic |
| Multi-model needed | No | Bedrock/Vertex/Foundry | Claude-only |
| Need scaling | No | You build it | Automatic |
| Cost-sensitive at scale | Best (Pro flat) | Moderate | Expensive |

## Vendor Lock-in Assessment

| Dimension | Agent SDK | Managed Agents |
|-----------|-----------|---------------|
| Model provider | Swappable (Bedrock/Vertex) | Claude API only |
| Infra | Any cloud, any container | Anthropic only |
| Session format | Standard (you define) | Proprietary event log |
| Migration cost | Low (it is API calls) | High (rewrite orchestration) |
| Tool definitions | Standard Claude tools | Same, but environment configs are proprietary |

## Self-Hosted Alternatives

| Tool | What | Open source | Notes |
|------|------|------------|-------|
| **Agent SDK** | Claude Code as library | Anthropic terms | Best for Claude-native teams |
| **CrewAI** | Multi-agent orchestration | Yes | Model-agnostic via LiteLLM |
| **Docker Agent** | Docker CLI plugin | Yes | Run any model in containers |
| **Hermes Agent** | Self-improving agent | Yes | Runs on $5 VPS |
| **tama** (tama.mlops.ninja) | Docker-wrapped agents | Unclear | Very new, minimal docs as of Apr 2026 |

## Recommendation

For teams already using Claude Code with hooks/skills/CLAUDE.md:

1. **Keep CLI for daily work** - your customized setup is more powerful than Managed Agents
2. **Agent SDK for automation** - CI/CD, scheduled tasks, products. Natural extension of your workflow
3. **Managed Agents only when** building a product for OTHER users where you'd rather not manage containers
4. **Skip Managed Agents if** you need multi-model, care about data locality, or run many agents at scale

The $0.08/hour is negligible for light use. The real cost is at scale AND in lock-in: once you build on Managed Agents' proprietary session format, migration requires rewriting the orchestration layer.

## Real-World Cost Data Point

Native Claude Review in GitHub via API Key: ~$20/week at moderate usage (direct API). This matches Sonnet 4 at ~$0.04-0.05 per 400-line diff review, ~20 PRs/day. Alternative: Claude Code GitHub Action (open source) with same API key, same cost, more control.

## Sources

- Anthropic Engineering: managed-agents architecture
- Claude blog: managed-agents announcement (Apr 8, 2026)
- Anthropic API docs: managed-agents overview, pricing
- HackerNews discussion thread
