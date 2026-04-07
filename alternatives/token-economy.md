# Token Economy - экономия токенов в AI-агентах

## Проблема

Токены = деньги. Claude Code может тратить 180 токенов на "I'd be happy to help you with that. Let me search the web for you." когда достаточно 2 токена: "Tool work".

## Caveman Prompting

Источник: 16-летний SaaS-разработчик, Derp Learning (апрель 2026)

**Идея:** научить агента говорить минимально, как пещерный человек.

| Обычный Claude | Caveman Claude |
|----------------|----------------|
| "I executed the web search tool and found relevant results" (8 tok) | "Tool work" (2 tok) |
| "Let me analyze the codebase to understand the architecture" (10 tok) | "Read code" (2 tok) |
| "I'd be happy to help you with that request" (9 tok) | (ничего, сразу делает) |

**Результат: 75% экономия токенов** (180 → 45 на задачу).

## Где применять

### 1. Sub-agents (Agent tool)

При запуске субагентов через Agent tool - добавить в промпт:
```
Respond minimally. No preamble, no summaries. 
Action → result. Skip "I'll", "Let me", "I found".
```

Субагенты не видны пользователю - красивый текст не нужен.

### 2. Internal reasoning

В системных промптах для внутренних операций:
```
Output: facts only. No explanations. No transitions.
Format: bullet points, no prose.
```

### 3. Batch operations

При обработке 10+ файлов, не писать "Processing file X..." для каждого.

## Где НЕ применять

- Ответы пользователю (нужна понятность)
- Обучающие объяснения (нужна детальность)
- Первый ответ в сессии (нужен контекст)
- Debugging output (нужна полнота)

## Количественные ориентиры

| Операция | Обычно | Caveman | Экономия |
|----------|--------|---------|----------|
| Web search + отчёт | ~180 tok | ~45 tok | 75% |
| File analysis | ~300 tok | ~80 tok | 73% |
| Multi-file refactor (10 files) | ~2000 tok | ~500 tok | 75% |
| Sub-agent research task | ~1500 tok | ~400 tok | 73% |

## Реализация в Claude Code

### Через prompt для субагентов
```python
Agent(prompt="""
[CAVEMAN MODE] Terse output. No preamble. Facts only.
Task: {task}
""")
```

### Через CLAUDE.md секцию
```markdown
## Token Economy
- Sub-agents: minimal output, no preamble
- Batch ops: no per-item status messages
- Internal: bullet points, no prose
```

## Связь с другими практиками

- **Layered memory loading** - загружать только нужное = меньше input токенов
- **JIT context** - не загружать весь проект, а только релевантные файлы
- **Context Engineering** - pruning + re-inject вместо полного контекста
