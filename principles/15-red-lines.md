# Principle 15: Red Lines (红线)

## The Problem

AI coding agents have rules, guidelines, and best practices - but they are all treated with the same priority. When context pressure grows (long sessions, complex tasks, urgent requests), the agent starts cutting corners on lower-priority rules. Without a clear hierarchy, it may cut corners on the wrong ones.

## The Paradigm

**Red lines are absolute prohibitions that cannot be violated regardless of context, urgency, or explicit user request.** They are separate from regular rules, carry higher priority, and each one has an incident history explaining why it exists.

Source: Chinese engineering community pattern (红线, literally "red line"). Used by Chinese tech teams (ByteDance, Alibaba, Tencent) to define non-negotiable boundaries in agent-assisted workflows.

## The Mechanism

### Structure

Create a `REDLINES.md` file (or a section in CLAUDE.md) with this format:

```markdown
# Red Lines - Never Cross

## RL-01: Never delete production data
**Severity:** CRITICAL
**Incident:** 2026-02-15 - Agent interpreted "clean up old records"
as DELETE FROM users WHERE created_at < '2025-01-01'
**Rule:** Never execute DELETE/DROP/TRUNCATE on any database
without explicit user confirmation of the exact SQL statement.
No inference, no "obvious" interpretations.

## RL-02: Never commit secrets
**Severity:** CRITICAL
**Incident:** 2026-03-01 - API key in .env committed when agent
ran `git add -A` after being told to "commit everything"
**Rule:** Never use `git add -A` or `git add .` without first
checking for .env, credentials, keys, tokens in the diff.
```

### Key Properties

| Property | Regular Rules | Red Lines |
|---|---|---|
| Priority | Normal - can be balanced against each other | Absolute - never overridden |
| Violation response | Correct and continue | Stop and alert |
| Context-dependent | Yes - "prefer X" means usually, not always | No - "never Y" means never |
| Requires incident | No - can be proactive | Yes - each red line traces to a real failure |
| Count | Unlimited | 5-15 maximum (too many = none are special) |

### Red Line Categories

**Data Safety:**
- Never delete production data without explicit confirmation of exact scope
- Never expose secrets in commits, logs, or error messages
- Never overwrite uncommitted changes without confirmation

**System Integrity:**
- Never modify system files (/etc/*, registry, global configs) without confirmation
- Never restart all instances of a service simultaneously
- Never change firewall/security rules without understanding current state

**External Actions:**
- Never send messages/emails/notifications on behalf of user without explicit confirmation
- Never create public repositories or make private repos public
- Never post to external services (social media, forums) without confirmation

**Agent-Specific:**
- Never disable security controls, even if they seem to be blocking progress
- Never substitute a different model/tool/service for what was requested
- Never use paid APIs or services without explicit user request

### Implementation Patterns

**Pattern 1: CLAUDE.md section (simplest)**

Put a `## Red Lines` section at the TOP of CLAUDE.md (before any other rules):

```markdown
## Red Lines - NEVER violate these regardless of context

1. Never `git add -A` - always add specific files
2. Never DELETE/DROP without showing exact SQL to user first
3. Never commit .env, credentials, or key files
4. Never restart all service instances at once
5. Never use paid APIs without explicit request
```

**Pattern 2: Separate REDLINES.md**

A dedicated file loaded via `.claude/rules/redlines.md`:

```markdown
# Red Lines

These override ALL other rules. If a regular rule conflicts
with a red line, the red line wins.

[Full entries with incidents as shown above]
```

**Pattern 3: Hook enforcement (strongest)**

Convert critical red lines to PreToolUse hooks that mechanically block violations:

```json
{
  "matcher": "Bash(git add -A|git add .)",
  "hooks": [{
    "type": "command",
    "command": "echo '{\"decision\":\"block\",\"reason\":\"Red line: never git add -A. Add specific files instead.\"}'"
  }]
}
```

Hook enforcement is the strongest because it does not rely on the agent remembering or choosing to follow the rule.

### Red Line Lifecycle

1. **Incident occurs** - agent makes a mistake with real consequences
2. **Root cause analysis** - what was the trigger, what was the incorrect reasoning
3. **Red line drafted** - specific prohibition with incident reference
4. **Implementation** - added to CLAUDE.md/REDLINES.md + hook if possible
5. **Review quarterly** - are all red lines still relevant? Any new incidents?

### Relationship to Other Principles

**vs Agent Security (Principle 10):** Agent Security covers external threats (injection, poisoning). Red Lines cover self-inflicted mistakes - the agent doing something harmful with good intentions.

**vs Deterministic Orchestration (Principle 04):** Red Lines define WHAT must not happen. Deterministic Orchestration defines HOW to ensure mechanical tasks run correctly. They compose: critical red lines should be enforced by hooks (deterministic), not just rules (probabilistic).

**vs Documentation Integrity (Principle 11):** Red lines with incident history ARE living documentation. They decay less than regular docs because each one is anchored to a real failure.

## Gotchas

1. **Too many red lines = none are special.** Keep to 5-15. If everything is a red line, the agent treats them all as regular rules. The whole point is that these are the FEW things that absolutely cannot happen.

2. **Red lines without incidents are just opinions.** The incident history is what gives a red line its weight. "Never use force push" is a preference. "Never use force push - on 2026-01-15 a force push to main overwrote 3 days of teammate's work" is a red line.

3. **Red lines must be specific.** "Be careful with data" is not a red line. "Never execute DELETE without showing the exact WHERE clause to the user" is a red line.

4. **Hook > Rule > Hope.** The enforcement hierarchy: hooks block mechanically (guaranteed), rules guide probabilistically (usually works), nothing else is reliable under context pressure.

## Sources

- Chinese engineering community (红线 pattern) - ByteDance, Alibaba, Tencent internal practices
- OWASP Agentic Applications Top 10 (ASI09: Human-Agent Trust Erosion)
- Production incident analysis from Claude Code deployments
