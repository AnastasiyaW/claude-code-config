# Updates

Changelog for claude-code-skills. Newest first.

---

## 2026-04-17 (KB enforcement pattern + drop-in skeleton)

### New: principles/21-knowledge-base-enforcement.md

The pattern **review finding -> regression test -> invariant -> cross-reference** as a durable triangle. Every accepted review finding gains three forms (fix, test, invariant); missing any form loses a guarantee.

Covers structure (`AGENTS.md` + `docs/kb/` tree), the three forms concretely, validator role, bidirectional review-template cross-link, when-to-adopt criteria, and real numbers from a Phase 2 security sweep (123 findings -> 25 fixes -> 65 regression tests -> 25 invariants).

### New: templates/kb-skeleton/

Drop-in starter for the pattern. Copy into any repo, configure the top of `scripts/validate_kb.py`, start growing `INVARIANTS.md` from your first review.

Contains:
- `AGENTS.md` -- AAIF-standard entry, `<=150` lines, TODO markers
- `docs/kb/README.md` -- meta-rules (how to use, when to update)
- `docs/kb/INVARIANTS.md` -- format + example block
- `docs/kb/conventions.md` -- section stubs (imports, async, errors, types, ...)
- `docs/kb/patterns.md` -- recipe skeleton
- `docs/kb/gotchas.md` -- symptom/cause/workaround skeleton
- `docs/kb/decisions.md` -- ADR template
- `docs/kb/modules/example.md` -- per-module contract template
- `scripts/validate_kb.py` -- working validator, configurable `SOURCE_ROOTS` at top, multi-root path resolver, `(future)` / `(planned)` markers honored, stdlib-only, ASCII-safe output
- `.github/workflows/kb.yml` -- CI gate

Adoption time: ~15 minutes. First invariant can be added in under 5 minutes.

### Why this exists

Previous principles **07 - Codified Context** set the mindset ("context is infrastructure"). **11 - Documentation Integrity** generalized reference-validation-at-session-start. Principle 21 bridges the two with a concrete, adopt-able structure for projects that want the full loop from review to durable contract.

---

## 2026-04-17 (Humanize Russian: 80/20 term russification rule)

### Updated: skills/writing/humanize-russian/SKILL.md

Added new section "Русификация терминов - правило 80/20" between stylistic markers and conversational elements.

**Rule:** in Russian text, 80% of technical terms should be written as Russian words or transliterations, not left as English. Persistent English terms in Russian prose are a strong signal of machine translation or LLM generation.

**Detection mechanics:** native Russian speakers think "интерфейс" or "чекпоинт" first, then "UI" / "checkpoint". LLMs go the other way - the English term is the first statistical choice, so it stays untranslated. Output reads like a translation, not an original.

**Replacement table** (20+ terms): UI→интерфейс, checkpoint→чекпоинт, backup→бекап, deploy→развернуть/выкатить, workflow→пайплайн/процесс, pipeline→пайплайн, cache→кэш, cluster→кластер, node→нода/узел, retention policy→политика хранения, etc.

**Keep in English (20%):** library/brand names (PyTorch, MinIO, ControlNet, LoRA), standard acronyms (API, JSON, GPU, CPU, SSD), code and commands.

**Composition rule:** no more than 1-2 non-russified English terms per sentence (excluding library/brand names).

Checklist updated with two new items.

Trigger: caught in an actual HR response draft - "обучила сотрудников UI" vs the natural "обучила сотрудников работе с интерфейсом". The first reads as translated, the second as native.

---

## 2026-04-17 (Humanize skills: add vague intensifiers)

### Updated: skills/writing/humanize-russian/SKILL.md + humanize-english/SKILL.md

Added vague-intensifier LLM markers to Tier 1 banned words:

- **Russian:** "кардинально / кардинальное / кардинальный" - usage without a measured scale. LLM loves these as universal amplifiers; humans name the scale with a number or concrete word ("в разы", "вдвое", "на 40%").
- **English parallel:** "dramatically / significantly / drastically / substantially" - same failure mode. Replace with a concrete number or plain "fast/big/huge".

Both skill checklists updated accordingly.

Trigger: caught the pattern in actual production writing - an LLM draft used "кардинально эффективнее" / "кардинальная экономия" as stand-ins for what should have been "в ~8x быстрее" / "экономия на железе". The vague intensifier is a reliable AI signature because it optimizes for "sounds impressive" while specifically removing the measurement humans include when they know the scale.

---

## 2026-04-16 (v2.9.0 - Security Tooling Guide)

### Added: references/security-tooling-guide.md

Practical guide to all available security tools for Claude Code:
- **Anthropic /security-review** - install and usage (command + GitHub Action)
- **Trail of Bits Skills** - 16 security-focused plugins from the 38-plugin marketplace (static-analysis, variant-analysis, entry-point-analyzer, fp-check, constant-time-analysis, zeroize-audit, supply-chain-risk-auditor, etc.)
- **sast-skills** - 14-module SAST workspace pattern
- **Our tools** - plan-swarm-review code mode + vulnerability KB

Includes recommended pipelines for quick (1 min), standard (5-10 min), deep (30-60 min), and multi-session (1-2 hrs with mclaude) security audits.

---

## 2026-04-16 (v2.8.0 - Vulnerability Knowledge Base)

### Added: skills/architecture/plan-swarm-review/references/vulnerability-kb.md

Condensed CWE Top 10 detection heuristics for agent consumption during `/plan-swarm-review` code mode. Each CWE entry: triggers, taint flow, false positive indicators. Covers: XSS, SQL injection, OOB write/read, use-after-free, file upload, deserialization, SSRF, integer overflow, resource consumption.

Plan-swarm-review SKILL.md updated to reference this KB during code mode reviews.

Based on Vul-RAG approach (ACM TOSEM 2025): knowledge-level entries outperform code-level RAG by +16-24% accuracy.

Full Vul-RAG entries (10 articles with code examples, root cause analysis, fixing patterns): published to knowledge-vault/docs/security/cwe/ for happyin.space deployment.

---

## 2026-04-16 (v2.7.0 - Vulnerability Detection Pipeline)

### Added: principles/20-vulnerability-detection-pipeline.md

New principle formalizing the 6-layer AI vulnerability detection pipeline: SAST scan -> LLM false-positive filter -> multi-agent diverse review -> knowledge-enriched RAG -> adversarial verification -> sandbox PoC.

Backed by 15 papers and production evidence:
- Claude Opus 4.6: 500+ confirmed zero-days in OSS (Anthropic, Feb 2026)
- SAST-Genius: hybrid SAST+LLM reaches 89.5% precision vs 35.7% SAST alone
- MAVUL: +600% detection vs single-agent
- Vul-RAG: knowledge-level RAG adds +16-24%, found 6 CVE in Linux kernel
- Chinese ecosystem: Qianxin #1 CyberSec-Eval, DeepAudit 48 CVE, Tencent A.S.E framework

