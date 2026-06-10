---
paths:
  - "**/*.css"
  - "**/*.scss"
  - "**/*.html"
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.vue"
  - "**/*.svelte"
---

# Post-UI-Change Design Review — Convention

## Принцип (2026-05-14, user explicit «пусть агенты перепроверят качество вёрстки после каждого шага вёрстки»)

После КАЖДОГО изменения CSS / HTML / DOM-структурного JS в frontend-проекте — **спавнить isolated design-review subagent** для независимой quality check.

Не trust собственному eye — модель хвалит свою работу (self-evaluation bias, см. CLAUDE.md «Generator-Evaluator Pattern»).

## Когда применять

**Триггеры (после tool use на этих files):**
- `Edit` / `Write` на `*.css` (любые стили)
- `Edit` / `Write` на `*.html` с visible markup (не на script-only / config)
- `Edit` / `Write` на `*.js` где меняется DOM structure (создаются/удаляются elements; meaningful class toggles)

**Не триггерить для:**
- Чистый JS logic refactor (без DOM mutation)
- Comments-only changes
- Cache version bumps (только query string)
- Backend / server scripts
- Memory files / docs / SPEC documents

## Workflow

После каждого подходящего change (или batch из 2-3 связанных):

1. **Bump cache** (`?v=...`) если CSS/JS изменилось — без этого preview reload не подтянет.
2. **Reload preview** (headless browser / preview tool с `location.reload()`; restart preview если tab stuck).
3. **Wait initial paint** (sleep 5-10s — на больших DOM-страницах headless медленный).
4. **Spawn design-review agent** через Agent tool:
   ```
   subagent_type: "frontend:design-review" (если skill активен) или "general-purpose"
   description: "Post-edit design review of <component>"
   prompt: <self-contained, см. template ниже>
   ```
5. **Agent verdict**:
   - PASS → log в session handoff «design-review @ <timestamp>: PASS, ничего не trip'нуто»
   - NEEDS-FIX → читать findings, точечно править, GOTO step 1 (новая итерация)
   - REJECT → roll back последний edit, переосмысливать архитектуру

## Agent prompt template

Self-contained (новая сессия без знания контекста); подставить свой проект/URL/SPEC:

```markdown
Контекст: ты независимый design QA в проекте <project>. Текущий live URL — <url> (cache `?v=<X>`).

Я (предыдущая сессия) только что изменила: <one-line>
Файлы изменены: <list>
Что должно работать: <expected behavior>
SPEC: <path к canonical таблице interactions, если есть>

Задача: открой preview (headless browser / preview tool), сделай:
1. Smoke check — readyState=complete, no console errors, ключевые classes на месте.
2. Visual quality (через inspect / screenshot, не через memory):
   - Spacing/alignment не сломан
   - Typography hierarchy clear
   - Color contrast легит
   - Layout: плотное плотно, растянутое растянуто
3. Functional probe — кликни ключевой контрол, verify side-effects (localStorage / dataset / DOM).
4. Compare to SPEC: ВСЕ ли поведения из таблицы соответствуют реальности?

Verdict (200 слов max):
- **PASS** + ничего не trip'нуто
- **NEEDS-FIX** + конкретный список (file:line + что починить + почему)
- **REJECT** + причина невозможности continue + recommended rollback step

НЕ доверяй моему reasoning, проверяй state в живом preview.
```

## Cache management

Чтобы независимый agent видел свежую версию:
- Bump query string `?v=YYYYMMDD<letter>` (a-z incremental в течение дня)
- Agent читает live state через preview tools, не cached browser state
- Verify свежесть: `[...document.styleSheets].map(s => s.href)` должен содержать current `?v=...`

## Скорость / cost

- 1 design-review agent ~30-60 sec в реальном времени, ~$0.05-0.15 cost
- Не нужно spawn'ить на каждый mini-edit — **батчить 2-3 связанных** и review единым проходом
- Для critical paths (миграции режимов, layout refactor) — review **обязательно**, даже на single edit
- Для cosmetic tweaks (color hex change, padding adjust) — opt-in

## Anti-patterns

- ❌ Skip review «потому что я уверена что код правильный» — exactly когда reviewer ловит баг
- ❌ Review через **ту же** preview tab где работаешь (cached state) — нужна fresh eval
- ❌ Agent prompt без SPEC link → agent проверяет общие UX heuristics, не ваши conventions
- ❌ После 5 «NEEDS-FIX» подряд в одном edit — это сигнал переосмыслить архитектуру, не точечно патчить

## Связь с другими правилами

- **CLAUDE.md «Generator-Evaluator Pattern»** — теоретическая база, defence-in-depth
- **rules/no-guessing.md** — design-review = independent verifier для UI claims

## Mechanical enforcement (TBD)

Hook idea: `PostToolUse` на `Edit/Write` for `*.css/*.html`. Detect changes, append session-state marker "ui-edit-pending-review". При `Stop` event — блокировать завершение, если есть pending-review без recorded outcome.

Implementation deferred. Сейчас — culture + чек-лист.
