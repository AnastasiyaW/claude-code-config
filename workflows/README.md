# Dynamic Workflows — готовые команды

Claude Code **dynamic workflows** = детерминированный JS-скрипт, который оркестрирует
субагентов по «рельсам» (надёжнее, чем агент «по настроению»). Research preview с
2026-05-28, требует Claude Code **v2.1.154+**. На Pro включается в `/config` →
Dynamic workflows (по дефолту выкл — жжёт токены, см. `rules/safety-billing.md` Риск 4).

Как писать такие скрипты — skill `workflow-orchestration`
([skills/development/workflow-orchestration/](../skills/development/workflow-orchestration/)).
Этот каталог — готовые команды-примеры + боевые уроки.

## Установка

Скопировать `.js` в `~/.claude/workflows/` (глобально) или `.claude/workflows/` проекта.
Команда становится доступна как `/имя-файла`.

## Команды

| Команда | Что делает | Как звать |
|---|---|---|
| `/deep-review-flow` | Competency-review кода (security/perf/arch/concurrency/errors/tests) с adversarial-проверкой каждой находки + карточка на косяк + triage FIX/DEFER/ACCEPT | `/deep-review-flow` |
| `/research-cn-ru` | Research с обязательными китайскими (Alibaba/Tencent/DeepSeek, ModelScope, Zhihu) и русскими (Хабр, TG) источниками, не только англо-веб | `/research-cn-ru <вопрос>` |

Параметры (`args`) у каждой — в шапке соответствующего `.js`.

## Базовый цикл

1. **Вызов.** `/имя-команды` (или попросить «запусти workflow, который …» — скрипт будет
   написан на лету).
2. **Approve.** Claude Code покажет план фаз + предупреждение о токенах. `View raw script` —
   посмотреть скрипт до запуска. **Yes** — запустить.
3. **Прогресс.** `/workflows` → стрелками выбрать прогон → `Enter`. Видно фазы, число
   агентов, токены, время; можно зайти в агента и прочитать его промпт/результат.
4. **Стоп без потерь.** `x` останавливает прогон; завершённые агенты не теряются
   (resume-кэш в той же сессии).

## Боевые уроки

[EFFECTIVE-AGENTS.md](EFFECTIVE-AGENTS.md) — замеры стоимости (один `agent()` ≈ 95k-150k
токенов), resume как главный рычаг экономии, типовые грабли. Прочитать ДО первого большого
прогона.