Includes practical implementation guide for Claude Code (built-in + skills), comparison of LLM strengths/weaknesses by vulnerability type, and references to Trail of Bits Skills and sast-skills.

---

## 2026-04-16 (v2.6.0 - Plan Swarm Review)

### Added: skills/architecture/plan-swarm-review/SKILL.md

New skill for iterative plan/code review using multisampling + focused decomposition. Inspired by deksden's "Plan Swarming" technique (April 2026) and backed by 5 academic papers.

**Two modes:**
- **Plan mode**: review design docs, specs, ADRs before implementation
- **Code mode**: security audits, vulnerability hunting, bug detection

**4 escalating rounds:**
1. Broad review (single agent) - catch obvious issues
2. Diverse multisampling (3-5 agents with different personas) - stochastic diversity
3. Focused decomposition (one agent per aspect) - deep analysis
4. Focused + multisampling (optional) - maximum depth

**Key research-backed improvements over naive multisampling:**
- Diverse perspectives instead of identical prompts ([2502.11027]: +10.8% reasoning accuracy)
- Minority-correct finding preservation ([2602.09341] AgentAuditor: recovers 65-82% of findings majority voting misses)
- Code vulnerability aspects based on MultiVer [2602.17875] (82.7% recall) and VulAgent [2509.11523] patterns

**Empirical result** (deksden): 36 agent runs found ~30+ issues that a 2-3 hour single-agent planning session missed entirely.

---

## 2026-04-15 (v2.5.0 - Reasoning regression debugging)

### Added: alternatives/reasoning-regression-debugging.md

