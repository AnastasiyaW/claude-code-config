# 22 - Anti-pattern as Config: Explicit Negative Lists and the Anti-Attractor Procedure

**Source:** Distilled from pbakaus/impeccable (2026-04) + OWASP agent security research + our own harness-design experience.

## Overview

Most configuration tells the agent what to do: "use this library, follow this style, match this design system." This works for tasks where success has many correct answers. It fails for tasks where the **failure mode is a single attractor** — one generic default that the agent reverts to under pressure.

For those tasks you need the opposite: an **explicit list of what not to do**, enforced at two layers:

1. **At prompt time**, the agent is told to enumerate and reject its default reflexes before committing.
2. **At verification time**, a deterministic check (script, linter, regex, vision model) fails the output if any anti-pattern is present.

This principle codifies that discipline. It is the frontend/design-slop version of what secure coding checklists do for AppSec: list the bad patterns, check for them every time.

---

## The Failure Mode This Fixes

Observed across every major LLM: without explicit anti-pattern guidance, models regress to the same small set of "safe" choices, because those choices are statistically most represented in training data.

For frontend design:
- Inter font, system defaults
- Purple gradients, dark glows
- Cards nested in cards ("Cardocalypse")
- Gray text on colored backgrounds
- Bounce / elastic easing

For copy:
- "Elevate your workflow" / "Unlock the power of"
- "Game-changing", "Seamless", "Cutting-edge"
- Every CTA reading "Get started today"

For architecture:
- Microservices for a 3-endpoint app
- Redis for a 100-row dataset
- React for a static landing page

For naming:
- `getData()`, `handleClick()`, `Utils`
- `MyService`, `DataManager`, `ThingHelper`

Positive-only guidance does not fix this. "Use distinctive typography" does not prevent Inter because the model considers Inter distinctive. **Explicit exclusion** does: "Do not use Inter, Roboto, Arial, or system-ui. If those are your first instincts, name three alternatives and pick one."

---

## The Anti-Attractor Procedure

A three-step routine for the agent to run **before** committing to a visible choice (font, color, layout, variable name, data structure):

### Step 1: Name the reflex default

Before selecting, the agent writes out what its first instinct would be.

> *"My first instinct is to use Inter at 16px with gray-600 body text on white background."*

This externalizes the attractor so it can be examined.

### Step 2: Reject if on the anti-pattern list

The agent checks the default against an explicit list. If the default is a known anti-pattern, reject it.

> *"Inter is on the anti-pattern list (rule IMP-TYPE-001). Rejecting."*

### Step 3: Enumerate alternatives, pick one with justification

Instead of picking the second attractor (also often generic), the agent lists three distinct alternatives and justifies the choice against the task context.

> *"Alternatives: (a) Söhne — feels editorial, fits content-heavy brief. (b) Cabinet Grotesk — assertive, fits landing page hero. (c) IBM Plex Sans — utilitarian, fits dashboard context. Brief is an editorial landing page, so (a) Söhne."*

This prevents the "two-deep attractor" problem: even when the agent rejects its first instinct, its second is usually also default.

---

## The Three-Layer Enforcement

