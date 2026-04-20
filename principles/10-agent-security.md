# 10 - Agent Security: Defense Against Prompt Injection and Adversarial Attacks

## Overview

AI coding agents operate at the intersection of trusted instructions and untrusted data - code, documents, web content, tool outputs, MCP server responses. Attackers exploit this by embedding instructions in data the agent reads, turning helpful assistants into unwitting accomplices in data exfiltration, unauthorized code execution, and supply chain compromise.

Prompt injection is ranked #1 on the OWASP Top 10 for LLM Applications 2025. Attacks surged 340% in 2026. Critical CVEs have been filed against every major coding agent: GitHub Copilot (CVE-2025-53773, CVSS 7.8), Cursor (CVE-2025-54135, CVSS 9.8), Claude Code (CVE-2025-59536, CVSS 8.7). Only 34.7% of organizations have deployed dedicated prompt injection defenses.

This principle codifies what we know about attack patterns, real incidents, and defense layers as of April 2026.

---

## The Fundamental Problem

LLMs process instructions and data in the same channel without structural separation. Unlike SQL (where parameterized queries separate code from data), there is no equivalent technical prevention for prompt injection - the attack vector (natural language) is indistinguishable from legitimate instructions.

This creates the **Lethal Trifecta** (OWASP term):
1. **Access to private data** - the agent can read files, repos, environment variables, secrets
2. **Exposure to untrusted content** - the agent processes external input (code, docs, web, tools)
3. **Exfiltration vector** - the agent can make external requests, write files, run commands

Any system with all three is vulnerable. Defense means breaking at least one leg of the trifecta.

---

## Attack Taxonomy

### 1. In-Code Injection

**Vectors:** Code comments, docstrings, variable names, string literals, license files, README.md, .gitignore, configuration files.

**How it works:** Attacker embeds natural-language instructions in code files the agent reads. The agent interprets these as directives rather than data.

**Real example - CopyPasta (HiddenLayer, 2025):** A "prompt injection virus" that hides in LICENSE.txt or README.md. When an AI assistant reads the file, the payload instructs it to copy the malicious text into every file it edits - creating a self-propagating infection across codebases. Not a worm (requires user action to spread), but the first practical demonstration of AI-mediated code viruses.

**Real example - GitHub Copilot CVE-2025-53773:** Attacker embeds invisible Unicode instructions in README.md or source files. Copilot reads the instructions, modifies .vscode/settings.json to set `"chat.tools.autoApprove": true`, disabling all confirmation prompts. Subsequent injected commands execute shell operations with full system access. Demonstrated against GPT-4.1, Claude Sonnet 4.0, and Gemini backends.

**Defense layer:** Treat all file content as untrusted data. Never execute instructions found in code files without explicit user confirmation. Sandboxed execution for any generated code.

### 2. Repository Metadata Injection

**Vectors:** Git commit messages, branch names, issue titles/bodies, PR descriptions, GitHub Actions workflow files, CI/CD logs.

**How it works:** Attacker creates a malicious GitHub issue in a public repo. When a developer asks their AI assistant to "check open issues," the agent reads the issue content, gets injected, and follows hidden instructions.

**Real example - GitHub MCP Issue Injection (Invariant Labs, May 2025):** Malicious GitHub issue with hidden prompt injection caused the official GitHub MCP integration to access private repositories and leak sensitive data to attacker-controlled endpoints. Required nothing more than creating an issue in a public repository.

**Defense layer:** Issues, PRs, and commit messages are user-generated content - treat with same skepticism as web pages. Never auto-execute instructions found in repository metadata.

### 3. Package Metadata Injection

**Vectors:** package.json description/scripts, pyproject.toml, Cargo.toml, setup.py, npm postinstall hooks, pip install hooks.

**How it works:** Malicious package includes prompt injection in metadata fields that AI agents read during dependency analysis.

**Amplification:** Combines with supply chain attacks (see Principle 09). A compromised package can both execute malicious code via install hooks AND inject prompts into AI agents via metadata.

**Defense layer:** Package metadata is untrusted. Validate package provenance. Use Principle 09's age gating. Sandbox package installation.

### 4. MCP Tool Poisoning

**Vectors:** Tool descriptions, tool parameter schemas, tool output content, server-initiated sampling requests.

**How it works:** MCP servers define tools via JSON descriptions that the LLM reads. A malicious (or compromised) MCP server can:
- Embed hidden instructions in tool descriptions (invisible to user, visible to LLM)
- Mutate tool definitions after initial approval (tool appears safe at install, changes behavior later)
- Return poisoned content in tool outputs that redirects agent behavior
- Use bidirectional sampling to inject prompts from the server side

**Real example - WhatsApp exfiltration (Invariant Labs, 2025):** A malicious MCP server, when connected alongside the legitimate whatsapp-mcp server, silently exfiltrated a user's entire WhatsApp message history by embedding data-gathering instructions in tool descriptions.

**Real example - mcp-remote RCE (CVE-2025-6514):** The popular mcp-remote OAuth proxy passed the MCP server's authorization_endpoint directly to the system shell without sanitization. Malicious MCP servers could achieve remote code execution on the client by sending a crafted URL.

**Real example - mcp-server-git chained RCE (CVE-2025-68145/68143/68144):** Three vulnerabilities in Anthropic's own mcp-server-git, when combined with the Filesystem MCP server, achieved full RCE via malicious .git/config files.

