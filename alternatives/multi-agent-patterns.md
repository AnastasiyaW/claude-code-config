# Multi-Agent Patterns - когда и как использовать несколько агентов

## Проблема

Один агент = один контекст. На сложных задачах контекст забивается, качество падает. Multi-agent позволяет разделить ответственность.

## Почему большинство НЕ использует multi-agent

1. **Overhead координации** - агенты должны "договориться", это токены
2. **Сложность отладки** - где именно сломалось?
3. **Нет готового tooling** - нужно самому писать orchestration
4. **Solo agent "достаточно хорош"** для 80% задач

## Когда multi-agent оправдан

| Сигнал | Один агент | Multi-agent |
|--------|-----------|-------------|
| Файлов в задаче | 1-3 | >5 |
| Нужен ревью | Нет | Да (Generator + Evaluator) |
| Задача > 30 мин | Контекст деградирует | Каждый агент = чистый контекст |
| Параллельные subtasks | Последовательно | Одновременно |
| Нужны разные "взгляды" | Один промпт | Security + Performance + UX agents |

## Паттерны

### 1. Generator-Evaluator (GAN-inspired)

```
Generator → код → Evaluator → feedback → Generator → ...
```

Из Anthropic Harness Design. Ключевое: evaluator = **отдельный контекст**.
Модели хвалят свою работу (self-evaluation bias).

**Стоимость:** Solo ~$9 vs Full harness ~$200. 20x cost → качественный скачок.

### 2. Coordinator + Specialists

```
Coordinator → распределяет задачи
  ├── Frontend agent
  ├── Backend agent  
  ├── Test agent
  └── Security agent
```

Координатор не пишет код. Sub-agents специализированы.
Координация через shared artifacts (файлы в репо).

### 3. CORAL Pattern (MIT/Meta, 2026)

```
Agent 1 ──┐
Agent 2 ──┤── shared knowledge layer (.coral/public/)
Agent 3 ──┤     ├── attempts/ (evaluations)
Agent 4 ──┘     ├── notes/ (observations)
                └── skills/ (reusable procedures)
```

Ключевое: **heartbeat mechanism**
- Каждые 10 evaluations → forced reflection + knowledge sharing
- 5 consecutive failures → stagnation redirection (pivot)
- Результат: 3-10x efficiency vs linear approaches

### 4. Proof Loop (spec → build → verify)

```
Spec-freezer → AC1, AC2... (read-only)
Builder → implements (write)
Verifier → fresh session, verdict.json (read-only)
Fixer → minimal fixes (write)
```

4 роли с жёсткими границами. Verifier = **fresh session** (не видел build).

## Реализация в Claude Code

### Простой: Agent tool с разными промптами

```
# Security review
Agent(prompt="Review for OWASP top 10. Files: X, Y. Format: JSON with severity.")

# Performance review  
Agent(prompt="Check for N+1 queries, missing indexes, unnecessary allocations.")
```

### Средний: Parallel agents

```
# Запустить 3 ревьюера параллельно
Agent(name="security", prompt="...", run_in_background=True)
Agent(name="performance", prompt="...", run_in_background=True)  
Agent(name="architecture", prompt="...", run_in_background=True)
```

### Продвинутый: Shared knowledge через файлы

```
# Агенты пишут результаты в shared файлы
.agents/
  ├── security-findings.md
  ├── performance-findings.md
  └── architecture-findings.md

# Coordinator читает все findings и синтезирует
```

## Context hint для субагентов

При запуске Agent tool - явно указать контекст:
- Не "send everything" (перегруз)
- Не "send nothing" (потеря контекста)
- В prompt включить: (1) что делаем, (2) только релевантный state, (3) constraints

## Anti-patterns

- Запускать субагент для задачи на 5 строк кода
- Координатор который тоже пишет код (путает роли)
- Нет shared artifacts (агенты не видят работу друг друга)
- Доверять claim субагента "я проверил, всё ок" без durable evidence
