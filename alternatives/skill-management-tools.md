# Skill Management Tools — comparison with our manual mirror workflow

Two community tools surfaced in May 2026 solving variants of "manage Claude Code skills/rules/agents across multiple machines and projects". Both honest, both useful for the right setup. Here is how they compare with the approach this repository takes.

## The problem they solve

When you maintain Claude Code configuration across multiple machines and multiple projects, you accumulate friction:

- Local `~/.claude/skills/` differs from project-level `.claude/skills/` differs from machine B's
- Public skill repos exist; you want some skills, not all — pulling everything bloats context
- After improving a rule on machine A, you need to sync to machine B and to your public-share repo
- When you join a new machine, restoring full setup is manual

This repo's current approach: manual `cp` between locations + `git push`. Works, but each sync is hand-coordinated and easy to forget.

## Tool 1: ai-dotfiles

**Repo:** https://github.com/pavel-gorlov/ai-dotfiles
**Language / age / stars (2026-05-16):** Python, 4 days old, 0 stars, single contributor
**Self-description:** "Package manager for Claude Code configuration. Like npm for your AI coding setup."

### How it works

1. **Central catalog** at `~/.ai-dotfiles/catalog/` holds shared skills, agents, rules, hooks, and "domains" (bundles of related elements with topological dependencies)
2. **Manifest** `ai-dotfiles.json` per project lists which packages that project uses
3. **Symlinks** from `<project>/.claude/` into the central catalog — project tree stays small, content versioned once in catalog
4. **Vendor system** for installing 3rd-party content: `vendor github install`, `vendor skills_sh install`, `vendor paks install`, `vendor buildwithclaude install`, `vendor tonsofskills install`
5. **Settings merge** — domains can ship `settings.fragment.json` / `mcp.fragment.json` which are deep-merged into `.claude/settings.json` / `.mcp.json` on `add`, with user-authored keys preserved and ownership of what the tool wrote tracked for clean removal
6. **Gitignore sync** — managed block in `.gitignore` lists vendored symlinks so per-machine paths never land in git history
7. **Multi-machine restore** — `ai-dotfiles init -g --from git@github.com:you/my-config.git` clones your storage repo on a new machine

### Where it fits well

- You manage Claude Code config across 3+ machines
- You install many 3rd-party skills and want a clean uninstall path
- You have multiple MCP servers and want per-project `.mcp.json` to compose from named domains
- You want a small `.claude/` per project (just symlinks) instead of duplicated content

### Why this repo does not adopt it

- **Symlinks are a hard "no" in our setup** (see CLAUDE.md "НИКАКИХ СИМЛИНКОВ"). The reason: symlinks break under mount-point migrations (`/vol/` vs `/workspace/` vs `/mnt/`), create invisible dependencies, complicate backup/rsync/container-rebuild. We solve the same problem with explicit config files, environment variables, or copies. ai-dotfiles' core mechanism is symlinks; adoption would require either changing our rule or forking the tool.
- **Supply chain risk profile mismatch.** Our `min-release-age=7` (npm) and `exclude-newer = "7 days"` (uv) gate fresh packages by default. ai-dotfiles is 4 days old at evaluation, 0 stars, single contributor — pipx fetch bypasses these gates. The tool itself looks well-written, but our policy is to wait for the maturity window before adoption.
- **Public-vs-private boundary.** ai-dotfiles' `~/.ai-dotfiles/` is private storage. Our `claude-code-config` repo is **public share for community**. These are different concepts; adopting ai-dotfiles' model means deciding how the public share fits into it (a vendor source? a separate flow?). Not a blocker, but not free either.

### What we like and may borrow conceptually

- **Domain manifest with topological depends** — clean way to express "this skill needs that rule needs that hook". Our `principles/README.md` "Composition Patterns" section already does this informally; could be formalized.
- **Vendor system with `.source` file** tracking origin/date/license per installed item — would solve the question "where did this skill come from when I want to update it?" cleanly. Our current approach: ATTRIBUTION.md hand-written per cloned skill.
- **Settings fragment merge with ownership tracking** — `.ai-dotfiles-settings-ownership.json` tracks what was added by tool vs user, so removal cleans only its own additions. Conceptually parallel to our drift-state.json mark-with-timestamp pattern.