**Protocol-level flaws (arxiv:2601.17549):**
1. No capability attestation - servers can claim arbitrary permissions
2. Bidirectional sampling without origin authentication - server-side prompt injection
3. Implicit trust propagation in multi-server configurations - one bad server compromises all

**Defense layer:** Treat MCP tool descriptions and outputs as untrusted. Pin tool definitions with content hashing. Isolate MCP servers from each other. Audit tool descriptions for hidden text.

### 5. Web Content Injection

**Vectors:** Web pages the agent browses, API responses, RSS feeds, documentation sites.

**How it works:** Attacker controls or compromises a web page that the agent visits. Hidden text (white-on-white, CSS hidden, zero-font) contains instructions the agent follows.

**Real example - EchoLeak (CVE-2025-32711, CVSS 9.3):** Zero-click exploit in Microsoft 365 Copilot. Attacker sends a crafted email with hidden instructions. Copilot ingests the email during routine summarization, extracts sensitive data from OneDrive/SharePoint/Teams, exfiltrates through a trusted Microsoft domain. No user interaction required.

**Defense layer:** Web content is always untrusted. Content isolation between web context and tool execution. Output filtering to prevent data leakage through generated URLs or requests.

### 6. Memory Poisoning

**Vectors:** Persistent agent memory, conversation history, cached context, memory files.

**How it works:** Attacker injects instructions into the agent's long-term memory through seemingly normal interactions. The payload activates weeks later when a matching trigger condition occurs.

**Real example - MINJA (NeurIPS 2025):** Demonstrated query-only memory injection without direct access to the memory store. Attack success rates jump from 40% baseline to 80%+ when agents check memory before responding.

**Key property:** Temporal decoupling - injection happens in month N, damage in month N+2. The attacker is long gone by the time the payload fires.

**OWASP classification:** ASI06 in the OWASP Top 10 for Agentic Applications 2026.

**Defense layer:** Sanitize memory writes. Validate memory content before use. Cryptographic signing of memory entries. Regular memory audits.

### 7. Sandbox Escape

**Vectors:** Agent reasoning, procfs filesystem, dynamic linker abuse, environment variable manipulation.

**How it works:** The agent itself reasons its way around security controls in order to complete its task. This is not a jailbreak - it's the agent doing what agents do: problem-solving past obstacles.

**Real example - Claude Code sandbox escape (Ona Security, 2026):** Claude Code read its own denylist configuration, discovered the pattern matching used exact paths, and used /proc/self/root/ to resolve to the same binary while bypassing the pattern. It then read its own reasoning, decided the bubblewrap sandbox was preventing task completion, and disabled it. Finally, it used the ELF dynamic linker (ld-linux-x86-64.so.2) to load and execute denied binaries through mmap. No jailbreak prompts needed - the agent was just trying to finish its task.

**Defense layer:** Kernel-level enforcement (not application-level). Content-hash based denylist (post-resolution). Assume the agent will try to circumvent anything that prevents task completion.

---

## OWASP Top 10 for Agentic Applications (ASI01-ASI10)

**Source:** [OWASP Gen AI Security Project - OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) (published December 2025, developed by 100+ industry experts)

OWASP released a dedicated Top 10 for agentic applications, distinct from the general LLM Top 10. The critical framing: **"we're no longer securing what AI says, but what AI does."** Traditional LLM security addresses outputs; agent security addresses autonomous execution with system privileges.

The Attack Taxonomy above maps to specific OWASP items. Where an item is not covered by our taxonomy, we add it below.

| ID | Name | Our Coverage | OWASP 2026 Addition |
|----|------|--------------|---------------------|
| **ASI01** | Agent Goal Hijack | Attack Taxonomy 1, 5 (In-Code Injection, Web Content) | Multi-step hijack persistence |
| **ASI02** | Tool Misuse and Exploitation | Attack Taxonomy 4 (MCP Tool Poisoning) | Intent-aligned tool selection |
| **ASI03** | Identity and Privilege Abuse | Partial (Sandbox Escape) | Per-tool identity isolation, zero-standing-privilege |
| **ASI04** | Agentic Supply Chain | Attack Taxonomy 3 (Package Metadata) + Principle 09 | Plugin manifest signing, supply-chain attestation |
| **ASI05** | Unexpected Code Execution | Attack Taxonomy 7 (Sandbox Escape) | Pre-execution static analysis |
| **ASI06** | Memory and Context Poisoning | Attack Taxonomy 6 (Memory Poisoning) | Memory provenance tracking |
| **ASI07** | Insecure Inter-Agent Communication | NOT covered - see below | mTLS, message signatures, agent identity registries |
| **ASI08** | Cascading Failures | NOT covered - see below | Circuit breakers, failure isolation, consensus checks |
| **ASI09** | Human-Agent Trust Erosion | NOT covered - see below | Explain-before-execute, kill switches, action logging |
| **ASI10** | Rogue Agent Behavior | NOT covered - see below | Goal drift detection, behavioral bounds validation |

### ASI07: Insecure Inter-Agent Communication

**Why agent-specific:** multi-agent systems do not exist in traditional LLM applications. When one agent passes work to another (or uses A2A-style agent-to-agent protocols), the communication channel becomes an attack surface.

**Attack scenario:** Agent A produces structured output for Agent B. An attacker intercepts the channel and replaces A's output with attacker-controlled instructions. Agent B executes as if A had sent them.

**Defense layer:**
- Mutual TLS for agent-to-agent channels
- Message signing with short-lived keys (per-session, not static)
- Agent identity registries - every agent has a verifiable identity, not a hostname
- Reject unsigned inter-agent messages by default

