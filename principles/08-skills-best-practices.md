# 08 - Skills Best Practices: Building Reliable Claude Code Skills

**Source:** Production experience across multiple Claude Code deployments

## Overview

A skill is a reusable package of knowledge and procedure that a Claude Code agent can invoke. The difference between a skill that gets used effectively and one that gathers dust comes down to three things: discoverability (the model finds it when needed), reliability (it works every time), and maintainability (it stays accurate as the project evolves).

---

## Description as Trigger

The description field in a skill is NOT documentation for humans. It is a **trigger for the model** -- the text that determines whether the model selects this skill for a given task.

### The Formula

```
[What the skill does] + [When to use it -- specific trigger phrases] + [Key capabilities]
```

### Examples

**Bad:**
```
"Helps with servers."
```
The model will rarely select this skill because "helps with servers" matches almost nothing a user would say.

**Good:**
```
"Use when: worker process hangs, GPU health check, service tunnel issues.
Manages GPU compute workers. Can restart services, check GPU memory, diagnose
connectivity problems, and monitor job queue health."
```
The model will select this skill when a user mentions GPU problems, service issues, or queue problems.

### Writing Effective Triggers

1. **Include the exact phrases users will say.** "Worker process hangs" not "workflow execution engine becomes unresponsive."
2. **Include the symptoms, not just the solutions.** Users describe problems ("connection refused"), not solutions ("need to restart the tunnel").
3. **Include the key nouns.** Model matching works on nouns: "GPU", "RunPod", "Redis", "BullMQ", "deploy."
4. **Keep it under 200 words.** Longer descriptions dilute the trigger signal.

---

## Required Sections in SKILL.md

Every skill file must contain these sections:

### Core Instructions

The main body of the skill -- what to do and how to do it. Keep this focused and procedural.

### Gotchas

**The most valuable section.** Populated from real failures, updated every time an edge case is encountered.

```markdown
## Gotchas

- Docker `environment:` in docker-compose.yml OVERRIDES `env_file:` values.
  Do not set the same variable in both places.

- `127.0.0.1 s3.example.com` in /etc/hosts looks like a bug but is a
  local reverse proxy. Do NOT change to the real IP without understanding
  the proxy architecture.

- Multiple SSH connections to the same host in quick succession triggers
  rate limiting (e.g. fail2ban). Reuse a single SSH client per session.

- BullMQ `removeOnComplete` must be set to a number (retention count),
  not `true`. Setting `true` removes jobs immediately, breaking job history.
```

**Maintenance rule:** Every time a skill fails due to an edge case, add the edge case to Gotchas before closing the issue. Gotchas are living documentation of the system's sharp edges.

### Troubleshooting

Structured as symptom-cause-solution triples:

```markdown
## Troubleshooting

### Service connection refused on forwarded port
- **Symptom:** `curl http://localhost:PORT` returns "Connection refused"
- **Cause:** The tunnel or port-forward process is not running
- **Solution:** Restart the tunnel manager: `python tunnel_manager.py start`

### GPU worker returns 500 on job submission
- **Symptom:** POST /api/job returns HTTP 500
- **Cause:** GPU out of memory (previous job did not clean up VRAM)
- **Solution:** Restart the worker container: `docker restart gpu-worker`
  Then verify: `curl http://localhost:8080/health`

### Jobs stuck in "active" state indefinitely
- **Symptom:** BullMQ dashboard shows jobs active for >30 minutes
- **Cause:** Worker crashed mid-processing, job lock not released
- **Solution:** Move stale active jobs to failed:
  `bull queue clean --status active --age 1800`
```

**Format matters.** Symptom first (what the user observes), cause second (why it happens), solution third (what to do). Do not start with the cause -- users search by symptoms.

---

## File Structure

### Size Limit

SKILL.md should stay under **5,000 words**. If it exceeds this:
- The model will struggle to process it efficiently
- Important details get lost in volume
- Maintenance becomes burdensome

### Directory Organization

```
.claude/skills/
  my-skill/
    SKILL.md              # Main skill file (<5000 words)
    references/           # Detailed reference material
      api-docs.md         # API documentation
      architecture.md     # System architecture details
      examples.md         # Extended examples
    scripts/              # Executable scripts
      health-check.sh     # Health check script
      deploy.sh           # Deployment script
      validate.sh         # Validation script
```

### Rules

- **SKILL.md** is the entry point. It should be self-contained for common cases.
- **references/** holds detailed material that SKILL.md links to but does not include inline.
- **scripts/** holds executable scripts that the skill invokes.
- **No README.md** inside a skill directory. SKILL.md IS the readme.

---

## Critical Validations: Scripts, Not Words

This is the single most important principle for skill reliability:

**Code is deterministic. Language is not.**

### The Problem

If a skill says "verify that the deployment succeeded by checking the health endpoint," the model might:
- Check the wrong endpoint
- Accept a 500 response as "healthy" because the page returned HTML
- Skip the check entirely because it "knows" the deployment worked
- Check once and move on even though the service needs 30 seconds to start

### The Solution

Replace prose validations with executable scripts:

**Wrong (prose instruction):**
```markdown
After deploying, check that the service is healthy by hitting the
health endpoint and confirming it returns 200.
```

**Right (executable script):**
```bash
#!/bin/bash
# scripts/verify-deployment.sh
MAX_RETRIES=10
RETRY_DELAY=3

