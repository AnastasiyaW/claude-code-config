# Maintenance Workflow

How to keep this repo internally consistent and in sync with personal/internal workflows.

This repo is a curated, generalized set of principles, rules, hooks, and skills. It evolves separately from any specific project. The guidelines below catch drift before it ships.

---

## 1. Rule audit on every new principle

**Trigger:** adding a new `principles/NN-*.md`.

**Before merging:**
1. Re-read every file in `rules/` with fresh eyes
2. Ask: does the new principle contradict or supersede any rule?
3. Ask: does any rule need a cross-reference to the new principle?
4. Ask: does the new principle change what "best practice" means for any existing pattern?

**Example of drift we actually hit:**
Principle 18 (multi-session coordination) was added while `rules/session-handoff.md` still recommended single-file `.claude/HANDOFF.md` - the exact pattern principle 18 warns against. The principle and the rule were internally inconsistent for one commit.

**Mitigation:** after writing a principle, search `rules/` for any file that touches the same topic and audit alignment in the same PR.

**Command:**
```bash
# List rules that mention handoff / session / lock / etc
grep -rli "<keyword>" rules/
```

---

## 2. Cross-reference check (automated)

**Script:** `scripts/cross_reference_check.py`

**What it checks:**
1. Every markdown link resolves to an existing file (principles, rules, hooks, templates, skills)
2. Principle numbering has no gaps or duplicates
3. Every principle is linked from at least one index (README / principles README / AGENTS.md)
4. Every hook in `hooks/*.py` is mentioned in README.md

**Run before every commit:**
```bash
python scripts/cross_reference_check.py
```

**Strict mode** (warnings fail too):
```bash
python scripts/cross_reference_check.py --strict
```

**Automated checks the script performs:**
1. All markdown links resolve to existing files
2. Principle numbering has no gaps or duplicates
3. Text references to "principle N" resolve to an actual `principles/NN-*.md`
4. Every principle is linked from at least one index (warning)
5. Every hook is mentioned in README (warning)
6. **Alternatives freshness** (warning) - if an `alternatives/*.md` declares `related_principles: [N, M]` + `last_reviewed: YYYY-MM-DD` in frontmatter, the script flags it when any of those principles was modified on a day after `last_reviewed`. Forces a re-audit before stale trade-off tables ship.
7. **Anti-pattern propagation** (warning) - principles with `warns_against: [phrase1, phrase2]` frontmatter cause the script to grep rules/ and alternatives/ for those phrases and warn if they appear, catching cases where a new principle bans pattern X but an existing rule still recommends X.

**Opt-in via frontmatter:** checks 6 and 7 are opt-in - a file is only audited when it declares the relevant frontmatter keys. Files without frontmatter are ignored. This lets the system grow as patterns mature, rather than forcing retrofit on day one.

**Example frontmatter:**
```yaml
---
related_principles: [16, 18]
last_reviewed: 2026-04-14
---
```

```yaml
---
warns_against: ["single file .claude/HANDOFF.md", "mock the database in integration tests"]
---
```

**What the script still does NOT catch** (narrower scope than before):
- Deep semantic inconsistency that isn't captured by any `warns_against` phrase - still needs a human read-through on new principle introduction
- Trade-off tables that became outdated because the *ecosystem* shifted (not our own principle) - e.g. a competitor library improved. Requires external awareness, no file mtime signals it.

Whenever you notice a class of drift the script missed, **add it as a new automated check** instead of leaving it in this "not caught" list. The goal is to shrink this list over time.

---

## 3. Bi-weekly sync checkpoint with local workflow

**Trigger:** every ~2 weeks, or when onboarding a new significant pattern.

**Workflow:**
1. Diff `.claude/rules/` from your active project against `rules/` in this repo
2. For each file in local that doesn't exist in public, classify:
   - **Generalizable** - pattern applies broadly, not tied to personal paths/infra → port
   - **Local-only** - personal workflow (specific research hub, project names, server hostnames, custom triggers) → stay local
   - **Already ported** - covered by an existing principle/rule → verify alignment, no action
3. For each file in public that exists in local, diff the content:
   - Is the public version lagging behind local evolution? → update public
   - Is the public version correctly generic while local is happyin/project-specific? → no action
4. Update UPDATES.md with any ports or fixes

**Classification helper questions:**
- Does it mention specific server names, IPs, or paths like `C:\Users\...`? → local-only, do not port
- Does it describe a named personal project (e.g. "Журналист", specific client)? → local-only
- Does it describe a generic pattern anyone could adopt? → generalizable, port with personal details removed

---

## 4. Local → public generalization workflow

**When a pattern in a personal project proves itself and should become public:**

1. **Extract the core pattern** (what problem, what solution, what trade-offs)
2. **Strip all project-specific context:**
   - Replace hostnames with `host-a`, `server1`, or drop entirely
   - Replace absolute paths (`C:\Users\...`) with relative or `<project-root>/`
   - Remove proper names of internal projects
   - Remove language-specific triggers if the audience is broader (e.g. drop Russian-only trigger phrases unless the doc has an explicit Russian section)
3. **Add prior art section** - search for existing solutions to the same problem (GitHub, blog posts, papers). Link them. Position the new contribution relative to what exists.
4. **Place in the right location:**
   - Cross-cutting architectural pattern → `principles/NN-*.md`
   - Copy-pasteable behavior rule → `rules/*.md`
   - Trade-off comparison between approaches → `alternatives/*.md`
   - Executable automation → `hooks/*.py` or `scripts/*.py`
   - Reusable starter file → `templates/*.md`
5. **Update indexes** - README.md, AGENTS.md, principles/README.md if applicable
6. **Run cross-reference check** - `python scripts/cross_reference_check.py`
7. **Rule audit** - does this new pattern affect existing rules? (see section 1)
8. **Grep for personal data leakage before commit:**
   ```bash
   # Run against changed files - look for anything project-specific that slipped through
   grep -rE "personal-hostname|internal-project-name|C:\\\\Users|10\.|192\.168\." <changed-file>
   ```
9. **Commit with a Why section** - UPDATES.md entry should explain why this is a good addition, not just what changed

---

## 5. Versioning policy

- **Major** (vN.0.0) - breaking change to recommended patterns, large restructure
- **Minor** (v2.N.0) - new principle, new rule, new hook (additive)
- **Patch** (v2.3.N) - bug fix, freshness audit, rewrite that doesn't change recommendations

When in doubt, prefer minor over patch. The changelog is the audit trail.

---

## 6. Red flags that indicate drift

Watch for these in code review or self-review:

- A principle advocates pattern X, but a rule implements anti-pattern X' in the same repo
- A rule references `<file>.md` that doesn't exist
- A hook registers an event that doesn't exist in Claude Code current version
- UPDATES.md mentions v2.N.M but no commit bumps version numbers anywhere
- README.md counts don't match file counts (e.g. "17 principles" when `principles/` has 18)
- Dead link to an external GitHub repo that moved or archived

The cross-reference check catches most of these mechanically. Pair with periodic human read-through.