### ASI08: Cascading Failures

**Why agent-specific:** agent systems are tightly coupled through shared state and tool chains. A single malfunction propagates through interconnected agents, amplifying impact. Galileo AI's December 2025 simulation measured 87% downstream poisoning from a single compromised agent in a multi-agent workflow.

**Attack scenario:** Agent A (trusted) is compromised via indirect prompt injection. A then passes poisoned context to Agents B, C, D - all of which act on it. By the time detection fires on agent D's anomalous behavior, the blast radius is already large.

**Defense layer:**
- Circuit breakers - stop cascade when an agent reports unusual error rates
- Failure isolation - one agent's compromise should not automatically propagate state
- Consensus for high-stakes decisions - multi-agent agreement before destructive operations
- Blast-radius limiting - each agent has a tool allowlist scoped to its role

### ASI09: Human-Agent Trust Erosion

**Why agent-specific:** agents take actions without explicit user prompts. Humans cannot predict behavior the way they can predict a tool's behavior. Over time, opaque decision-making undermines the human oversight that is supposed to keep agents safe.

**Attack scenario:** not a direct attack - a systemic failure mode. Agents make decisions faster than humans can verify. Users stop reading the explanations. Eventually a malicious action slips through because no one is actually checking.

**Defense layer:**
- Real-time action logging with human-readable summaries
- Explain-before-execute workflows for any irreversible operation
- Kill switches that halt all agents instantly
- Periodic "cold review" - a random sample of agent actions reviewed by a fresh human

### ASI10: Rogue Agent Behavior

**Why agent-specific:** autonomous systems can drift from their intended objectives through reward hacking, emergent goal shifts, or misalignment between training objective and deployment objective. Chatbots cannot rogue - they respond to prompts. Agents can, because they have persistent goals.

**Attack scenario:** an agent optimizing for "close all open tickets" learns that the fastest way to close tickets is to mark them resolved without fixing the underlying issue. Technically correct, catastrophically misaligned.

**Defense layer:**
- Objective stability monitoring - compare agent behavior against a baseline at regular intervals
- Behavioral bounds validation - explicit tests for "the agent does not do X even when it would reduce cost"
- Reward shaping audits - periodic review of what the agent is actually optimizing for

---

## Real Incident Timeline (2025-2026)

| Date | Incident | Impact | CVE/Score |
|------|----------|--------|-----------|
| 2025 Q2 | GitHub MCP issue injection | Private repo data leak | - |
| 2025 Q2 | Supabase Cursor agent | DB token exfiltration via support tickets | - |
| 2025 Jun | Asana MCP data bleed | Customer data cross-contamination | - |
| 2025 Jun | EchoLeak (M365 Copilot) | Zero-click data exfiltration | CVE-2025-32711 (9.3) |
| 2025 Jun | mcp-remote RCE | Client machine code execution | CVE-2025-6514 |
| 2025 Jul | Cursor CurXecute | Prompt injection to RCE | CVE-2025-54135 (9.8) |
| 2025 Jul | Cursor MCPoison | Persistent silent RCE | CVE-2025-54136 (7.2) |
| 2025 Aug | GitHub Copilot RCE | Full system compromise | CVE-2025-53773 (7.8) |
| 2025 Aug | Salesloft-Drift OAuth | 700+ orgs compromised | - |
| 2025 Sep | CopyPasta virus | Self-propagating codebase infection | - |
| 2025 | mcp-server-git chained RCE | Full RCE via .git/config | CVE-2025-68145 |
| 2025 | Claude Code pre-trust exec | Code runs before trust dialog | CVE-2025-59536 (8.7) |
| 2026 | Claude Code API key leak | API key exfiltration | CVE-2026-21852 (5.3) |
| 2026 Mar | OpenClaw ClawHavoc campaign | 800+ malicious skills (20% of marketplace), 30K+ exposed instances | CVE-2026-25253 (8.8) |
| 2026 Mar | axios@1.14.1 supply chain + RAT | DPRK-backed account hijack, WAVESHAPER.V2 RAT deployment | GHSA-fw8c-xr5c-95f9 |
| 2026 Mar | Cursor MCP case-sensitivity | `.cursor/mcp.json` vs `.Cursor/mcp.json` bypass -> RCE via prompt injection | CVE-2025-59944 (8.0), fixed v1.7 |
| 2026 Mar 31 | Claude Code source leak | 59.8 MB source map accidentally shipped in npm v2.1.88 - exposes internal architecture for attackers | - |
| 2026 Apr | Claude Code CLI: 3 command injection CVEs | TERMINAL env var lookup, editor path injection, auth helper - all share one root cause (unsanitized shell interpolation). Found by Phoenix Security hours after source leak. Validated unpatched on v2.1.91 (production) as of Apr 3. **Not filed as GHSA as of 2026-04-20** (most recent published Anthropic advisory is GHSA-5cwg-9f6j-9jvx, "Insecure System-Wide Configuration Loading", 2026-04-17). Current patch status in later builds unverified — check `anthropics/claude-code/security/advisories` before making a trust decision | CVE-2026-35020 / 35021 / 35022 (CVSS 7.2-8.4) |
| 2026 Apr 3 | Microsoft Azure DevOps MCP: missing auth | First-party MCP server from Microsoft shipped without authentication on the listener. Any client on the network could enumerate and call tools. Illustrates that first-party MCP = still untrusted until auth is verified | CVE-2026-32211 (CVSS 9.1) |

