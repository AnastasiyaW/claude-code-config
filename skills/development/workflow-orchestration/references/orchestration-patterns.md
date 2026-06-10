# Orchestration Patterns - какой паттерн выбрать

Типология оркестрации (веб-ресерч best practices 2026 + наш боевой опыт). Дополняет
`SKILL.md` (API, золотые правила) и `lessons-and-gaps.md` (наши грабли). Здесь - КАК
структурировать флоу и КОГДА какой паттерн, плюс safety.

## Граница: subagent vs skill vs workflow (из офиц. рекомендаций)

- **Subagent** - когда нужны 1-2 изолированных исследования за ход (verbose research → чистый
  summary в main-контекст). Правило: бери субагента когда «сэкономленный clutter главного
  контекста стоит больше, чем startup-overhead», а НЕ «субагенты для всего».
- **Skill** - когда know-how должен быть переиспользуемым (инструкции, которые Claude следует).
- **Workflow** - когда сама ОРКЕСТРАЦИЯ должна быть повторяемой: fan-out → сравнить находки →
  перезапустить упавших → сохранить успешный прогон → переиспользовать как команду.

## 5 структурных паттернов (от простого к автономному)

Принцип: **начинай проще, чем кажется нужным; усложняй только когда измеримо упёрся.**

### 1. Sequential (последовательный)
Шаги в предсказуемом порядке, каждый зависит от предыдущего (data pipeline, doc processing).
- Риск: давление на контекст на длинных цепях; ломается при переменной структуре.
- Anti-pattern: длинная sequential-цепь там, где шаги могли бы идти параллельно.

### 2. Operator (оркестратор + субагенты)
Один Claude планирует и делегирует, отдельные агенты исполняют.
- Риск: токен-overhead на reasoning; single point of failure; **застревание в непродуктивных
  циклах без явных termination conditions**.
- Для нас: это обычный subagent-режим Claude (без workflow). Termination = бюджет шагов.

### 3. Split-and-merge (параллелизация) ← наш основной для fan-out
Много независимых однотипных задач. Варианты: **sectioning** (делёж по входу) и **voting**
(N прогонов, выбрать лучший / большинством).
- Риск: **токены растут ПРОПОРЦИОНАЛЬНО** числу веток; сложность merge-шага недооценивают.
- В нашем API: `pipeline` (sectioning, без барьера) или `parallel` + reduce (voting/dedup).
- Merge-шаг - честный код (dedup/голосование), не «ещё один агент на всякий».

### 4. Agent teams (мультиагентная коллаборация)
Разные типы reasoning, peer-review, специалисты. Самый сложный, максимальный coordination
overhead.
- Риск: **ошибки в мультиагентных системах быстро каскадят** (error amplification, см. ниже);
  нужны чёткие роли + handoff-протоколы.
- В нашем API: `Agent Team` внутри `agent()`, либо суб-воркфлоу через `workflow()`.

### 5. Headless (полностью автономный) ← осторожно
`claude -p` / Agent SDK / bypass - без промптов и подтверждений.
- **«Полностью автономный = полностью автономные ошибки.»**
- Бери ПОСЛЕДНИМ: только для well-understood повторяемых задач, после интерактивной обкатки.
- В headless workflow-агенты НЕ спрашивают разрешений → tool-calls идут по правилам без
  подтверждения. Опасно для write/deploy.

## Quality-паттерны (наши, поверх структурных - см. SKILL.md)

adversarial verify · perspective-diverse verify · judge panel · loop-until-dry ·
multi-modal sweep · completeness critic. Это «как повысить доверие», структурные выше - «как
разложить работу». Комбинируются: split-and-merge finders + adversarial verify каждой находки.

**Convergence-driven iteration** (офиц. паттерн): крутить, пока ответы не перестанут меняться.
Наш loop-until-dry - частный случай (K пустых раундов = сходимость).

## Error amplification - главный риск мультиагента

Если один агент выдал плохой output, а другие строят на нём - ошибка распространяется до того,
как кто-то её поймает. Исследования мультиагентных систем: **протоколы коммуникации и error
recovery - самые частые точки отказа.** Наши контрмеры:
- **schema = контракт между стадиями** (типизированный JSON, не сырой текст).
- **adversarial verify** перед тем как находка «folds in» (refute-проход).
- **fail-closed + sentinel-поля** (`confidence`/`needs_human`) - подозрительное не каскадит, а
  идёт в отдельную ветку (см. lessons-and-gaps Gap 3).
- **независимая верификация** (свежий контекст не доверяет предыдущему).

## Headless safety - 4 слоя (если идёшь в claude -p / SDK)

1. **Обкатать интерактивно** на репрезентативной выборке входов ПЕРЕД headless.
2. **Ограничить tool-permissions** (allowlist узкий).
3. **Явные fail-loud error states** (не тихий fallback - совпадает с нашим NO SILENT FALLBACKS).
4. **Confirmation checkpoints для необратимого** + rate limits / circuit breakers на действия с
   prod-данными даже в headless.

## Model-tiering по стадиям (экономия)

Не гнать всё на Opus. Эвристика: Sonnet по умолчанию, Haiku - механическое (bulk extraction),
Opus - только где нужен judgment (architecture, security review, debugging). В workflow:
`agent(prompt, {model: 'sonnet'})` для рутинных стадий, дефолт (модель сессии) - для сложных.
Наше правило субагентов: opus - программирование/архитектура/review; sonnet - bulk «прочитай→
извлеки→запиши».

## Источники (веб-ресерч 2026-05-30)

- [Anthropic blog: Introducing dynamic workflows](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code) - офиц. рекомендации (scoped task first, converge, admin disable)
- [Claude Code Docs: workflows](https://code.claude.com/docs/en/workflows) - API ground truth
- [MindStudio: 5 workflow patterns](https://www.mindstudio.ai/blog/claude-code-5-workflow-patterns-explained) - типология sequential→headless + safety
- [alexop.dev: deterministic orchestration](https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/) - pipeline vs parallel, loop-until-dry
- Token-оптимизация: [systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation), [Claude Code costs docs](https://code.claude.com/docs/en/costs)
