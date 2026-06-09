# ACE Context Merge — самоулучшение rules/memory через delta-мёрж, не переписывание

## Принцип (2026-06-09, из Agentic Context Engineering)

Когда CLAUDE.md / rules / memory обновляются «уроками сессии» — **обновлять как
структурированные ДЕЛЬТЫ (диффы), а не переписывать файл целиком**. Полное переписывание
агентом ведёт к **context collapse**: каждый проход размывает/теряет накопленные нюансы,
файл деградирует к более общей и короткой версии. Delta-мёрж сохраняет накопленное и
добавляет/правит точечно.

Источник: [Agentic Context Engineering, arXiv 2510.04618](https://arxiv.org/abs/2510.04618)
(Generator → Reflector → Curator; Curator мёржит инкрементальные дельты; −82% latency и
−75% rollouts vs GEPA, без context collapse). Это принципиальная версия нашего
Session Learning Extraction (CLAUDE.md) и апгрейд `revise-claude-md`.

## Три роли (разделять, не совмещать)

1. **Generator** — делает работу сессии (= обычный рабочий агент). Производит траекторию:
   что сработало, что нет, какие коррекции дал user, какие grNULL/решения.
2. **Reflector** — читает траекторию + **текущий** целевой файл (rule/CLAUDE.md/memory).
   Выдаёт список **кандидатов-дельт**: `ADD` (новый пункт), `EDIT` (уточнить существующий,
   с цитатой старого), `DELETE` (устарело/неверно, с обоснованием). НЕ переписывает файл.
3. **Curator** — детерминированно **применяет** дельты к файлу: ADD дописывает, EDIT —
   точечный search/replace, DELETE — удаляет именованный блок. Дедуп против существующего
   контента. Результат = **дифф**, который верифицируется (git diff), а не свеже-сгенерённый файл.

## Правила delta-мёржа

- **Никогда не отдавать модели «перепиши весь файл».** Только адресные дельты.
- Каждая дельта **самодостаточна**: что меняем + почему + где (цитата якоря для EDIT/DELETE).
- **Dedup обязателен**: перед ADD — проверить, нет ли уже такого пункта (иначе файл пухнет
  дублями — частый failure самоулучшения).
- **Curator ≠ Reflector** (Generator-Evaluator): тот, кто предложил дельту, не подтверждает её
  применение. Применение + verify (git diff читаем глазами/свежим агентом) = proof-loop.
- **Сохранять, не сжимать.** Если правка делает файл «чище» ценой потери нюанса — это
  context collapse, отклонить. Объём растёт медленно и осознанно, а не схлопывается.

## Когда применять

- В конце сессии при извлечении уроков (Session Learning Extraction) — вместо «перепиши CLAUDE.md».
- `revise-claude-md` / `/remember` — прогонять через Reflector→Curator дельты.
- Обновление любого долгоживущего rule/principle/memory по итогам инцидента.
- НЕ нужно для создания НОВОГО файла с нуля (там нечего терять — пиши целиком).

## Mechanical pattern (dynamic workflow)

Реализация — `scripts/ace_context_merge.workflow.js` (запуск через Workflow tool). Скелет:

```
phase('Reflect')
const target = read(targetFile)                 // текущий файл — НЕ переписываем
const deltas = await agent(reflectPrompt(target, trajectory), {schema: DELTA_SCHEMA})
                                                 // [{op:ADD|EDIT|DELETE, anchor, old, new, why}]
phase('Curate')
const deduped = deltas.filter(d => !alreadyPresent(target, d))   // дедуп против файла
const patched = applyDeltas(target, deduped)     // детерминированный аппликатор (search/replace)
// verify: git diff target — читаем глазами / свежим агентом, не trust blindly
```

`DELTA_SCHEMA`: `{op, anchor (цитата места), old_text?, new_text, rationale}`. Curator —
детерминированный JS (применяет дельты), модель только в Reflector. Дорогую модель — на
Reflector (что менять), дешёвую/код — на Curator (как применить) — см. `edit-formats-and-tiering.md`.

## Anti-patterns
- ❌ «Перепиши CLAUDE.md с учётом сессии» → context collapse, потеря нюансов
- ❌ ADD без dedup → файл распухает дублями
- ❌ Reflector сам же и применяет (нет независимой проверки применения)
- ❌ «Почистил, стало короче» как успех — короче ≠ лучше для накопленного контекста
- ❌ Применять к новому файлу (там нет накопленного — пиши целиком)

## Related
- `quality-over-tokens-independent-verify.md` — Reflector/Curator = Generator-Evaluator
- `edit-formats-and-tiering.md` — дельты = search/replace; модель-тиринг Reflector/Curator
- [[practice_autoresearch]] — ACE = его эволюция (delta-мёрж вместо keep/discard целого)
- [[practice_context_engineering]] — контекст как инфраструктура; защита от деградации
- [[article_agent_orchestration_digest_2026_06]] — источник + место в ландшафте 2026