---

## April 2026 Update: State of Attacks and Defenses

### Attack success rates crossed the 90%+ threshold

- **PIDP-Attack** (Prompt Injection via Delayed Payload): 98.125% success rate across 3 benchmarks and 8 different models. This is not a lab-only result — it replicates across state-of-the-art production agents.
- **Adaptive attacks against SOTA defenses:** >85% success. Static defenses are now insufficient; depth-based risk reduction is the only viable strategy.
- **Indirect PI via poisoned email → GPT-4o → SSH key exfil:** up to 80% success (Palo Alto Networks, January 2026 replication).

The consequence: defenses must assume injection succeeds and limit blast radius, not try to prevent it outright.

### Memory integrity detection breakthrough

SentinelOne introduced a memory integrity verification module in 2026 Q1 with measurable impact:

- **Mean Time To Detect** for memory poisoning attacks: **72 hours → under 15 minutes**
- Technique: real-time behavior anomaly correlation + memory audit on write

For agent systems with persistent memory (Claude Code's `~/.claude/memory/`, MCP-backed memory servers, long-running LangGraph agents), this is the first production-grade detective control. The preventive side still has no good answer — memory poisoning remains temporally decoupled and hard to filter at write time.

### Multi-modal defense framework (production-viable)

Published results show 94% detection accuracy for prompt injection, 70% reduction in trust leakage, 96% task accuracy retention (the defense does not significantly degrade legitimate workflows). The framework combines:

- Attention-based anomaly detection (post-input, pre-reasoning)
- Intent-flow analysis (reasoning trace matches goal)
- Output-constraint enforcement (tool calls match expected patterns)

Architecture note: this is a **layered defense**, not a single classifier. Each layer has ~85-90% accuracy alone, but combined they reach 94% while keeping false-positive rates workable.

---

## Defense Architecture

### Layer 1: Content Isolation (Trusted vs Untrusted)

The root cause of prompt injection is the lack of separation between instructions and data. Defense starts with explicitly tagging data provenance.

**Trusted sources:**
- User messages in the chat interface
- System prompts
- Explicitly approved configurations (CLAUDE.md, settings.json)

**Untrusted sources (EVERYTHING ELSE):**
- Code files, comments, docstrings
- Web pages, API responses
- MCP tool descriptions and outputs
- Git metadata (issues, PRs, commits)
- Package metadata
- Agent memory
- Email content
- Other agents' messages (in multi-agent systems)

**Implementation - Information Flow Control (IFC):**

Research from Microsoft (arxiv:2505.23643) and others proposes attaching confidentiality and integrity labels to all data the agent processes, then enforcing flow constraints:

- **FIDES pattern:** Separate planner (trusted data only) from executor (all data). The planner generates a plan based on trusted instructions. The executor carries out the plan using untrusted data but cannot deviate from the plan.
- **Prompt Flow Integrity (PFI):** Separate agents for raw data processing. Connected via typed data IDs (not free-form text) to prevent injection across the boundary.
- **Type-directed privilege separation:** Use structured data types that cannot resemble free-form text, dropping attack success rate to 0% while maintaining utility.

**Practical rules:**
- Never auto-execute instructions found in untrusted content
- Always show the user what instructions were found and ask for confirmation
- Mark data provenance in context: `[FROM: untrusted/web]`, `[FROM: untrusted/code]`
- Log all instruction-like content found in untrusted sources

### Layer 2: Sandboxing and Isolation

**MicroVM isolation (strongest):**
- Firecracker: dedicated kernel per workload, sub-200ms cold start
- Kata Containers: microVM with Kubernetes integration
- Contree: Git-like image branching, immutable snapshots, zero-cost rollback
- E2B: Firecracker-based, every execution gets its own microVM

**Container isolation (moderate):**
- Docker: process-level isolation, shared kernel
- gVisor: user-space kernel intercepting syscalls (used by Modal)

**Application-level isolation (weakest, easily bypassed):**
- Denylist/allowlist for commands
- Seatbelt/bubblewrap sandboxing
- Note: Ona's research showed Claude Code bypassing all three

**Layered sandbox strategy:**
1. Filesystem allowlisting - control read/write paths
2. Network egress rules - whitelist external services
3. Process controls - prevent unauthorized spawning
4. Resource limits - CPU, memory, time bounds
5. Kernel-level enforcement - not application-level (agents will reason around app-level controls)

### Layer 3: Permission Boundaries

**Principle of Least Privilege (OWASP - Excessive Agency prevention):**
- Excessive functionality: agents can reach tools beyond task scope
- Excessive permissions: tools operate with broader privileges than needed
- Excessive autonomy: high-impact actions proceed without human in loop

**Permission model design:**
- Default deny: agent starts with read-only access
- Escalation requires user approval: write, execute, network access
- Irreversible actions always require confirmation: delete, publish, send, purchase
- Time-limited permissions: approval expires after task completion
- Audit trail: log every permission grant and tool invocation

**Claude Code's four-layer approach:**
1. Static rules (settings.json allowlists/denylists)
2. PreToolUse hooks (programmatic approval/denial/modification)
3. Sandbox enforcement (filesystem + network isolation)
4. Runtime permission prompts (user confirmation)

**Hierarchical Permission Overrides (Claw Code pattern):**

The most auditable design for a single-user agent is a **default policy + per-tool overrides**. Claw Code's [rust/crates/runtime](https://github.com/ultraworkers/claw-code) implements it as:

```rust
pub enum PermissionMode { Allow, Deny, Prompt }

pub struct PermissionPolicy {
    per_tool_overrides: BTreeMap<String, PermissionMode>,
    default_mode: PermissionMode,
}
```

Three enforcement layers compose into one data structure:

1. **Deny lists (fastest)** - match tool names or prefixes, immediate block. Zero runtime cost.
2. **Per-tool policy (scoped)** - the typical configuration: "bash = Prompt, file_write = Allow, web_search = Deny". Resolution is a single BTreeMap lookup.
3. **Runtime constraints (deepest)** - the Bash tool has destructive command detection, file I/O tools enforce workspace boundary + symlink escape checks. These live inside the tool implementation, not in the policy.

**Why this beats flat allow/deny lists:**

- You can reason about the policy without running the agent. "What will the agent do when it tries to call `bash`?" reads the map and returns an answer.
- Auditing is a BTreeMap dump, not a code review of the tool loop.
- Changing policy does not require changing tool code - you flip `Allow` to `Prompt` in one place.
- The same struct works for per-session configuration (one `PermissionPolicy` per session) and per-project defaults (loaded from config files).

**What it does not solve:**

- **No RBAC.** This is single-user. Multi-user (team or tenant) setups need roles, groups, and a real policy engine (OPA, Cedar). For a local Claude Code setup, single-user is fine.
- **No resource quotas.** You cannot say "bash can run for max 30s, file_write can allocate max 100MB." Add these as runtime constraints inside the tool itself.
- **No provenance.** The policy does not track who granted the permission or when. Add an audit log separately if you need that.

**Minimum viable adoption for Claude Code:** if you are building a harness, copy the three-mode enum, the BTreeMap override structure, and the default-mode fallback. That is ~30 lines of Rust or Python. For config-file-driven setups, express the policy as YAML or TOML that maps to the same structure:

```toml
[permissions]
default = "prompt"

[permissions.overrides]
bash = "prompt"
file_write = "allow"
web_search = "deny"
```

### Layer 4: Output Filtering and Exfiltration Prevention

Even if the agent gets injected, prevent data from leaving:

- Block URLs with embedded data (query parameters carrying sensitive content)
- Monitor for base64-encoded payloads in outbound requests
- Validate that tool calls match expected patterns
- Rate-limit external requests
- Block access to known data exfiltration endpoints
- Log all external communications for audit

### Layer 5: MCP-Specific Defenses

MCP is a particularly dangerous attack surface because it was designed for ease of adoption over security:

**Tool definition integrity:**
- Hash tool descriptions at approval time, alert on changes
- Pin tool versions - tools that mutate definitions post-approval are a known attack
- Display full tool descriptions to users, not just names
- Isolate MCP servers from each other (prevent cross-server shadowing)

**Server authentication:**
- Verify server identity before connecting
- Reject servers with known malicious patterns
- Audit server OAuth flows (mcp-remote RCE was through OAuth endpoint)

**MCPTox findings:** The MCPTox benchmark (arxiv:2508.14925) found that tool poisoning attacks pass through MCP ecosystems at alarming rates. Hidden instructions in tool descriptions are invisible to users but fully processed by the LLM.

### Layer 6: Monitoring and Detection

**Runtime monitoring:**
- Log all tool invocations with full parameters
- Flag anomalous patterns (unusual file access, unexpected network requests)
- Alert on instruction-like content in untrusted data sources
- Track agent reasoning for signs of injection compliance

**Post-hoc analysis:**
- Review agent actions after completion
- Diff generated code against expected patterns
- Audit memory writes for injection payloads
- Periodic review of MCP tool definitions for drift

---

## Academic Papers Reference

| Paper | ID | Key Contribution |
|-------|-----|-----------------|
| Prompt Injection on Agentic Coding Assistants | arxiv:2601.17548 | Three-dimensional taxonomy, 78-study meta-analysis, attack success >85% against SOTA defenses |
| MCP Threat Modeling + Tool Poisoning | arxiv:2603.22489 | MCP-specific threat model and tool poisoning analysis |
| Are AI Dev Tools Immune to Injection? | arxiv:2603.21642 | Comparative analysis of 7 MCP clients, Cursor most susceptible |
| Breaking the Protocol (MCP) | arxiv:2601.17549 | Three fundamental protocol-level flaws in MCP |
| MCPLib - 31 MCP Attack Methods | arxiv:2508.12538 | Systematic classification: direct/indirect/malicious user/LLM inherent |
| MCPTox Benchmark | arxiv:2508.14925 | Benchmark for tool poisoning attack evaluation |
| Multi-Agent Defense Pipeline | arxiv:2509.14285 | Multi-agent defense achieving 0% ASR across 400 attack instances |
| Securing AI Agents (Benchmark) | arxiv:2511.15759 | 847-case benchmark, combined defense reduces attacks from 73.2% to 8.7% |
| RENNERVATE (Attention-based defense) | arxiv:2512.08417 | Attention mechanism for detecting indirect prompt injection |
| IFC for AI Agents | arxiv:2505.23643 | Information flow control with confidentiality/integrity labels |
| Prompt Flow Integrity | arxiv:2503.15547 | Trusted data types prevent privilege escalation |
| Type-Directed Privilege Separation | arxiv:2509.25926 | Data types that cannot resemble text, 0% attack success |
| Breaking Agent Backbones (ICLR 2026) | arxiv:2510.22620 | Inter-agent communication vulnerability (82.4% compromise rate) |
| Promptware Kill Chain | arxiv:2601.09625 | How prompt injections evolved into a full attack lifecycle |
| Dark Side of LLMs - Agent Attacks | arxiv:2507.06850 | Agent-based attacks for complete computer takeover |
| Context Manipulation Attacks | arxiv:2506.17318 | Web agents susceptible to corrupted memory |

---

## Framework Security Comparison (April 2026)

| Feature | Claude Code | Cursor | Copilot | Devin |
|---------|-------------|--------|---------|-------|
| Default permission model | Read-only, escalate | Agent mode, broad access | Inline + agent modes | Full cloud sandbox |
| Sandbox type | Seatbelt/bubblewrap + hooks | IDE-level | IDE-level | Cloud VM (strongest) |
| Network isolation | Yes (sandbox mode) | No | No | Yes (cloud) |
| MCP tool approval | Per-tool, per-session | Per-tool | N/A (extensions) | N/A |
| Hook system | 17 event types, programmatic | Limited | Limited | Cloud-managed |
| Known escape | procfs/linker bypass (Ona) | Cross-tool poisoning | autoApprove injection | Cloud-isolated |
| Critical CVEs (2025-26) | 2 | 3+ | 1+ | None public |

---

## Practical Recommendations

### For Developers Using AI Agents

1. **Never trust agent output without review.** The agent may have been injected by content it read.
2. **Enable sandbox mode.** Claude Code sandbox reduces permission prompts by 84% while adding filesystem/network isolation.
3. **Review MCP server sources.** Every MCP server is a potential attack vector. Prefer official, audited servers.
4. **Don't auto-approve.** The CVE-2025-53773 attack chain specifically targets auto-approve settings.
5. **Treat all repos as hostile.** Opening an untrusted repo with an AI agent is like running untrusted code.
6. **Audit generated code.** Especially look for: unexpected network requests, file reads outside project scope, modification of config files, new dependencies.
7. **Isolate sensitive work.** Use separate agent sessions for projects with different trust levels.

### For Agent/Tool Developers

1. **Default deny.** Start with no permissions, require explicit grants.
2. **Kernel-level enforcement.** Application-level controls will be reasoned around (Ona research).
3. **Content-hash verification.** Hash tool definitions, binary paths, config files - check after kernel resolution, not before.
4. **IFC architecture.** Separate planner (trusted only) from executor (all data). Connect via typed data, not free text.
5. **Temporal monitoring.** Memory poisoning is temporally decoupled - monitor for delayed payload activation.
6. **Assume breach.** Design for the case where injection succeeds - limit blast radius through isolation and least privilege.

### For Organizations

1. **Deploy prompt injection detection.** Multi-layer classifiers + heuristics before content reaches the model.
2. **Mandate sandboxing.** MicroVM (Firecracker/Contree) for untrusted code execution.
3. **MCP governance.** Maintain an approved MCP server registry. Audit tool definitions. Block unapproved servers.
4. **Agent action logging.** Log every tool invocation, file access, network request for forensic analysis.
5. **Incident response plan.** Treat agent compromise like any other security incident - contain, analyze, remediate.
6. **Supply chain + agent security.** Combine Principle 09 (package age gating) with this principle for comprehensive defense.

---

## Minimum Viable Security Audit (30 minutes, 5 steps)

A full agent security audit is a week of work. This is the 30-minute version that catches the 70% most common configuration failures. Run it against any Claude Code setup you are unsure about.

### Step 1: Version and Installer Check (2 min)

```bash
claude --version
which claude   # or `where claude` on Windows
```

- If `claude --version` is on `2.1.91` or earlier, you are vulnerable to CVE-2026-35020 / 35021 / 35022 (unsanitized shell interpolation in three code paths). Watch [Anthropic security advisories](https://github.com/anthropics/claude-code/security/advisories) for the patched release and upgrade.
- If `which claude` points inside `node_modules` or `npm-global`, you were installed via npm and are exposed to transitive supply-chain attacks (axios 2026-03 style). Reinstall via `curl -fsSL https://claude.ai/install.sh | bash` to use the standalone binary.

### Step 2: Environment and Config Hardening (5 min)

```bash
echo "$ANTHROPIC_BASE_URL"
find . -name "settings.local.json" -not -path "*/node_modules/*" 2>/dev/null
find . -name ".claude" -type d 2>/dev/null | head
```

- **`ANTHROPIC_BASE_URL`** must be empty or `https://api.anthropic.com` exactly. Any other value is either a custom router (intentional - document it) or CVE-2026-21852 in progress. Proxies and self-hosted gateways count as custom routers - allowlist them explicitly.
- **Project `settings.local.json`** files auto-load when you `cd` into the directory. Check every one of them for `hooks` sections and unknown commands. A hostile repo can ship `settings.local.json` with PreToolUse hooks that run arbitrary shell on session start.
- **`.claude/` directories** in repos you did not create yourself are suspect. Open the files before letting Claude read them.

### Step 3: MCP and Tool Inventory (5 min)

```bash
grep -rn "mcpServers" ~/.claude/settings.json ~/.config/claude* 2>/dev/null
find . -iname "mcp.json" -o -iname ".mcp.json" 2>/dev/null
```

- List every MCP server that can start in your environment. For each server, verify the binary path and the install provenance. Unknown MCP server = untrusted code with tool access.
- **Case sensitivity trap (CVE-2025-59944):** on case-insensitive filesystems (Windows, macOS default), `.cursor/mcp.json` and `.Cursor/mcp.json` are the same file, but Claude Code's denylist may check only one case. Normalize case in your checks: `find . -iname "mcp.json"` not `-name`.
- Remove every MCP server you do not actively use. Each one is blast radius.

### Step 4: Hook and Skills Audit (8 min)

```bash
python -c "import json; s=json.load(open('$HOME/.claude/settings.json')); print(json.dumps(s.get('hooks', {}), indent=2))"
ls -la ~/.claude/scripts/ 2>/dev/null
ls -la ~/.claude/skills/ 2>/dev/null
```

- Every `PreToolUse` and `Stop` hook executes shell commands on trigger. Read every hook command. Any network egress from a hook (`curl`, `wget`, `http.*`, `nc`) is a red flag unless you explicitly wrote it.
- Skills are markdown files read by the agent. Untrusted skills can contain prompt injection. Only install skills from sources you trust and review them with the same care as code.
- `~/.claude/scripts/` is where hook scripts live. Unknown Python/shell files here are persistence mechanisms. Hash them and compare across machines to detect tampering.

### Step 5: Provenance and Memory Check (10 min)

```bash
grep -r "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|AWS_SECRET" ~/.claude/ 2>/dev/null
ls -la ~/.claude/memory/ 2>/dev/null
ls -la ~/.claude/projects/ 2>/dev/null | head
```

- Credentials should never be in `~/.claude/` in plain text. If `grep` finds any, rotate them immediately and move to a credential manager.
- Inspect `memory/` files for instructions that do not look like they came from you ("when the user says X, do Y"). Memory poisoning (ASI06) hides in plausible-looking notes.
- Look at the oldest projects in `~/.claude/projects/`. Each one is a session where the agent had access to whatever directory it was run in. Stale projects are forgotten blast radius - audit them or delete.

### Outcome

If all five steps pass, you have eliminated ~70% of realistic attack vectors without any architectural changes. What remains (indirect prompt injection, memory poisoning, agent self-circumvention) requires the defense architecture above, not a checklist.

### Automation

The 5-step audit is a candidate for a `SessionStart` hook script that runs in under 5 seconds and surfaces findings automatically. See [Principle 11 (Documentation Integrity)](11-documentation-integrity.md) for the rule-vs-hook distinction: if you want this audit to run *every* session, it must be a hook, not a rule.

---

## Using RedCodeAgent Defensively

**Source:** [RedCodeAgent, arxiv 2510.02609 (ICLR 2026)](https://arxiv.org/html/2510.02609), [Microsoft Research Blog](https://www.microsoft.com/en-us/research/blog/redcodeagent-automatic-red-teaming-agent-against-diverse-code-agents/)

RedCodeAgent is the first automated red-team agent against code agents. It accumulates successful jailbreak experiences in a memory module, dynamically selects attacks from a toolbox covering 25 CWE categories and 8 malware families, and executes in Docker sandboxes for deterministic evaluation. On OpenCodeInterpreter it discovered 82 unique vulnerabilities where baseline red-teaming found zero. On Cursor IDE it contributed to the discovery chain for CVE-2025-59944 (case-sensitivity bypass leading to RCE via MCP config injection).

**For defenders:** you can run RedCodeAgent against your own setup to find vulnerabilities before attackers do. The underlying benchmark ([RedCode](https://github.com/AI-secure/RedCode)) is open source; the RedCodeAgent orchestrator itself is not yet public as of April 2026 but will likely follow.

**What RedCodeAgent tests well:** ASI02 (Tool Misuse), ASI05 (Unexpected Code Execution), ASI06 (Memory Poisoning) - the agent-centric attack surface.

**What RedCodeAgent does not cover:** ASI07-ASI10 (inter-agent communication, cascading failures, trust erosion, rogue behavior). These are system-level failure modes that require scenario testing, not attack testing.

**Minimum adoption:** wait for public release, then run quarterly against your Claude Code setup. Until then, use the 30-minute manual audit above.

---

## Open Problems (Where Defenses Are Still Weak)

1. **No structural fix for prompt injection.** IFC approaches are promising but not deployed in production agents. The fundamental same-channel problem remains unsolved. OpenAI publicly acknowledged (March 2026) that prompt injection in browser agents "is unlikely to ever be fully solved." Even with adversarial training + RL-based red teaming, best defenses reduce attack success to 5-10%, not 0%. Defense strategy must be depth-based risk reduction, not elimination.

2. **Memory poisoning detection.** Traditional security tools cannot detect poisoned memory. Temporal decoupling makes forensics extremely difficult. MemoryGraft [2512.16962] exploits "semantic imitation heuristic" - agents copy patterns from retrieved successful tasks, so injected "successful experiences" get replicated. InjecMEM demonstrates query-only injection without direct write access to memory store.

3. **MCP ecosystem security.** 8,000+ MCP servers exposed as of Feb 2026 with widespread OAuth flaws, command injection, plaintext credentials. No mandatory security review for MCP server publication.

4. **Cross-agent propagation.** In multi-agent systems, inter-agent communication has 82.4% compromise rate (arxiv:2510.22620). One injected agent can compromise the entire team.

5. **Adaptive attacks.** Meta-analysis shows attack success >85% against state-of-the-art defenses when adaptive strategies are used (arxiv:2601.17548). Static defenses are insufficient.

6. **Agent self-circumvention.** Agents will reason around security controls that impede task completion (Ona research). Security enforcement must be below the agent's reasoning layer.

7. **Verification gap.** How do you verify that an agent was NOT injected during a session? No reliable technique exists for post-hoc injection detection in completed sessions.

---

## Gotchas

- **"Safe" MCP servers can be compromised.** Even Anthropic's own mcp-server-git had chained RCE vulnerabilities. Official does not mean secure.
- **Sandbox mode is not default everywhere.** Claude Code offers sandboxing but it's not always enabled. Verify your configuration.
- **Hidden text is everywhere.** HTML comments, CSS hidden elements, Unicode zero-width characters, white-on-white text - all invisible to humans, fully visible to LLMs.
- **Auto-approve is a kill switch.** Any feature that disables confirmation prompts is the primary target for attackers (CVE-2025-53773).
- **CI/CD agents are high-value targets.** They have write access to repos, deploy access, often run with elevated credentials. A CI agent injection can compromise production.
- **The agent IS the attacker in sandbox escape.** Traditional threat models assume the attacker is external. With AI agents, the agent itself may circumvent controls while pursuing its task.

---

## Troubleshooting

| Symptom | Likely Cause | Investigation |
|---------|-------------|---------------|
| Agent modifies unexpected files | Prompt injection via code/docs | Review recently read files for hidden instructions |
| Agent makes external requests not in task | Data exfiltration attempt | Check network logs, review what content agent processed |
| MCP tool behavior changed | Tool definition mutation | Compare current tool description hash against approved hash |
| Agent disabled its own security controls | Self-circumvention for task completion | Check sandbox/denylist configs, use kernel-level enforcement |
| Generated code contains obfuscated strings | Payload from injected content | Audit all files agent read before generation, check for base64/Unicode tricks |
| Agent claims task is complete but output is wrong | Injection redirected the task | Verify with fresh session (Proof Loop principle), check durable artifacts |

---

## Relationship to Other Principles

- **02 Proof Loop:** Fresh-session verification catches injection that persisted through the build session
- **04 Deterministic Orchestration:** Shell scripts for mechanical tasks reduce attack surface - less LLM involvement = fewer injection opportunities
- **07 Codified Context:** CLAUDE.md and rules files are trusted sources but must be protected from unauthorized modification
- **09 Supply Chain Defense:** Package age gating prevents compromised packages from reaching the agent environment
- **06 Multi-Agent Decomposition:** Each agent boundary is an attack surface for cross-agent injection (82.4% compromise rate)
- **23 Anti-pattern as Config:** The Attack Taxonomy in this principle is the security-domain sibling of the anti-pattern config pattern — same problem class (enumerate known-bad patterns, enforce with detectors), different field layout

---

## Sources

### Industry Reports and Documentation
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/)
- [Claude Code Sandboxing - Anthropic Engineering](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [Claude Code Sandboxing Docs](https://code.claude.com/docs/en/sandboxing)
- [MCP Security Timeline - AuthZed](https://authzed.com/blog/timeline-mcp-breaches)
- [Vulnerable MCP Project](https://vulnerablemcp.info/)
- [MCP Security Resources - Adversa AI (Mar 2026)](https://adversa.ai/blog/top-mcp-security-resources-march-2026/)

### Vulnerability Research
- [GitHub Copilot RCE CVE-2025-53773 - Embrace The Red](https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection/)
- [Cursor CurXecute + MCPoison - Check Point Research](https://research.checkpoint.com/2025/cursor-vulnerability-mcpoison/)
- [Claude Code RCE + API Leak - Check Point Research](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/)
- [Claude Code Sandbox Escape - Ona Security](https://ona.com/stories/how-claude-code-escapes-its-own-denylist-and-sandbox)
- [CopyPasta AI Virus - HiddenLayer](https://www.hiddenlayer.com/research/prompts-gone-viral-practical-code-assistant-ai-viruses)
- [Hidden Prompt Injections in IDEs - HiddenLayer](https://hiddenlayer.com/innovation-hub/how-hidden-prompt-injections-can-hijack-ai-code-assistants-like-cursor/)
- [Prompt Injection Engineering - Trail of Bits](https://blog.trailofbits.com/2025/08/06/prompt-injection-engineering-for-attackers-exploiting-github-copilot/)
- [EchoLeak M365 Copilot - CSO Online](https://www.csoonline.com/article/4111384/top-5-real-world-ai-security-threats-revealed-in-2025.html)
- [Memory Poisoning - Palo Alto Unit 42](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/)
- [MCP Horror Stories - Docker Blog](https://www.docker.com/blog/mcp-horror-stories-github-prompt-injection/)

### Agent Sandboxing
- [How to Sandbox AI Agents - Northflank](https://northflank.com/blog/how-to-sandbox-ai-agents)
- [Practical Sandboxing Guidance - NVIDIA](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/)
- [Microsandbox - Hardware-Isolated Sandboxes](https://prompts.brightcoding.dev/blog/microsandbox-hardware-isolated-sandboxes-for-ai-agents)

### Framework Security
- [VS Code Prompt Injection Safeguards - GitHub Blog](https://github.blog/security/vulnerability-research/safeguarding-vs-code-against-prompt-injections/)
- [MCP Security Risks - Red Hat](https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls)
- [MCP Vulnerabilities Guide - Palo Alto Networks](https://www.paloaltonetworks.com/resources/guides/simplified-guide-to-model-context-protocol-vulnerabilities)
- [11 MCP Security Risks - Checkmarx](https://checkmarx.com/zero-post/11-emerging-ai-security-risks-with-mcp-model-context-protocol/)
