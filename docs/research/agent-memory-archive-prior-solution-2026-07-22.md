# Agent Memory and Prior-Solution Archive Research

Date: 2026-07-22
Status: adopted with a measured scope

## Problem

The same task can be reopened in Codex or Claude. The agent needs to find the
previous decision, evidence, and unresolved edge cases before proposing a new
implementation. Full transcript dumping is durable, but it is a poor first
lookup surface and can exhaust context.

## What existing systems confirm

- Letta Code keeps memory as a normal Git repository, which makes memory
  inspectable, versioned, and portable:
  https://github.com/letta-ai/letta-code
- ctk uses SQLite full-text search for archived conversations:
  https://github.com/queelius/ctk
- AgentDex indexes conversations from several coding agents into one search
  surface:
  https://www.agentdex.sh/
- Neo4j's agent-memory example models conversations and reasoning traces as a
  graph, while Jcode uses a separate memory/verifier path:
  https://github.com/neo4j-labs/agent-memory
  https://github.com/1jehuang/jcode
- Recent research also points toward hierarchical, dependency-aware memory
  traversal rather than sending an entire history to every turn:
  https://arxiv.org/abs/2605.14563

These examples support the architecture, but do not by themselves prove that
embeddings or a graph improve this repository's workload.

## Decision for this harness

Keep the current four-level lookup order:

1. `knowledge/` for compact, promoted decisions and verified patterns.
2. Readable `sessions/` for human-readable context and exact handoffs.
3. `research/` for source material and evaluated external ideas.
4. Raw JSONL only for forensic recovery, not as the default context payload.

The `UserPromptSubmit` hook searches the compact knowledge index first. A full
archive search remains available through `prior_solution.py`. Every promoted
knowledge entry must point back to evidence and must be validated against the
current repository state before reuse.

Do not add a vector database or graph index to the core path yet. First collect
a small benchmark of real prompts with expected prior-solution matches and
measure precision, recall, latency, and stale-result rate. Add a second index
only if the measured knowledge-first search misses relevant prior work.

## Operational requirements

- Readable chats, research files, knowledge indexes, and handoffs are mirrored
  to the private archive repository by the existing writer and Stop hook.
- Raw Codex JSONL has a separate writer and ownership boundary. Its freshness
  must be monitored separately; a readable archive being current does not mean
  raw history is current.
- The archive repository must stay private. The writer must verify GitHub
  visibility before pushing.
- Search failures and timeouts must never be reported as proof that no prior
  solution exists.

## Verification plan

Run the archive test suite, query `prior_solution.py` with known historical
topics, inspect the generated sync status files, and check the scheduled task.
For future changes, record a small JSONL benchmark with expected matches and
run it before promoting changes to the hook.