A complete anti-pattern system has three layers. Each catches different failures.

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 3: Deterministic detector (CLI, linter, regex, vision)  │
│   • Runs without LLM                                          │
│   • Catches outputs that slipped past layers 1 and 2          │
│   • Fails build / blocks merge on match                       │
└──────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────┐
│ Layer 2: Slash-commands that wrap common checks              │
│   /audit runs detectors, reports P0-P3 findings               │
│   /polish applies design-system rules before shipping         │
└──────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────┐
│ Layer 1: Skill + anti-pattern reference file                  │
│   • Explicit list of forbidden patterns                       │
│   • Anti-attractor procedure in skill instructions            │
│   • Agent reads and enforces at generation time               │
└──────────────────────────────────────────────────────────────┘
```

Without Layer 3 you rely on the agent to police itself, which it often does not under context pressure. Without Layer 1 the detector is a pure lint — fails without teaching. Without Layer 2 the two ends do not connect through a discoverable interface.

### Impeccable as reference implementation

The impeccable.style project realizes this stack concretely:

- **Layer 1:** SKILL.md with 7 reference files (typography, color-and-contrast, spatial-design, motion-design, interaction-design, responsive-design, ux-writing). Each has explicit anti-patterns.
- **Layer 2:** 18 slash commands: `/audit`, `/critique`, `/polish`, `/distill`, `/clarify`, `/typeset`, `/layout`, etc.
- **Layer 3:** `npx impeccable detect` — 24 anti-pattern checkers using regex + Puppeteer. Runs standalone, returns JSON + exit code, no LLM involved.

The 24 detectors cover: AI slop (side-tab borders, purple gradients, bounce easing, dark glows) and general design quality (line length, cramped padding, small touch targets, skipped heading levels).

---

## Writing an Anti-Pattern Reference

An anti-pattern file has four sections per rule. This structure reads well to both the agent and a human reviewer.

```markdown
### IMP-TYPE-001: Do not use Inter or Roboto as brand typefaces

**Pattern:** Font-family declarations naming Inter, Roboto, system-ui, Arial, Helvetica as the primary brand face.

**Why it's an anti-pattern:** Inter was 2020's distinctive choice; by 2024 it was the
monoculture default. Using it now signals "AI-generated" or "no typography decision
made." Same for Roboto (post-Material Design default).

**Exceptions:**
- Utility copy in technical dashboards where readability trumps distinctiveness
- Codebase already uses Inter and changing is out of scope for this task