## Tool 2: Skiller

**Repo:** https://github.com/beautyfree/skiller
**Language / age / stars (2026-05-16):** TypeScript (Electron), updated today, 19 stars
**Self-description:** "AI agent skills manager for Claude Code, Cursor, Codex and more — install, sync, and manage skills from one desktop app."

### How it works

- Desktop GUI application for managing skills across 30+ AI agent tools (Claude Code, Cursor, Codex, Gemini CLI, Kiro, Junie, Cline, Goose, Continue, Copilot CLI, Crush, ...)
- Each agent's skill format is normalized; install from one source, deploy to multiple agents
- Selective install from external skill repositories (avoids the "Cursor pulls all skills from all agents" bloat problem)

### Where it fits well

- You actively use 2+ AI agent tools (e.g. Claude Code + Cursor + Codex) and want consistent skill sets across them
- You prefer a desktop GUI over CLI for skill management
- You have skill bloat from auto-import behavior in any of your tools

### Why this repo does not adopt it

- **We are Claude Code-primary.** A single-agent setup does not benefit from cross-agent normalization. Claude Code's own progressive disclosure (skill triggers via descriptions, not preloaded content) handles bloat already.
- **CLI-first workflow.** A desktop GUI app adds friction for a workflow that is already entirely terminal-based.
- **Different abstraction level.** Skiller manages skills as a top-level concept. Our setup has skills + rules + agents + hooks + principles + alternatives + templates, all linked. A skills-only tool would handle only one slice.

### What we like and may borrow conceptually

- **Selective install** from external skill collection (Skiller calls out the Cursor "auto-pull everything" problem explicitly). Our manual `cp` + commit flow already does this naturally — we choose what to take. Worth keeping in mind if we ever build a cleaner install path for our own users.

## This repo's current approach

For now, this repo continues with:

1. **Local source of truth:** `~/.claude/rules/`, `~/.claude/skills/`, project-level `.claude/rules/`
2. **Public share:** `claude-code-config` repo on GitHub (this repo). Manual `cp` from local to repo + `git push` per release. Sanitization at copy time removes project-specific paths and person names.
3. **Multi-machine sync:** `git clone` this public repo + manual file selection (some items are not for all setups)
4. **External skill consumption:** `git clone --depth 1 <upstream-repo> ~/.claude/skills/<name>/` + `ATTRIBUTION.md` documenting source and clone date
5. **Update procedure:** `git pull` in `~/.claude/skills/<external>/`, diff, apply meaningful changes manually

This approach is hand-coordinated but transparent. Every file is real (no symlinks), every external dependency has an explicit attribution trail, and every public release has been intentionally curated.

## When to switch

Consider adopting ai-dotfiles (or building a similar tool ourselves without symlinks) when:

- Manual `cp` + `git push` per release crosses 5 commits per week
- You start maintaining > 5 active project-level `.claude/` directories
- You add a third machine to the rotation
- You start installing 3rd-party skills frequently enough that ATTRIBUTION.md trails become hand-coordinated drift risk

For now (1-2 machines, low-frequency 3rd-party installs, public share is itself the multi-machine sync mechanism), the manual approach has acceptable friction.

## Related entries in this repo

- [alternatives/managed-agents.md](managed-agents.md) — when to use Anthropic Managed Agents vs self-built harness (parallel "managed vs DIY" decision)
- [alternatives/orchestration.md](orchestration.md) — workflow orchestration tools
- [principles/08-skills-best-practices.md](../principles/08-skills-best-practices.md) — what makes a skill good once you have one
- [principles/17-dbs-skill-creation.md](../principles/17-dbs-skill-creation.md) — DBS framework for creating new skills from research

## Source links

- Original community announcement (May 2026): https://t.me/ai_dev_community (paraphrased)
- ai-dotfiles: https://github.com/pavel-gorlov/ai-dotfiles
- Skiller: https://github.com/beautyfree/skiller
