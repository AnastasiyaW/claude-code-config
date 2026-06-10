# Bug-Fix Task Prompt Template (Opus 4.7-tuned)

Использовать когда даёшь агенту задачу починить баг или provide code review где найденные issues должны быть исправлены, не отложены.

Учитывает literal interpretation Opus 4.7 (по дизайну narrows scope) - даёт **explicit constraints** чтобы агент не уходил в "это pre-existing".

## Шаблон

```
[Bug Report / Task]
- File: <path>:<line range>
- Reproduction: <command или steps что показывают bug>
- Current behavior: <что происходит сейчас>
- Expected behavior: <что должно>

Acceptance criteria:
1. <Failing test/check before fix - reproducible>
2. <Same test/check passes after fix>
3. <Full test suite remains green>
4. <Linter/build OK>

Constraints (mandatory, do not narrow scope):
- ALL bugs/quality issues encountered MUST be fixed in this session
- Do NOT label any finding as "pre-existing", "out of scope", "separate refactor", "deferred"
- "Risky" or "complicated" are NOT valid reasons to skip - they mean test more carefully or split into steps
- If a finding genuinely cannot be fixed now → add to PROBLEMS.md with explicit Status from 5-exception list:
  missing-data | missing-dep | arch-decision | scope-explosion | inaccessible-repo
- Without one of these 5 reasons - the finding must be fixed in this session
- "Done" requires durable artifacts: failing→passing test command + output, not "looks good"

Process:
1. Read affected file(s) fully (not just diff context)
2. Reproduce the bug (artifact: command output before fix)
3. Write failing test/check (artifact: test fails red)
4. Fix
5. Verify test passes (artifact: test passes green)
6. Run full suite (artifact: no regression)
7. List ALL other findings from steps 1-6. Each must be either fixed OR in PROBLEMS.md with valid Status

Self-verification before claiming done:
- Did I fix only the requested bug or also adjacent issues I noticed? List both.
- Did I label anything as pre-existing/out-of-scope without 5-exception ticket? If yes - go fix or ticket properly.
- Are all artifacts (test outputs, command results) actually shown in my response, not just claimed?

If you have enough information, proceed. If anything is ambiguous, ask one focused question first - do not assume.
```

## Когда использовать

- Bug report от user / issue tracker
- "Сделай code review" tasks
- Migrate from old to new pattern (часто всплывают сопутствующие issues)
- Refactor with quality gate
- Anything где agent склонен уходить в "out of scope"

## Когда НЕ использовать

- Чисто research / explore tasks (нечего фиксить)
- "Try this approach" exploratory coding
- Когда explicit short scope нужен (1 файл, 1 функция) - тогда constraints скорее мешают

## Связанное

- **Rule**: [~/.claude/rules/no-pre-existing-evasion.md](../rules/no-pre-existing-evasion.md)
- **Stop hook**: [~/.claude/scripts/stop-test-gate.py](../scripts/stop-test-gate.py) - блокирует "готово" если красный
- **PROBLEMS.md hook**: [~/.claude/scripts/check-problems-md.py](../scripts/check-problems-md.py) - блокирует если OPEN без 5-exception

## Источники

- [Anthropic - Best Practices Opus 4.7](https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code) - literal interpretation
- [bradfeld - Fix or ticket policy](https://gist.github.com/bradfeld/1deb0c385d12289947ff83f145b7e4d2) - 5-exception list
- Research: [research/agentic/2026-05-04-claude-pre-existing-bug-evasion-pattern.md](../../Desktop/CODE_Claude/research/agentic/2026-05-04-claude-pre-existing-bug-evasion-pattern.md)