**Correct alternatives:** Söhne, Cabinet Grotesk, Pitch Sans, IBM Plex Sans,
Author, Söhne Mono, GT Walsheim, Roobert — pick one matching brief context.
```

Four things that make the rule work:

1. **Rule ID** (`IMP-TYPE-001`) so the agent can cite it in reasoning and the detector can reference it in output.
2. **Pattern description** with concrete markers the detector can match (font-family names, CSS properties, Unicode characters).
3. **Why** — short rationale that the agent reads and internalizes, not just "do not do this because I said so."
4. **Exceptions + alternatives** so the rule does not become a blanket ban that the agent has to contort around.

---

## Where This Applies Beyond Frontend

The same three-layer pattern works anywhere there is a detectable attractor.

### Security

OWASP Top 10 is an anti-pattern list for web apps. Impeccable's structure (rule ID + pattern + why + alternatives) maps directly. Our [10-agent-security.md](10-agent-security.md) is the corresponding reference for agent security — each "Attack Taxonomy" section is a named anti-pattern with detection guidance.

### Database queries

`SELECT *` in production, `N+1` queries, missing indices on join columns, `CASCADE DELETE` on user data. Detectable by explain plan analyzers + linters like [sqlfluff](https://sqlfluff.com/) + ORM query loggers.

### Dockerfiles

`FROM alpine:latest`, `RUN apt-get install` without `--no-install-recommends`, `COPY . .` before dependency install (cache bust), running as root without `USER` directive. Detectable by [hadolint](https://github.com/hadolint/hadolint).

### Python idioms

Mutable default arguments, bare `except:`, broad `Exception` catches, `==` for `None` check. Detectable by ruff / flake8 rules.

### Test code

Tests that do not actually assert, skipped tests without issue links, tests that mock the thing they claim to test. Detectable via our [safety-test-muting](https://github.com/AnastasiyaW/claude-code-config/blob/main/rules/safety-test-muting.md) hook pattern (extended to check for weak assertions).

### Architecture

Microservices for small apps, eventual-consistency for data that needs transactions, Kafka for low-throughput events. Harder to detect automatically — but the agent-level anti-attractor procedure still works: "Before proposing microservices, write the one-service version and explain why it is insufficient."

---

## Relationship to Other Principles

| Principle | How it connects |
|---|---|
| **01 Harness Design** | Layer 3 detectors are the Evaluator's deterministic half. The Evaluator uses them + LLM review, not LLM alone. |
| **02 Proof Loop** | Detector output is an unfakeable artifact: "build failed on rule IMP-COLOR-003" is evidence, not a claim. |
| **04 Deterministic Orchestration** | Shell Bypass Principle in practice. Mechanical checks go through scripts, not model reasoning. |
| **08 Skills Best Practices** | The reference-file structure (rule ID, pattern, why, alternatives) is the template for skill anti-pattern docs. |
| **10 Agent Security** | The Attack Taxonomy table IS an anti-pattern config. Same structure, different domain. |
| **22 Visual Context Pattern** | When showing designs visually, pair the display with anti-attractor checks in the reference skill so visible choices do not slide back to defaults. |

---

## Gotchas

- **Negative-only lists drift stale faster than positive guides.** If a rule says "do not use X," someone eventually ships X because the ban outlived the reason. Include the "why" so the rule can be retired when the reason is gone.
- **Anti-pattern rules must be exception-friendly.** An absolute ban breeds violations. "Do not use Inter *unless it is already in the codebase and migrating is out of scope*" is a stronger rule than "Do not use Inter."
- **Rule IDs must be stable.** If `IMP-TYPE-001` becomes `IMP-TYPOGRAPHY-001` in v2, every past skill citation breaks. Treat IDs like public API.
- **Detector false positives erode trust.** If `/audit` reports 40 findings on a clean file, people stop reading the output. Tune thresholds aggressively in year one; over-reporting kills adoption faster than under-reporting.
- **Anti-attractor procedure costs tokens.** The three-step "name / reject / enumerate" routine adds ~100 tokens per visible choice. For a complete page redesign with 20 choices, that is 2000 tokens. Budget for it.
- **Rules must be machine-readable.** A detector needs to match something. "Use distinctive typography" is not machine-readable; "font-family must not be Inter|Roboto|Arial|Helvetica|system-ui" is.

---

## Troubleshooting

### Agent picks anti-pattern default anyway
- **Symptom:** Output contains Inter despite anti-attractor rule.
- **Cause:** Anti-attractor procedure was not triggered. Either the skill was not loaded, or the rule was buried deep in the reference file and the agent did not read it in this task's context.
- **Solution:** Move the most critical anti-patterns to the skill description (layer 1 trigger surface). Add a `/polish` pre-commit step that re-runs the detector.

### Detector fails on legitimate exceptions
- **Symptom:** `npx impeccable detect` flags a design token that should be exempted.
- **Cause:** Anti-pattern rule has no exception clause for this context.
- **Solution:** Add exception to rule reference file; re-run detector. If exceptions multiply, the rule is mis-calibrated — revisit.

### Slash-command output overwhelms user
- **Symptom:** `/audit blog` returns 50 findings, user does not read.
- **Cause:** No severity filtering. Every rule contributes one finding at default severity.
- **Solution:** Bucket findings into P0/P1/P2/P3 severity. Default output shows P0+P1. `/audit --all` reveals the rest. See impeccable's P0-P3 convention.

---

## Minimum Viable Adoption

You do not need to fork impeccable to start. The minimum viable anti-pattern stack per project:

1. **One reference file** `docs/anti-patterns.md` with 5-10 rules in the format above.
2. **One detector script** `scripts/check-anti-patterns.sh` that greps / lints for those rules.
3. **One CLAUDE.md entry** pointing the agent to the reference and requiring the anti-attractor procedure on visible choices.

Scale up by adding more rules, adding slash commands that invoke the detector on demand, and adding the detector to CI. The full impeccable stack is the mature form; the minimum is three files.

---

## Sources

- [pbakaus/impeccable](https://github.com/pbakaus/impeccable)
- [impeccable website](https://impeccable.style/)
- [anthropic/skills/frontend-design (base skill)](https://github.com/anthropics/skills/tree/main/skills/frontend-design)
- [hadolint (Dockerfile linter)](https://github.com/hadolint/hadolint)
- [sqlfluff (SQL linter)](https://sqlfluff.com/)
- [ruff (Python linter, Rust-fast)](https://github.com/astral-sh/ruff)