Full playbook for detecting and mitigating agent reasoning-quality regression. Based on the Stella Laurenzo (AMD) investigation of the Feb-Apr 2026 Claude Code degradation ([issue #42796](https://github.com/anthropics/claude-code/issues/42796)), which analyzed 6,852 sessions and Boris Cherny's Hacker News response with official workarounds.

Five approaches compared:
- **A: Config reset** - `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1`, `MAX_THINKING_TOKENS=32000`, `/effort high`/`max`, `ULTRATHINK` keyword, settings.json options
- **B: Stop-phrase guard hook** - blocks session end on five phrase categories (ownership dodging, permission-seeking, premature stopping, known-limitation labeling, session-length excuses)
- **C: Metric monitoring** - weekly Read:Edit ratio, Research:Mutation ratio, Edits-without-prior-Read %, loop rate, user-interrupt rate, write%
- **D: Fresh-session A/B** - minimal-context comparison to isolate vendor vs user-side regression
- **E: Proof Loop** (principle 02) - structural immunity to regression via fresh-session verifier

Full effort scale reference (0/30/85/95/100), complete list of environment variables and settings.json options, phrase categories with representative patterns, decision matrix for when to use which approach.

### Added: hooks/stop-phrase-guard.py

Implements approach B from the alternatives doc. Scans the final assistant message from the Stop hook's transcript input against five regex-grouped phrase categories. Uses meta-discussion markers to suppress false positives on legitimate anti-pattern references. Touches `.claude/.stop-phrase-guard-fired` marker to avoid re-blocking same session.

### Added: scripts/reasoning_metrics.py

Computes all six regression metrics from `~/.claude/projects/*.jsonl` session files. Supports `--days N` lookback, `--project` filter, `--json` / `--csv` output modes, per-session plus median-aggregated summary with healthy/transition/degraded status flags.

**First-run validation:** when run against our own last 7 days of sessions, the script produced Read:Edit ratio = 2.0 (exact number from the AMD investigation's degraded population), Research:Mutation = 1.05, Write% = 42.9%. The tool works and confirms the regression is affecting our own workflow. Remediation via approach A applies.

### Updated: principle 02 (Proof Loop) - added regression case study

The principle now includes a "Why this matters: the April 2026 regression case study" subsection explaining why Proof Loop is structurally immune: the fresh-session verifier does not care whether the builder's reasoning was sharp, only whether evidence proves the AC. Output quality becomes bounded by the spec, not by the model's current capacity. Cross-links to the new alternatives doc for cases where full Proof Loop is too heavy.

### Updated: indexes

- `README.md`: added stop-phrase-guard to hooks table, added reasoning-quality-regression to alternatives table
- `HOW-IT-WORKS.md`: added reasoning_metrics.py to scripts table
- `hooks/README.md`: added session-handoff-check and stop-phrase-guard to Session Management table with full descriptions

---

## 2026-04-15 (v2.4.0 - Inter-Agent Communication principle)

### Added: Principle 19 - Inter-Agent Communication

Directed asynchronous messaging between parallel Claude sessions. Complements principle 18 by adding the directed-messaging layer on top of the shared-state substrate: where 18 covers ownership (nouns - who holds what), 19 covers messaging (verbs - who tells whom).

- `principles/19-inter-agent-communication.md` - full pattern:
  - Two coordination axes (broadcast vs directed) × two primitives (shared state vs messages) = four total coordination patterns; principle 18 covers the shared-state row, principle 19 covers the messages row
  - Why classical mail semantics specifically: SMTP/IMAP survived 40 years solving exactly this problem (async point-to-point with delivery guarantees between parties that may never be online simultaneously)
  - Minimal implementation: file-based mailbox with inbox/sent/archive per recipient + `all/` for broadcast
  - Message format with email-style frontmatter (from, to, subject, message_id, in_reply_to, date, status)
  - Decision tree: handoff vs lock vs directed mailbox vs broadcast mailbox
  - Anti-patterns: polling on every tool call, editing another agent's sent folder, using mailbox for long-term state, no threading, bad agent names
  - Prior art: aydensmith/mclaude, existing alternatives/agent-mailbox-system.md, SMTP/IMAP reference, Erlang process mailboxes

### Extended: alternatives/agent-mailbox-system.md

The original doc (April 12) covered basic send/receive/broadcast. Production surfaced gaps - threading confusion, no sender audit trail, no delivery confirmation. Added classical mail extensions:

- Threading via `message_id` + `in_reply_to` + `references` headers (format: `YYYYMMDD-HHMMSS-<sender>-<seq>`)
- Sent folder: copy every outgoing message to `mailbox/<sender>/sent/` for sender audit trail
- Delivery receipts: two levels (status update on the inbox copy, or explicit receipt message)
- Filter rules: `.filter.yaml` per mailbox for auto-triage by sender/subject
- Reply-to header for cases where reply target differs from sender
- Maintenance commands: archive messages >14 days, delete old receipts
- Mailbox-specific data loss rules (atomic writes, unique message_id, sender-scoped sequence for strict order)
- Frontmatter `related_principles: [19]` + `last_reviewed: 2026-04-14` for the freshness audit

### Updated indexes

- `README.md`: 18 → 19 in 3 places (English, 中文, Russian), added principle 19 to bulleted list, added mini decision tree in handoff section for "which coordination primitive"
- `AGENTS.md`: 18 → 19
- `principles/README.md`: 18 → 19, full entry for principle 19, 3 decision-matrix rows added (ask another session, broadcast architecture decision, delivery confirmation)
- `HOW-IT-WORKS.md`: new "Inter-Agent Mail" section with concrete mechanism + production validation from retouch-app
- `CLAUDE.md`: added "Inter-Agent Communication" summary section for global config

### Composition

Principle 18 + principle 19 together close the multi-session coordination picture. Principle 18 asks "who owns what state"; principle 19 asks "who is talking to whom". Using both, parallel Claude sessions can:
- Leave durable handoffs for future sessions (broadcast, append-only)
- Claim exclusive resources with heartbeat-based lifecycle (mutex)
- Send targeted requests or questions to specific other sessions (inbox)
- Broadcast decisions everyone needs to know (`mailbox/all/`)

---

## 2026-04-14 (v2.3.4 - HOW-IT-WORKS expanded with 3 more deep-dives)

### Added: Proof Loop, Autoresearch, Documentation Integrity sections in HOW-IT-WORKS.md

The "humans-friendly technical deep-dive" file covered Rules, Memory, Handoffs, Hooks, KV-Cache, Context Fill, Chronicles, Skills, Supply Chain, and Multi-Session, but three of the most important principles had no technical explainer:

- **Proof Loop** - why the agent cannot sign its own completion. Explains the 4-role protocol (Spec-freezer / Builder / Verifier / Fixer), fresh-session verification, durable artifacts vs claims, and the anti-fabrication verify-after-action rule.
- **Autoresearch** - iterative self-optimization mechanics. Covers the 5-step READ-CHANGE-TEST-DECIDE-REPEAT loop, the 3 preconditions (numerical score / automated eval / single-file mutation), git-as-memory, guard mechanism with 3-6 binary assertions, CORAL heartbeat for stagnation, and HyperAgent upgrade path via Contree microVMs.
- **Documentation Integrity** - how SessionStart hook catches drift before the agent acts on stale paths. Explains multi-strategy path resolution, the rule-vs-hook distinction ("rules are hopes, hooks are executions"), and the Rust compile-time analogy for why validation at session start beats post-failure detection.

Each section follows the same structure as existing deep-dives: problem statement, mechanism, concrete details, links to the full principle file. Meant for readers who read README and thought "okay but HOW does this work mechanically?"

---

## 2026-04-14 (v2.3.3 - Principle 18 coverage audit)

### Fixed: principle 18 was silently missing from most index files

After adding principle 18 (Multi-Session Coordination) in v2.3.0, the counts and references across the repo lagged:

- `README.md`: still said "17 principles" in 3 places (English heading, 中文 and Russian sections, Structure list), and the principle-by-problem bulleted list didn't include 18
- `AGENTS.md`: referenced "17 principles"
- `principles/README.md`: said "collection of 17 battle-tested principles", had no entry for principle 18 at all, and missed decision-matrix rows for multi-session scenarios
- `HOW-IT-WORKS.md`: had no technical deep-dive section for the new principle, and the scripts table was missing the new cross-reference checker

All fixed in this release. Principle 18 now appears:
- Counted in all three language sections of README.md
- Listed in the "What This Gives You" bulleted principle list
- Full entry in `principles/README.md` with two decision-matrix rows
- Technical section in `HOW-IT-WORKS.md` explaining append-only vs mutable shared state with the Anthropic `.claude.json` corruption incident as cautionary data
- Brief mention in `CLAUDE.md` (global config summary)

### Root cause

When a principle is added, there is no automated check that "every principle is counted in every index". The `cross_reference_check.py` script catches broken links and numbering gaps, but a lagging count like "17" when the reality is 18 reads as valid prose. Added this class of drift as an open concern in MAINTENANCE.md red-flags section.

Extended the script immediately with `check_principle_count_claims`: counts `principles/NN-*.md` files and greps index files (README, AGENTS, principles/README, CLAUDE, MAINTENANCE, HOW-IT-WORKS) for claims like "N principles" / "N принципов" / "N 个架构原则" / "N battle-tested principles" - any mismatch is an error. UPDATES.md is excluded because changelog entries record historical counts that were accurate at the time.

Also added principle 18 sections to `HOW-IT-WORKS.md` (append-only vs mutable shared state explainer with the Anthropic #29217 incident as cautionary data) and `CLAUDE.md` (global config summary with convention-before-automation guidance).

---

## 2026-04-14 (v2.3.2 - Maintenance infrastructure)

### Added: MAINTENANCE.md

Governance doc covering how this repo stays consistent with itself and in sync with personal/internal workflows. Six sections:

1. **Rule audit on new principle** - re-read all rules when adding a principle, catch contradictions in the same PR (this is exactly the check that would have caught the principle-18 vs handoff-rule inconsistency fixed in v2.3.1)
2. **Cross-reference check (automated)** - run `scripts/cross_reference_check.py` before commit
3. **Bi-weekly sync checkpoint** - diff local `.claude/rules/` vs public `rules/`, classify each file as generalizable / local-only / already-ported
4. **Local → public generalization workflow** - 9-step procedure for porting a pattern: strip project context, add prior art, place in right location, verify indexes, grep for personal data leakage
5. **Versioning policy** - major/minor/patch definitions
6. **Red flags** - drift indicators that warrant attention

### Added: scripts/cross_reference_check.py

Automated consistency check. Validates:
- All markdown links resolve to existing files (principles, rules, hooks, templates, skills)
- Principle numbering has no gaps or duplicates
- Every principle is linked from at least one index file
- Every hook is mentioned in README.md

Skips fenced code blocks and inline code so illustrative examples aren't validated. Strict mode (`--strict`) promotes warnings to errors for CI.

**First run result:** 4 real broken links in `alternatives/memory-strategies.md` - inside a markdown code block showing MEMORY.md entry format, pattern examples used markdown link syntax with placeholder filenames (e.g. square-brackets-text-parens-placeholder-md) that didn't resolve to any real file. Even though the enclosing code block made them illustrative, the syntax was misleading: a reader skimming the doc could assume these were real links, and anyone copying the template into their own MEMORY.md would inherit broken links. Fixed by dropping the link syntax for pattern examples (plain `pattern_NAME.md` text). All checks now pass.

### Why this matters

The principle-18-vs-handoff-rule inconsistency (fixed in v2.3.1) was caught by manual review only after commit. The user asked "why didn't we notice?" - because there was no mechanical check for it. The script catches link-level drift. The MAINTENANCE.md workflows catch semantic drift that still needs human reading.

Neither alone is enough. Together they bound how far the repo can drift from its own claims.

### Follow-up: expanded script to shrink the "not caught" list

The original script left three classes of drift to humans: semantic contradictions, outdated trade-off tables, and broken concept references. That framing was wrong - automation should handle everything it can.

Added checks:
- **Principle number references** (error): text mentions of "principle N" must resolve to an actual `principles/NN-*.md` file, not a hallucinated number
- **Alternatives freshness** (warning): opt-in via `related_principles: [N, M]` + `last_reviewed: YYYY-MM-DD` frontmatter. Flags when any referenced principle was modified on a day after the review date. Compares at date precision to avoid same-day false positives.
- **Anti-pattern propagation** (warning): opt-in via `warns_against: [phrase, phrase]` frontmatter on principles. Greps rules/ and alternatives/ for those phrases and warns if they appear - catches cases where a new principle bans X but existing rules still recommend X.

Applied frontmatter to `alternatives/session-handoff.md` as first adopter. Future alternatives should follow the same pattern. MAINTENANCE.md section 2 updated to document all 7 checks and the opt-in frontmatter format.

The "not caught" list is now two items (deep semantics without warns_against phrases, ecosystem shifts external to the repo) instead of three. Every new drift class observed in the future should be added as an automated check rather than left to humans.

---

## 2026-04-14 (v2.3.1 - Handoff rule catches up with multi-session mode)

### Fixed: `rules/session-handoff.md` was stuck on single-file `.claude/HANDOFF.md`

The rule file still recommended the old single-file pattern even though:
- `alternatives/session-handoff.md` already documented 5 approaches including multi-session
- README (v2.2.2 audit) already mentioned `.claude/handoffs/` in handoff section
- Both hooks (`session-handoff-check.py`, `session-handoff-reminder.py`) already support both formats
- Principle 18 (added earlier today) explicitly invokes the multi-session invariant

This left the main rule inconsistent with its own ecosystem. Now the rule:
- Offers **two modes** up front: single-file (simpler, default for most users) vs multi-session (opt-in when parallel chats happen)
- Gives clear switch criteria: "use multi-session only if you've actually hit last-writer-wins data loss"
- Keeps both protocols side-by-side so a user can read whichever fits their workflow
- References principle 18 for the architectural theory behind multi-session

Updated files: `rules/session-handoff.md`, `README.md` (handoff section now shows the two-mode table).

### Note: this repo is maintained separately from any internal workflow

The skills/principles/rules here are a curated set meant to be copy-pasteable into any Claude Code project. Personal workflow evolutions (e.g. project-specific memory files, absolute paths, custom rules) are intentionally excluded. When an internal pattern proves itself and can be generalized, it gets ported here - but the round-trip is manual, not automatic. That's why the public rule lagged: the internal multi-session pattern evolved over weeks before the generalized version was ported.

---

## 2026-04-14 (v2.3.0 - Multi-Session Coordination)

### Added: Principle 18 - Multi-Session Coordination

Pattern for coordinating state between parallel Claude Code sessions that share a single workspace. Addresses a real gap in the ecosystem: isolation solutions (worktrees, sandboxes, Agent Teams) are well-covered, but live shared-state resource locks are not.

- `principles/18-multi-session-coordination.md` - full pattern:
  - Two types of shared state: append-only (handoffs) vs mutable (locks) require different mechanisms
  - Lock-file pattern with heartbeats + external stale verification
  - Convention-first evolution (hooks come later, when patterns stabilize)
  - Per-resource files (not one shared table) to minimize conflict windows
  - Take / Heartbeat / Release protocol with anti-fabrication verify-after-delete
  - Prior art table: Anthropic Agent Teams, claude_code_agent_farm, parallel-cc, Kmux, issue #19364 (proposed session.lock), issue #29217 (`.claude.json` concurrent-write corruption - cautionary data)
  - Why this is a 40-year-old distributed systems problem: translate, don't invent

**Key design decisions:**
- Canonical resource names (`<server>_gpu<N>.lock`) - one resource = one file name, no variants
- Heartbeat obligatory for long tasks (>2h); stale reclaim requires external process verification before taking over
- INDEX.md is append-only (log of TAKE/HEARTBEAT/RELEASE events), lock files are the single source of current state
- Session identity via short task name or session-id prefix, not globally unique UUIDs

**Maturity level:** L2 (Self-Evolving) - live state that accumulates within and across sessions.

---

## 2026-04-12 (v2.2.2 - Freshness audit)

### Fixed: Principle numbering conflict (two #12s)

`12-dbs-skill-creation.md` conflicted with `12-low-signal-residual-training.md`. Renumbered DBS to `17-dbs-skill-creation.md`. Low-Signal Training keeps #12 (was published first, already referenced in UPDATES and README).

### Updated: All index files for accuracy

Comprehensive freshness audit of README.md, AGENTS.md, principles/README.md:
- Principle count: 16 -> 17 across all files
- Skills Catalog: added 6 missing skills (5 video-production + humanize-russian), now 16 total
- Hooks table: added missing `session-handoff-check.py` (SessionStart), now 5 total
- Templates: added `chronicle.md`, `memory-project.md`, `memory-reference.md` to listing
- Session Handoff section: updated from old `.claude/HANDOFF.md` to multi-session `.claude/handoffs/` format
- Chinese (中文) and Russian sections: updated all counts
- Maturity table: added DBS to L1 Foundational
- Decision matrix: added DBS entry

### Added: 2 new alternatives (previously untracked)

- `alternatives/agent-mailbox-system.md` - inter-agent communication patterns
- `alternatives/kb-code-sync.md` - keeping knowledge base in sync with code

---

## 2026-04-12 (v2.2.1 - DBS Skill Creation Framework)

### Added: Principle 17 - DBS Framework (was incorrectly numbered 12)

When creating skills from research, split content into three categories:
- **Direction** (-> SKILL.md): logic, decision trees, error handling
- **Blueprints** (-> references/): templates, guidelines, taxonomies
- **Solutions** (-> scripts/): deterministic code, API calls, calculations

This prevents monolithic SKILL.md files where logic, data, and code are mixed. The model loads Direction into context, fetches Blueprints on demand, and executes Solutions without reasoning.

Source: @hooeem's NotebookLM integration guide (April 2026).

---

## 2026-04-11 (v2.2.0 - Project Chronicles)

### Added: Principle 16 - Project Chronicles

Long-running projects that span weeks/months need more than handoffs. Handoffs answer "what's next?" but not "how did we get here?" Chronicles solve this with a condensed timeline per project.

- `principles/16-project-chronicles.md` - full pattern: chronicle vs handoff vs documentation comparison, entry format, integration with handoffs, when to add entries, scaling strategies
- `templates/chronicle.md` - starter template for new project chronicles
- `rules/session-handoff.md` - updated with chronicle connection: `Project:` field in handoffs, auto-append to chronicle on handoff write

**Key design decisions:**
- Chronicle entry = 3-7 lines of strategic digest (decisions, pivots, results, dead ends), NOT a handoff copy
- One file per project in `.claude/chronicles/`, append-only
- Entries added at milestones (phase completion, pivots, dead ends confirmed), NOT every session
- Chronicles complement handoffs: strategic context (months) + tactical context (days) = full picture

**Maturity level:** L2 (Self-Evolving) - project memory that accumulates across sessions.

### Updated: README, principles/README

- Principle count: 15 → 16
- New maturity row: "Cross-cutting: Session + Project Continuity" (Codified Context, Project Chronicles, Research Pipeline)
- Decision matrix: 2 new entries for project history scenarios

---

## 2026-04-11 (v2.1.0 - Video Production Skills)

### Added: Complete video production skill suite (`skills/video-production/`)

5 new skills for creating product demo videos, ads, and presentations:

- **product-meaning-extractor** - Deep product analysis before creating content. "So What?" test, JTBD, StoryBrand, April Dunford positioning, customer language bank. Outputs structured brief with: core insight, enemy, transformation, unique mechanism, proof, emotional hooks, customer voice bank.

- **video-narrative-arc** - 5 proven narrative templates (10s-90s): Pattern Interrupt, Problem-Solution Flash, Hook-Pain-Demo-Proof-CTA, Apple Keynote Mini, Full Story Arc. Each with beat-by-beat timing, emotional arc mapping, and hook formulas.

- **script-evaluator** - Flatness detector. Scores 6 dimensions (tension, specificity, emotional arc, hook strength, customer voice, visual variety) on 1-10 scale. Identifies 5 common flatness patterns with specific fixes.

- **remotion-production-guide** - Complete Remotion reference: project setup, animation library (fadeIn/slideUp/scalePop/stagger/countTo), spring presets, typography rules, easing reference, color palettes, pacing tables, 3D integration (@remotion/three, Lottie, Spline), export settings for all platforms.

- **video-post-production** - FFmpeg patterns for audio mastering, captions, color correction, platform export (YouTube/TikTok/Reels/Shorts), concatenation, speed changes, GIF creation. Includes volume levels table, BPM guide for music selection, and quality checklist.

Built from deep research: 2500+ lines of rules from Apple HIG, Material Design 3, Disney's 12 Principles, motion design best practices, and analysis of 28 existing Claude Code video/marketing skills.

---

## 2026-04-11 (v2.0.2 - Memory Cross-Links)

### Added: wiki-links graph pattern for memory files

- `rules/memory-crosslinks.md` - guide for adding `[[wiki-links]]` between memory files
- `templates/memory-project.md` - structured project memory with Activity log, Open Items, Key Decisions, Related links
- `templates/memory-reference.md` - structured reference memory with Gotchas and Related links

Inspired by Rowboat knowledge graph approach. Memory files linked via `[[filename]]` create a navigable graph without any database. Five relationship clusters: infrastructure, projects, methodology, tools, feedback.

---

## 2026-04-10 (v2.0.1 - Multi-session Handoff Fix)

### Fixed: handoff scripts now support multi-session format

- `session-handoff-reminder.py` (Stop hook) - now tells agent to write to `.claude/handoffs/` instead of old `.claude/HANDOFF.md`
- Added `session-handoff-check.py` (SessionStart hook) - reads from `.claude/handoffs/` directory, shows recent handoffs, falls back to old format

The old single-file HANDOFF.md format had race conditions when multiple Claude sessions ran in parallel. The new format uses `.claude/handoffs/YYYY-MM-DD_HH-MM_<session-id>.md` with an append-only INDEX.md.

---

## 2026-04-10 (v2.0.0 - Plugin Format)

### BREAKING: Converted to Claude Code plugin format

Added `.claude-plugin/plugin.json` manifest. The repo can now be installed with `claude plugin install` instead of manual file copying. Version bumped to 2.0.0 to reflect this structural change.

### Added: hooks/ directory with 4 ready-to-use scripts

| Script | Event | Purpose |
|---|---|---|
| `session-drift-validator.py` | SessionStart | Validates file path references in CLAUDE.md and rules/ |
| `session-handoff-reminder.py` | Stop | Reminds to write handoff before closing long sessions |
| `destructive-command-guard.py` | PreToolUse | Blocks rm -rf, git push --force, DROP TABLE, etc. |
| `secret-leak-guard.py` | PreToolUse | Prevents writing API keys/tokens into tracked files |

Each script includes setup instructions and works standalone. README covers hook events reference, conditional hooks (v2.1.89+), matcher patterns, and hook response format.

### Added: Principle 14 - Managed Agents

Separate the brain (planning) from the hands (execution). Covers:
- Anthropic Managed Agents API (April 8, 2026): `execute(name, input) -> string` interface
- Brain/Hands/Session architecture with lazy provisioning (p50 TTFT -60%)
- Claude Code Agent Teams (TeamCreateTool behind feature flag - found via Chinese community analysis of 510K LOC TypeScript source)
- HiClaw pattern (Alibaba/AgentScope): Matrix protocol, worker tokens, permission scoping
- Self-hosted alternatives table (CrewAI, Docker Agent SDK, Hermes, tama)
- Cost analysis: $0.08/session-hour + tokens

### Added: Principle 15 - Red Lines (红线)

Absolute prohibitions inspired by Chinese engineering community pattern:
- Red lines vs regular rules: priority, enforcement, incident anchoring
- Three implementation patterns: CLAUDE.md section, separate REDLINES.md, hook enforcement
- Red line categories: data safety, system integrity, external actions, agent-specific
- Lifecycle: incident -> root cause -> draft -> implement -> quarterly review
- Hook > Rule > Hope enforcement hierarchy

### Added: templates/ directory

Starter configurations for common project types:
- `CLAUDE-web-app.md` - React/Vue/Next.js web applications
- `CLAUDE-ml-project.md` - ML/AI training and inference projects
- `CLAUDE-library.md` - npm/PyPI/crates.io packages
- `REVIEW.md` - Code review guidelines (drop-in for any project)

All templates under 150 lines (KV-cache efficient), with `{{placeholder}}` format for customization.

### Updated: Principle 08 - $ARGUMENTS documentation

Added new section on parameterized skills: how `$ARGUMENTS` works, invocation examples, best practices (always handle empty, natural language not CLI flags, scope not behavior).

### Updated: README.md - bilingual sections

Added Chinese (中文简介) and Russian (описание на русском) sections. Not full translations, but navigational summaries for non-English speakers. Includes: feature list, structure overview, installation command.

### Updated: README.md, AGENTS.md, principles/README.md

- Principle count updated from 13 to 15 across all index files
- Added hooks and templates to structure listings
- Added Managed Agents to L3 maturity level
- Added Red Lines to Cross-cutting level
- Added 3 new entries to Decision Matrix
- Added hooks table and templates link to main README

---

## 2026-04-10

### Fixed: Principle numbering conflict

Two files had number 11: `11-documentation-integrity.md` and `11-research-pipeline.md`. Renumbered research-pipeline to `13-research-pipeline.md`. Now 13 principles with clean sequential numbering.

### Updated: Principles README

Added entries for Principles 11 (Documentation Integrity), 12 (Low-Signal Residual Training), 13 (Research Pipeline) to the README overview and decision matrix. Updated principle count from 10 to 13.

### Added: alternatives/managed-agents.md

Comprehensive comparison of Claude Managed Agents (launched Apr 8, 2026) vs Agent SDK vs Claude Code CLI. Covers:
- Brain/Hands/Session architecture and lazy provisioning (p50 TTFT -60%, p95 -90%+)
- Pricing: $0.08/session-hour + standard API tokens. Break-even analysis vs self-hosted
- Vendor lock-in assessment (HIGH for Managed Agents)
- Self-hosted alternatives table (CrewAI, Docker Agent, Hermes, tama)
- Decision matrix and recommendations for teams already using Claude Code
- Real-world cost data: ~$20/week for native Claude Review in GitHub at moderate usage

---

## 2026-04-09 (night)

### Updated: Principle 06 - DeerFlow 2.0 three-layer isolation deep dive

Expanded "Pattern B: Sandbox Isolation (DeerFlow 2.0)" from a brief overview to a full architectural walkthrough. Research source: deep dive into [bytedance/deer-flow](https://github.com/bytedance/deer-flow) README, architecture docs, and DeepWiki analysis.

New content:
- **Layer 1: Virtual Path Translation** (`ThreadDataMiddleware`) - per-thread directories with transparent `/mnt/user-data/*` mapping
- **Layer 2: Docker Container Isolation** (AioSandboxProvider / Kubernetes) - three provisioner modes, 5-10s cold start cost, seccomp/cgroup transparency gap flagged
- **Layer 3: LangGraph State Channel Isolation** - separate `ThreadState` per sub-agent, fan-out/fan-in pattern, unidirectional communication
- **Data flow walkthrough:** `task()` tool -> `SubagentExecutor` -> 3-worker pool -> SSE result, `MAX_CONCURRENT_SUBAGENTS=3`, 15-min timeout
- **Memory weakness** documented: global `memory.json` contamination reintroduces leakage that the isolation layers prevent. Mitigation: per-session memory sharding or append-only with provenance

### Added: Principle 04 - Tool Registry Pattern (Claw Code)

New section citing Claw Code's `rust/crates/tools/` as a reference implementation of declarative tool definitions. `ToolSpec { name, description, input_schema }` struct separates tool definition (data) from dispatch (runtime) from execution (side effect). Three benefits: tiny audit surface, isolated tool tests, new tools without prompt changes. Warning against shipping 200 tools "just in case" (each degrades LLM decision quality) - Claw Code ships 19 as the baseline.

### Added: Principle 10 - Hierarchical Permission Overrides (Claw Code)

New subsection under "Layer 3: Permission Boundaries" showing the Claw Code `PermissionPolicy { default_mode, per_tool_overrides }` structure with a `PermissionMode { Allow, Deny, Prompt }` enum. Cleaner than flat allow/deny lists for single-user setups. Explicit acknowledgment of what it does NOT solve: no RBAC, no resource quotas, no provenance - those require additional mechanisms. Includes a minimal TOML config example for adoption.

### Added: scripts/kvcache_stats.py

Working Python script to measure KV-cache hit rate across Claude Code sessions. Parses `~/.claude/projects/*/*.jsonl` session logs, aggregates `cache_creation_input_tokens` / `cache_read_input_tokens` / `input_tokens` / `output_tokens` from assistant messages, computes per-session and overall hit rate, estimates cost in USD using Claude Opus 4.6 pricing, and shows savings vs a no-cache baseline. Includes percentile distribution, top-N by tokens, worst hit rate detection. Supports filtering by project substring and time window.

Real-world results on a single workspace: 96.9% overall hit rate across 83 sessions in 7 days, $10,929 actual cost vs $78,160 without caching ($67,231 / 86% savings). Median per-session 89.7%. Validates Manus's claim that KV-cache is the dominant production metric.

Run: `python scripts/kvcache_stats.py --days 7 --project <substring>`

---

## 2026-04-09 (evening)

### Updated: Principle 10 - OWASP ASI01-ASI10 + fresh CVEs + 30-minute audit

Major update to the agent security principle based on OWASP Gen AI Security Project's [Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) (published December 2025, 100+ industry experts).

**New sections:**

1. **Full OWASP ASI01-ASI10 mapping** - explicit table showing which of our Attack Taxonomy items cover which OWASP risks, and four new sub-sections for the items our taxonomy did not previously address: ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent Trust Erosion, ASI10 Rogue Agent Behavior.

2. **Minimum Viable Security Audit (5 steps, 30 minutes)** - concrete shell commands for version check, environment hardening, MCP/tool inventory, hook audit, and provenance check. Catches ~70% of realistic attack vectors without architectural changes.

3. **Using RedCodeAgent defensively** - how to use the ICLR 2026 red-team agent ([arxiv 2510.02609](https://arxiv.org/html/2510.02609)) against your own setup. RedCodeAgent memory module discovered 82 unique vulnerabilities on OpenCodeInterpreter where baseline red-teaming found zero.

**Timeline additions (2026 real CVEs):**

- **CVE-2025-59944** (Cursor IDE, CVSS 8.0): case-sensitivity bypass in MCP config (`.cursor/mcp.json` vs `.Cursor/mcp.json`) leading to RCE via prompt injection. Fixed in Cursor v1.7.
- **Claude Code source leak (March 31, 2026):** 59.8 MB source map accidentally shipped in npm v2.1.88, exposed internal architecture to attackers.
- **CVE-2026-35020 / 35021 / 35022** (Claude Code CLI): three command injection CVEs with a shared root cause (unsanitized shell interpolation in TERMINAL env var lookup, editor path invocation, and auth helper). Discovered by Phoenix Security hours after the source leak, validated unpatched on v2.1.91 (production) as of April 3, 2026. CVSS 7.2-8.4.

**Why this matters for Claude Code users:** anyone on a Claude Code version at or before v2.1.91 needs to watch for the security advisory and upgrade via the native installer (not npm) when the patch ships.

---

## 2026-04-09

### Added: AGENTS.md at repo root

Linux Foundation / Agentic AI Foundation standard file. 70 lines, under the 150-line best-practice limit from the GitHub analysis of 2500+ repositories. Hybrid with CLAUDE.md: AGENTS.md is the universal entry point for any agent (Codex, Cursor, Claude Code), CLAUDE.md remains the Claude Code-specific overlay. Future-proofs the repo for when Claude Code adds native AGENTS.md support (issue anthropics/claude-code#6235).

### Updated: Principle 01 - SEMAG trace-similarity escalation

Added a new section on execution trace similarity as a stagnation signal for Generator-Evaluator loops. Based on [arxiv 2603.15707](https://arxiv.org/abs/2603.15707). When consecutive attempts produce near-identical runtime traces (rho > 0.85), the loop has stalled and should escalate through three levels: single-shot -> trace-guided debugging -> multi-agent discussion-decision with weighted voting. Explicitly rejects SEMAG's full Automatic Model Selector as too task-specific without difficulty measurements.

### Updated: Principle 02 - Reliability metrics + OpenClaw paid note

Added a new section on reliability as a distinct dimension from accuracy, based on [arxiv 2602.16666](https://arxiv.org/html/2602.16666v1). Extends the single PASS/FAIL verdict with a four-dimensional tuple (consistency, robustness, predictability, safety). Minimum viable adoption: multi-run consistency + prompt paraphrase robustness. Also added a note at the top: OpenClaw is now a paid third-party tool as of April 4, 2026, but the arxiv paper and the pattern remain freely usable.

### Updated: Principle 06 - Coordination Patterns (Paperclip vs DeerFlow)

Added a new section comparing two production-tested coordination approaches: Paperclip's shared-workspace pattern (43K stars, file-based handoff, scales to 50+ trusted agents) vs DeerFlow 2.0's sandbox-isolation pattern (44K stars, per-agent Docker, 10-15 agents with strict blast-radius control). Includes a decision table and a hybrid pattern.

### Updated: Principle 03 - Autoresearch scope limitations

Added SICA v2 findings from [arxiv 2504.15228](https://arxiv.org/abs/2504.15228). Three failure modes: base model saturation, reasoning interruption, path dependency. Revised scope guidance and a "signal to stop" rule: three consecutive iterations without improvement means stop.

### Updated: alternatives/context-management.md - Manus KV-cache insights

Comprehensive section on KV-cache hit rate as THE production metric. Four rules for cache-friendly context: stable prefixes, mask tools instead of swapping, filesystem as extended context, preserve errors. Includes the todo.md recitation trick (exploiting recency bias). Cross-table showing how KV-cache interacts with each of the four context management approaches.

### Updated: Principle 09 - Sapphire Sleet attribution + native installer note

Added Microsoft's Sapphire Sleet attribution alongside Google's UNC1069 attribution (same DPRK actor, different vendor naming). Added explicit Claude Code recommendation: use the native installer instead of npm to eliminate transitive dependency attack vectors entirely.

---

## 2026-04-08 (night update)

### Updated: Principle 12 - Added Trap 7 (Loss Asymmetry on Bipolar Residuals)
- **Critical discovery from visual inspection**: L2 loss silently ignores half of bipolar residual distributions (e.g., Dodge&Burn where dodge spots are +5% but burn spots are -2%)
- Metrics (MAE, PSNR) looked fine because the missed side contributes less to mean error — but visual contrast enhancement revealed model was producing "zero" for darker corrections
- New **Trap 7** section: cause, diagnosis, fix (L1/Huber instead of L2)
- Updated "Which Loss" section: L2 is wrong for bipolar residuals, Huber is safe default, Active weighting helps on dense/complex scenes
- Added diagnostic step #8: compare enhanced prediction vs enhanced GT side-by-side, check both sides of distribution
- Updated quick-reference config: `loss_fn: huber` (was L2)
- Key lesson: **don't trust metrics alone for low-signal tasks - always visually inspect with contrast enhancement ×5-10**

---

## 2026-04-08 (evening)

### Added: Principle 12 - Low-Signal Residual Training
- `principles/12-low-signal-residual-training.md` - 6 traps + fixes for ML tasks where targets have small deviations from a constant baseline
- Covers: "predict zero" attractor, PSNR metric lies, JPEG target poisoning, tanh saturation, subject background pollution, warmup/EMA timing
- Source: 4 rounds of retouch training failure + 7-config parallel sweep
- Includes known-good config (U-Net + EffB4, amp=5, no tanh, Huber/L2, warmup+delayed EMA)
- General applicability: any residual prediction task (denoise, color correction, enhancement)

---

## 2026-04-08

### Added: 3 new alternatives from Telegram research digest
- `alternatives/memory-strategies.md` - verbatim vs extraction vs hybrid, MemPalace 4-layer model, temporal validity, when to use ChromaDB
- `alternatives/token-economy.md` - Caveman Prompting (75% token savings), where to apply/avoid, quantitative benchmarks
- `alternatives/multi-agent-patterns.md` - Generator-Evaluator, Coordinator+Specialists, CORAL heartbeat, Proof Loop, implementation in Claude Code

### Updated: English Text Humanization Skill
- `skills/writing/humanize-english/SKILL.md` - upgraded sources from SEO blogs to peer-reviewed research
- Added Liang et al. (arxiv 2406.07016) data: 10 marker words, excess ratios (delve 25.2x, showcasing 9.2x)
- Added structural anti-patterns section (AI shape, symmetry, tone traps)
- Added co-evolution note (word lists go stale, principles > specific words)
- Replaced "humanizer tool" sources with academic papers + research data repos

### Added: Russian Text Humanization Skill
- `skills/writing/humanize-russian/SKILL.md` - new skill for Russian-language text naturalization
- Russian-specific markers: "является", "не просто..., а...", deverbal nouns (отглагольные существительные)
- English calque detection (word order, syntax patterns)
- Conversational elements dosing (частицы, вводные, оценочные)
- Checklist + comparison table RU vs EN detection differences
- Sources: gramota.ru, Habr 918226, Sber GigaCheck, Russian Wikipedia

---

## 2026-04-07

### Added: Alternative - Workspace Organization
- `alternatives/workspace-organization.md` - система из 3 навигационных .md файлов
- WORKSPACE.md (карта), PROJECTS.md (реестр), session-handoff (правило)
- Research Hub с тематическими подпапками (_inbox, agentic, ml, infra, security, product)
- Потоки данных: raw research → research/{тема}/ → knowledge pipeline → проекты
- Связь с Karpathy LLM Wiki, MemPalace, CORAL patterns

---

## 2026-04-04

### Added: Principle 11 - Research Pipeline
- Save research results to `.research/incoming/` after every research session
- Prevents duplicate work across sessions
- Creates a knowledge pipeline: research -> incoming -> review -> knowledge base
- Connected to Codified Context, Session Handoff, Autoresearch principles

---

## 2026-04-08

### Added: Manual handoff trigger phrases + ready-to-copy rule file

Natural-language trigger phrases ("prepare handoff", "save context for new chat", etc.) for writing `.claude/HANDOFF.md` on demand. Essential for migrating existing sessions that predate any hook-based automation.

- New file: [rules/session-handoff.md](rules/session-handoff.md) - drop-in rule with trigger phrases, HANDOFF.md format, session-start behavior, and rule-vs-hook rationale
- New README section: "Session Handoff - Moving Between Chats" with the trigger phrases and usage explanation for humans
- Updated [alternatives/session-handoff.md](alternatives/session-handoff.md): trigger-phrase variant added to Approach A (Manual HANDOFF.md)

The rule complements hook-based automation: hook handles forgetful users, rule handles deliberate session closure.

### Added: Principle 11 - Documentation Integrity

Fundamental solution to documentation drift for AI agents: validate all file references at session start via a SessionStart hook, not rules.

**Core insight**: rules are instructions of hope - the agent follows them only if it remembers and chooses to. Hooks are shell processes that run unconditionally. For guaranteed behaviors (validation, handoff, cleanup), use hooks, not rules.

The principle ships with a working Python validator (`scripts/validate_config.py`) that:
- Distinguishes real references (absolute paths, multi-segment with `/`) from examples (bare filenames like `foo.py`)
- Uses multi-strategy path resolution (absolute -> relative to file -> cwd -> workspace roots)
- Keeps false positives low via skip patterns for template placeholders

Drop the script into `~/.claude/scripts/` and register a `SessionStart` hook - the agent sees drift warnings automatically on every session start.

See [principles/11-documentation-integrity.md](principles/11-documentation-integrity.md) and [scripts/validate_config.py](scripts/validate_config.py).

---

## 2026-04-03

### Rewritten: README.md

Repositioned from "skills collection" to "configuration system for Claude Code agents". Focus on: what problems each principle solves (not abstract descriptions), alternatives as key feature (agent picks the right approach), security hardening section, principles by maturity level (L1-L3). Skills described as secondary/reference implementations.

### Added: Session Handoff comparison (Alternative)

Five approaches to seamless session transitions compared: Manual HANDOFF.md, Stop Hook (auto), Session Journal (living log), ContextHarness (framework), Memory Only (baseline). Sources: claude-handoff plugin, ContextHarness, JD Hodges patterns, GitHub issue #11455 community patterns.

Key insight: structured handoff (500-2000 tokens) beats raw conversation dump (50-100K tokens) by ~50x compression with higher signal. "What did NOT work" is the most valuable section - prevents the next session from repeating dead ends.

See [alternatives/session-handoff.md](alternatives/session-handoff.md).

---

## 2026-04-02

### Added: Research evidence to Codified Context (Principle 07)

Two contradictory studies on context files (AGENTS.md/CLAUDE.md): one shows -28.6% task time, other shows -3% success rate. Resolution: auto-generated context hurts, human-written non-inferable knowledge helps. Added "The Rule" - only include what the agent cannot derive from reading the code. ETH Zurich data: LLM-generated context = +20% cost, +2-4 extra reasoning steps.

### Added: Principle Map by Reasoning Level to README

Three-level taxonomy (arxiv 2601.12538, 2504.19678) maps to our 10 principles: L1 Foundational (single agent), L2 Self-Evolving (feedback + memory), L3 Collective (multi-agent). Helps users pick which principles to adopt first.

### Updated: Structured Reasoning accuracy to 93% (Principle 05)

Paper v2 results on real-world agent-generated patches: 78% -> 93% accuracy.

---

## 2026-04-01

### Added: axios@1.14.1 case study to Supply Chain Defense (Principle 09)

Real-world supply chain attack on the official `axios` npm package (~100M weekly downloads), attributed to DPRK-nexus threat actor UNC1069 by Google Threat Intelligence. Maintainer account hijacked, RAT deployed via postinstall hook. Exposure window: ~3 hours. `min-release-age=7` would have completely blocked the attack. Full timeline, attack chain, defense matrix, and IOCs documented. Sources: Elastic Security Labs, Snyk, Wiz, Google Cloud Blog.

### Added: Revision Trajectories + problems.md schema to Proof Loop (Principle 02)

Based on Agent-R (arxiv 2501.11425): failed-then-fixed trajectories are more valuable than clean passes. Added structured Evaluator feedback format (cut point + reflection + direction) and a concrete `problems.md` schema with criterion ID, reproduction steps, expected vs actual, affected files, and smallest safe fix. Improves the fix -> verify again cycle.

### Fixed: README principle count (9 -> 10)

README.md listed "9 architectural principles" and was missing Principle 10 (Agent Security) from the principles table. Updated to reflect all 10 principles.

### Added: "Deletion = re-verification" rule to Anti-Fabrication

Added the pattern: after executing a delete command, always verify the object is actually gone. Commands can exit 0 without doing anything (permissions, locks, wrong path). Part of the Anti-Fabrication section in Deterministic Orchestration.

---

## 2026-03-31

### Added: Agent Security (Principle 10)

Comprehensive defense guide against prompt injection and adversarial attacks on AI coding agents. Covers 7 attack categories (in-code injection, repo metadata, package metadata, MCP tool poisoning, web content injection, memory poisoning, sandbox escape) with real CVEs and incidents. Six-layer defense architecture from content isolation to monitoring. See [principles/10-agent-security.md](principles/10-agent-security.md).

### Added: Supply Chain Defense (Principle 09)

Package age gating as defense against supply chain attacks. Two config lines that block packages published less than 7 days ago:

```ini
# ~/.npmrc
min-release-age=7
```

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

Most malicious packages are caught within 1-3 days. The 7-day delay eliminates the attack window with near-zero friction to your workflow. See [principles/09-supply-chain-defense.md](principles/09-supply-chain-defense.md) for full details including per-manager configs, CI considerations, and defense-in-depth layers.

### Fixed: 6 skills were ZIP archives, not readable on GitHub

`diffusion-engineering`, `vlm-segmentation`, `flux2-klein-prompting`, `forensic-prompt-compiler`, `ios-development`, `frontend-design` - all now properly extracted with SKILL.md + references/ as readable markdown.

### Updated: Memento references replaced

The `mderk/memento` repo appears to have been removed from GitHub. All references updated to point to active alternatives: [task-orchestrator](https://github.com/jpicklyk/task-orchestrator), [inngest/agent-kit](https://github.com/inngest/agent-kit). The deterministic orchestration principles remain valid and well-documented.

### Freshness check: all 10 concepts reviewed

| Concept | Status |
|---------|--------|
| Generator-Evaluator | Current - now a standard primitive |
| Proof Loop | Current - watch formal verification + LLM space |
| Autoresearch | Very current - 21K stars, ecosystem explosion |
| HyperAgents | Current - Meta released code |
| HACRL | Current - conceptual pattern is actionable |
| Structured Reasoning | Current - 78%->88% accuracy validated |
| Codified Context | Current - 1M window adjusts urgency, not principle |
| Memento | Repo gone - principles live in alternatives |
| Context Engineering | Current - update for 1M context realities |
| Multi-Agent Decomposition | Current - trend toward adaptive routing |

---

## 2026-03-30

### Initial release

8 architectural principles, 4 alternative comparison docs, 10 skills, CLAUDE.md template. Covers: harness design, proof loops, autoresearch, deterministic orchestration, structured reasoning, multi-agent decomposition, codified context, skills best practices.