for i in $(seq 1 $MAX_RETRIES); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health)
  if [ "$STATUS" = "200" ]; then
    echo '{"status": "healthy", "attempts": '$i'}'
    exit 0
  fi
  sleep $RETRY_DELAY
done

echo '{"status": "unhealthy", "attempts": '$MAX_RETRIES', "last_status": "'$STATUS'"}'
exit 1
```

The script:
- Always checks the right endpoint
- Retries automatically
- Returns structured output (JSON + exit code)
- Has deterministic behavior regardless of model interpretation

### When to Use Scripts vs. Prose

| Task | Use Script | Use Prose |
|---|---|---|
| Health checks | Yes | No |
| Configuration validation | Yes | No |
| Test execution | Yes | No |
| File existence checks | Yes | No |
| Architectural reasoning | No | Yes |
| Decision-making with trade-offs | No | Yes |
| User communication | No | Yes |
| Creative problem-solving | No | Yes |

**Rule of thumb:** If the same input should always produce the same output, use a script. If judgment is required, use prose.

---

## Skill Lifecycle

### Creation

1. Identify a repeating task pattern
2. Write SKILL.md with description (trigger), core instructions, empty Gotchas, empty Troubleshooting
3. Create initial validation scripts
4. Test the skill on 2-3 real tasks

### Iteration

1. After each use, review what went wrong
2. Add edge cases to Gotchas
3. Add failure patterns to Troubleshooting
4. Refine validation scripts based on observed failures
5. Update the description if the model is not selecting the skill when it should

### Retirement

1. If a skill has not been used in 30+ days, review whether it is still needed
2. If the underlying system has changed significantly, the skill may be misleading
3. An inaccurate skill is worse than no skill -- it gives the model false confidence

---

## Checklist for Skill Review

When creating or reviewing a skill, verify:

- [ ] Description includes specific trigger phrases users would say
- [ ] Description is under 200 words
- [ ] SKILL.md is under 5,000 words
- [ ] Gotchas section exists (even if empty for new skills)
- [ ] Troubleshooting section exists with symptom-cause-solution format
- [ ] All deterministic validations are scripts, not prose
- [ ] Scripts return structured output (JSON + exit code)
- [ ] No README.md in the skill directory
- [ ] References and scripts are in their respective subdirectories
- [ ] The skill has been tested on at least one real task

---

## Parameterized Skills with $ARGUMENTS

Skills can accept arguments from the user via `$ARGUMENTS`. When a user invokes `/my-skill some text here`, the `some text here` part is available as `$ARGUMENTS` inside the skill.

### Usage in SKILL.md

```markdown
---
name: review
description: Code review with configurable focus. Use when asked to review code.
---

Review the code changes with focus on: $ARGUMENTS

If no specific focus given, do a general review covering security, performance, and correctness.
```

### Invocation

```
/review security          -> $ARGUMENTS = "security"
/review PR #42            -> $ARGUMENTS = "PR #42"
/review                   -> $ARGUMENTS = "" (empty)
```

### Best Practices

1. **Always handle empty arguments.** Not everyone will pass them. Provide sensible defaults.
2. **Document expected arguments** in the skill description, not just in the body.
3. **Keep argument parsing simple.** Natural language, not CLI flags. The model interprets it.
4. **Use arguments for scope, not behavior.** Good: `/review security` (narrows focus). Bad: `/review --format=json --strict` (CLI-style flags confuse the model).

### Examples

```markdown
# Skill: /investigate
Investigate the issue: $ARGUMENTS

If $ARGUMENTS is empty, ask the user what to investigate.

# Skill: /ship
Ship the changes. Additional instructions: $ARGUMENTS

Default behavior: merge base, test, review, PR.
If $ARGUMENTS includes "hotfix", skip non-critical checks.
```

---

## Relationship to Other Principles

| Principle | Relationship |
|---|---|
| **Deterministic Orchestration (04)** | "Critical validations as scripts" is the Shell Bypass principle applied to skills |
| **Codified Context (07)** | Skills themselves are codified context -- reusable packages of knowledge |
| **Autoresearch (03)** | Skills with measurable pass rates can be improved through autoresearch cycles |
| **Proof Loop (02)** | Skill execution results (script outputs) serve as evidence in the proof loop |
| **Harness Design (01)** | Skills can be used as building blocks for Generator and Evaluator agents in a harness |
