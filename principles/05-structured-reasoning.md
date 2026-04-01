# 05 - Structured Reasoning Protocol

**Source:** [2603.01896] Agentic Code Reasoning (Mar 2026)

## Overview

For complex tasks -- debugging, architecture decisions, optimization, security review -- free-form chain-of-thought reasoning is unreliable. Models build plausible but incorrect reasoning chains ("planning hallucinations"). The Structured Reasoning Protocol replaces free-form thinking with a semi-formal framework that forces explicit tracking of what is known, what was observed, what follows logically, and what was ruled out.

**Key finding from the paper:** Structured prompting consistently outperforms free-form reasoning for code-related tasks. The structure itself prevents the most common reasoning failures. Paper v2 results: accuracy 78% → 93% on real-world agent-generated patches (patch equivalence verification, fault localization, code QA).

---

## The Four Steps

### Step 1: Premises

**What we know for certain.** Facts drawn from code, logs, tests, documentation -- not assumptions or hypotheses.

Each premise must be:
- **Sourced** -- where did this fact come from? (file:line, log entry, test output)
- **Verifiable** -- another agent could confirm this fact independently
- **Current** -- not stale information from a previous state

#### Example

```
PREMISES:
P1: auth.ts:47 -- login() calls validateToken() before checking session
    Source: code inspection
P2: Test log shows validateToken() returns null for token "abc123"
    Source: test-output.txt line 203
P3: validateToken() uses RS256 algorithm (auth.config.ts:12)
    Source: code inspection
P4: The JWT library version is 4.2.1 (package.json)
    Source: dependency file
```

**Common failure:** Listing assumptions as premises. "The token should be valid" is not a premise -- it is a hypothesis. Only verifiable facts qualify.

### Step 2: Execution Trace

**Step-by-step tracing of control flow and data flow.** Walk through the code path or process that leads to the observed behavior.

The trace must follow:
- **Control flow** -- which functions call which, which branches are taken
- **Data flow** -- what data enters each function, what it returns, how it transforms

#### Example

```
EXECUTION TRACE:
T1: Client sends POST /login with {email, password}
T2: router dispatches to loginHandler() (routes.ts:23)
T3: loginHandler() calls validateCredentials(email, password)
T4: validateCredentials() queries DB, returns user object (user.id=42)
T5: loginHandler() calls createSession(user)
T6: createSession() calls generateToken(user) -- GENERATES JWT
T7: generateToken() uses RS256 with KEY_A (from env SECRET_KEY)
T8: Token returned to client in response body
T9: Client sends GET /dashboard with Authorization: Bearer <token>
T10: authMiddleware() calls validateToken(token)
T11: validateToken() uses RS256 with KEY_B (from env VERIFY_KEY)  <-- DIFFERENT KEY
T12: RS256 verify fails because KEY_A != KEY_B
T13: validateToken() returns null
T14: authMiddleware() rejects request with 401
```

**Common failure:** Skipping steps or assuming intermediate behavior. The trace must be explicit about every state transition.

### Step 3: Conclusions

**What follows logically from the premises and trace.** Each conclusion must be derivable from specific premises and trace steps.

#### Example

```
CONCLUSIONS:
C1: Authentication fails because signing key (SECRET_KEY) differs from
    verification key (VERIFY_KEY).
    Derived from: T7 (signs with KEY_A from SECRET_KEY) + T11 (verifies with
    KEY_B from VERIFY_KEY) + T12 (verification fails)

C2: This is a configuration error, not a code bug. The code correctly uses
    RS256 for both signing and verification.
    Derived from: P3 (RS256 configured) + T7/T11 (both use RS256)

C3: Fix: ensure SECRET_KEY and VERIFY_KEY contain the same RSA key pair
    (private for signing, public for verification) or use the same
    symmetric secret.
    Derived from: C1 + C2
```

**Common failure:** Drawing conclusions not supported by the premises and trace. Every conclusion must cite its supporting evidence.

### Step 4: Rejected Paths

**Hypotheses that were considered and ruled out, with the reason for rejection.** This is the most important step for preventing repeated work and circular debugging.

#### Example

```
REJECTED PATHS:
R1: "Token is expired"
    Rejected because: Token was just generated (T6-T8) and checked
    immediately (T9-T11). Expiration is set to 24h (P3 config check).

R2: "JWT library bug"
    Rejected because: Library version 4.2.1 is current (P4), and the
    verify function works correctly when given matching keys (manual test
    with same key for sign+verify succeeds).

R3: "CORS or header issue preventing token transmission"
    Rejected because: T10 shows validateToken() receives the token
    (it returns null, not "token missing"). The token arrives; it just
    fails verification.
```

**Why this matters:** Without rejected paths, the next debugging session (or the next person) will re-investigate the same hypotheses. Documenting rejections with reasons saves that wasted effort.

---

## Template

```markdown
## Structured Reasoning: [Problem Description]

### Premises
- P1: [fact] (source: [file:line / log / test])
- P2: [fact] (source: [file:line / log / test])
- ...

### Execution Trace
- T1: [step]
- T2: [step]
- ...
- Tn: [anomaly or result]

### Conclusions
- C1: [conclusion] (derived from: P#, T#)
- C2: [conclusion] (derived from: C1, T#)
- ...

### Rejected Paths
- R1: "[hypothesis]" -- rejected because: [reason citing P#/T#]
- R2: "[hypothesis]" -- rejected because: [reason citing P#/T#]
- ...
```

---

## When to Apply

### Good fit

| Situation | Why structured reasoning helps |
|---|---|
| **Debugging with non-obvious root cause** | Forces systematic tracing instead of guessing |
| **Architecture decisions with >2 options** | Makes trade-offs explicit and comparable |
| **Performance optimization** | Traces data flow to identify actual bottlenecks |
| **Security review** | Systematically traces attack surfaces and trust boundaries |
| **Incident post-mortems** | Documents the reasoning chain for future reference |

### Not needed

| Situation | Why not |
|---|---|
| Simple CRUD operations | The reasoning is obvious; structure adds overhead |
| Single-file changes with clear requirements | No ambiguity to resolve |
| Well-understood patterns (add a route, update a schema) | Experienced developer knowledge suffices |
| Tasks where the solution is known and just needs implementation | Reasoning is about finding the solution, not implementing it |

---

## Common Anti-Patterns

### 1. Premise contamination

Mixing hypotheses with facts. "The database is probably slow" is not a premise. "Query X takes 3.2 seconds (from slow_query_log)" is a premise.

### 2. Trace gaps

Skipping from T3 to T7 because "the middle is obvious." The middle is where bugs hide. Trace every step, especially the "obvious" ones.

### 3. Conclusion leaps

Drawing conclusions not supported by the chain. "We should rewrite the auth module" does not follow from "the keys are misconfigured." The conclusion should match the scale of the evidence.

### 4. Missing rejections

Not documenting what was ruled out. This is the most commonly skipped step and the most valuable for preventing wasted future work.

---

## Relationship to Other Principles

| Principle | Relationship |
|---|---|
| **Harness Design (01)** | The evaluator can use structured reasoning to produce more reliable quality assessments |
| **Proof Loop (02)** | Structured reasoning output becomes evidence in the proof loop -- the reasoning chain is a durable artifact |
| **Deterministic Orchestration (04)** | Structured reasoning is for the reasoning steps; deterministic orchestration handles the mechanical steps that feed premises into the reasoning |
| **Codified Context (07)** | Completed reasoning documents (especially Rejected Paths) become codified context for future sessions |
