---
name: harness-design
description: >
  Design and build multi-agent harness architectures for long-running AI application
  development. GAN-inspired Generator-Evaluator pattern, Sprint Contract negotiation,
  context management, quality criteria calibration. Based on Anthropic Engineering patterns.
  Use when: "build a harness", "multi-agent architecture", "agent orchestration",
  "generator-evaluator", "long-running app", "harness design", "agent pipeline",
  "quality evaluation loop", "sprint contract", "build app with agents",
  "Claude Agent SDK architecture", or when building complex full-stack apps
  that need planning → generation → evaluation cycles. Also use when discussing
  context degradation, self-evaluation bias, or assumption testing in AI workflows.
user-invocable: true
model: opus
---

# Multi-Agent Harness Design

Источники:
- Anthropic Engineering — "Harness design for long-running apps"
- OpenClaw-RL paper (arxiv 2603.10165) — personal agent verification
- DenisSergeevitch/repo-task-proof-loop — execution protocol with durable proof

См. также: `references/proof-loop-research.md` — детали paper + repo mapping

## Когда нужен harness, а когда хватит solo agent

| Сигнал | Solo agent | Harness |
|--------|-----------|---------|
| Scope | Одна фича, bug fix, refactor | Full-stack app, multi-feature product |
| Длительность | < 30 мин | 1-6+ часов |
| Качество | Baseline достаточно | Нужен polish, originality, craft |
| Стоимость | ~$5-15 | ~$100-200+ |
| Проверка | Manual review | Automated evaluation + Playwright |

**Правило:** Evaluator оправдан когда задача **за пределами reliable solo performance**. Не фиксированное yes/no — зависит от complexity tier.

---

## Архитектура: Three-Agent System

### 1. Planner (Планировщик)
- Расширяет 1-4 предложения пользователя в **детальную спецификацию**
- Амбициозный scope — находит возможности для AI-фич
- **НЕ** over-specify реализацию — только what, не how
- Вписывает AI features в продукт органично

### 2. Generator (Генератор)
- Реализует фичи итеративно
- Включает **self-evaluation** перед handoff (но она ненадёжна — см. ниже)
- Работает в рамках Sprint Contract

### 3. Evaluator (Оценщик)
- **Независимый** от генератора — отдельный контекст, отдельный промпт
- Валидирует через Playwright MCP — скриншоты, навигация, тесты
- Откалиброван через few-shot примеры
- Ловит то, что self-evaluation пропускает

---

## Sprint Contract Pattern

Перед каждой итерацией:

```
1. Planner определяет фичу и user story
2. Generator и Evaluator ДОГОВАРИВАЮТСЯ о:
   - Что значит "done" для этой фичи
   - Конкретные testable success criteria
   - Что НЕ входит в scope
3. Generator реализует
4. Evaluator валидирует по контракту
5. Если не пройдено → конкретный feedback → повтор с п.3
```

**Контракт = мост** между user stories и implementation. Без него evaluator судит по своим критериям, generator не знает что проверять.

---

## Generator-Evaluator: Почему раздельно

### Self-evaluation bias
Модели **уверенно хвалят свою работу** — даже когда качество посредственное. Это не баг модели, а свойство: генератор оптимизирован на producing, не на judging.

### Решение: Independent evaluator
- Другой system prompt с calibrated skepticism
- Few-shot примеры с **детальными score breakdowns**
- Тестирует через browser, не через чтение кода
- Конкретные failure criteria, а не общие "looks good"

### Калибровка оценщика (QA Tuning Loop)
```
1. Evaluator выдаёт оценку
2. Ты проверяешь: согласен ли с оценкой?
3. Расхождение → обновляешь QA промпт
4. Типичные проблемы:
   - Superficial testing, пропускает edge cases
   - Premature approval посредственной работы
   - Слишком строгие критерии → бесконечные итерации
5. Повторяешь пока evaluator judgment ≈ твой judgment
```

---

## Quality Criteria Framework (для фронтенда)

### 4 измерения, каждое 0-10:

**1. Design Quality** — Целостность
> Дизайн ощущается как единое целое, а не коллекция частей?
- Интеграция color, typography, layout, imagery
- Consistent visual language

**2. Originality** — Уникальность
> Штраф за:
- Template layouts, library defaults
- AI slop patterns: purple gradients over white cards
- "Telltale signs of AI generation"
- Cookie-cutter структуры

**3. Craft** — Техническое мастерство
- Typography hierarchy
- Spacing consistency
- Color harmony, contrast ratios
- Pixel-perfect alignment

