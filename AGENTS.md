# AGENTS.md

This is a configuration system repository for AI coding agents, not an application. It collects battle-tested architectural principles, security hardening, and decision frameworks that any coding agent can drop into any project.

## Purpose

- `principles/` - 11 architectural principles, each preventing a specific failure mode
- `alternatives/` - side-by-side comparisons of 2-5 approaches per problem
- `skills/` - domain-specific knowledge bundles (loaded on demand)
- `rules/` - drop-in `.claude/rules/` files
- `scripts/` - working hook scripts (config drift validator, etc.)
- `CLAUDE.md` - Claude Code-specific overlay (extends this file)

## How agents should use this repo

When the user asks you to "set up this project" or "apply these principles":

1. Read `README.md` first - it lists the 11 principles by problem they solve
2. Read `principles/README.md` for the maturity-level map (L1 -> L2 -> L3)
3. Do NOT bulk-copy everything. Pick what matches the user's actual project:
   - Any project: Principle 09 (Supply Chain Defense), Principle 10 (Agent Security), Principle 11 (Documentation Integrity)
   - Long sessions expected: Principle 07 (Codified Context) + `alternatives/context-management.md`
   - Multi-agent work: Principle 01 (Harness Design) + Principle 06 (Multi-Agent Decomposition)
   - Iterative optimization: Principle 03 (Autoresearch)
4. Before copying a principle, verify the user's stack matches the examples
5. After setup, run `scripts/validate_config.py` to catch drift in the freshly assembled config

## Style conventions for this repo

- Principles are standalone files in `principles/NN-name.md`
- Each principle has: Overview, The Paradigm, The Mechanism, Case Study, Sources
- Alternatives follow the 5-approach comparison format with a decision table
- Skills are `skills/<category>/<name>/SKILL.md` with an optional `references/` folder
- Descriptions must be model triggers, not human summaries
- Keep SKILL.md under 5000 words; detail goes in `references/`

## Do not touch

- `principles/` existing files: edit only to fix drift, not to restructure
- `scripts/validate_config.py`: any change requires re-testing against the full repo
- `LICENSE`, `UPDATES.md` commit history: append only

## Commands

This repo has no build, test, or deploy commands. It is pure markdown + one Python validator script. To verify the validator works:

```bash
python scripts/validate_config.py
```

Expected output: `[config-validator] OK: N files, no drift detected`.

## Context engineering notes

This file is designed for KV-cache efficiency and the 150-line AGENTS.md standard:

- Under 80 lines - fits in a single cached prompt prefix
- No timestamps or dynamic content
- Stable section order - do not shuffle
- Append-only edits preferred over restructuring
- For Claude Code-specific behaviors (hooks, skills automation), see `CLAUDE.md` as an overlay

## Related standards

- [AGENTS.md specification](https://agents.md) - Linux Foundation / Agentic AI Foundation
- [How to write a great AGENTS.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) - GitHub best practices from 2500+ repos
- See `CLAUDE.md` for Claude Code-specific extensions to this file