**4. Functionality** — Работоспособность
> Пользователь завершает задачу без угадывания?
- Все интерактивные элементы работают
- Нет stub features
- Error states обработаны

### Влияние формулировок на генерацию
Фразы в criteria **прямо влияют** на вывод генератора:
- "museum quality" → visual convergence к одному стилю
- "best designs" → перфекционизм за счёт creativity
- **Тестируй формулировки** — они стируют модель ДО оценки

---

## Контекст-менеджмент

### Context Degradation
Модели теряют coherence по мере заполнения context window.

**Context reset > Compaction:**
- Compaction сохраняет continuity, но не даёт чистый лист
- Reset + structured handoff artifact = лучший баланс
- Handoff artifact = документ с state, decisions, progress

### Context Anxiety
Модели (особенно Sonnet) начинают **сворачивать работу раньше времени** — думают что контекст кончается.
- Решение: clean context resets
- Opus 4.6: проблема значительно уменьшена

### Structured Handoff
При context reset передавать:
```
- Что уже сделано (с конкретными файлами/строками)
- Какие решения приняты и почему
- Что осталось сделать
- Текущие проблемы и blockers
- Sprint contract для текущей итерации
```

---

## Assumption Testing

> "Every component in a harness encodes an assumption about what the model can't do on its own"

### Принцип: предположения устаревают
- Модели улучшаются → scaffolding requirements снижаются
- Sprint decomposition нужно было для Sonnet → Opus 4.6 может без него
- **Стратегия**: убирать компоненты по одному, измерять влияние

### Simplification Loop
```
1. Текущий harness работает? Да →
2. Убери один компонент (напр. sprint decomposition)
3. Качество упало? Да → верни. Нет →
4. Повтори с другим компонентом
5. Остановись на минимальном harness для текущей задачи
```

---

## Реальные failure modes (пойманные evaluator'ом)

- Rectangle fill tool ставит тайлы только на endpoints drag, вместо заполнения области
- Delete key handler требует два условия, когда нужно одно
- FastAPI route matching: "reorder" матчится как integer frame_id
- Audio recording: stub без mic capture
- Missing clip resize/split operations
- Effect visualizations как числовые слайдеры вместо графики
- Display-only features без интерактивности
- Missing instrument panels
- Unimplemented recording functionality

---

## Инструментарий

### Claude Agent SDK
- Handles agent orchestration + compaction автоматически
- Manages context growth across long sessions
- Рекомендуемый стек для production harnesses

### Playwright MCP
- Evaluator навигирует запущенное приложение
- Скриншоты перед grading
- Тестирует UI features, API endpoints, database states

### Рекомендуемый стек
- Frontend: React + Vite / Nuxt + Vue
- Backend: FastAPI / Fastify
- Database: SQLite (dev) → PostgreSQL (prod)
- Version Control: Git integration
- Testing: Playwright MCP для automated evaluation

---

## Gotchas

- **Language shapes output**: формулировки в criteria сдвигают генератор ДО обратной связи от оценщика. "Museum quality" → convergence, "experimental" → divergence
- **Creative leaps happen late**: в итерации 9 — стандартный dark theme, в итерации 10 — CSS 3D perspective room. Не останавливай цикл слишком рано
- **Cost scales with iteration**: каждый round ≈ $20-40. 5 rounds = $100-200. Budget accordingly
- **Evaluator needs tuning**: первая версия QA промпта почти всегда слишком мягкая. Планируй 3-5 итераций калибровки
- **Self-evaluation is seductive**: генератор БУДЕТ говорить "всё отлично" — не верь, проверяй через independent evaluator

## Troubleshooting

| Симптом | Причина | Решение |
|---------|---------|---------|
| Evaluator всё одобряет | Промпт слишком мягкий | Добавь few-shot с detailed score breakdowns, конкретные failure criteria |
| Generator не улучшается | Feedback слишком абстрактный | Evaluator должен давать конкретные файлы/строки/проблемы |
| Бесконечные итерации | Criteria невыполнимы | Пересмотри контракт, снизь планку или split задачу |
| Context degradation | Длинная сессия без reset | Structured handoff + clean context reset |
| Все итерации выглядят одинаково | Criteria слишком узкие | Расширь пространство, убери "museum quality" формулировки |
| Evaluator ловит мелочи, пропускает крупное | Wrong priority в промпте | Restructure: critical → high → medium → cosmetic |
