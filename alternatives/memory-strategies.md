# Memory Strategies - verbatim vs extraction vs hybrid

## Проблема

AI-агенты теряют контекст между сессиями. Как хранить память эффективно?

## Три подхода

### 1. Extraction (текущий default в Claude Code)

```
Диалог → LLM извлекает факты → key-value summary → .md файл
```

**Пример:**
```markdown
---
name: user_preferences
type: user
---
Предпочитает PostgreSQL для проектов с JSONB.
Не использует ORM, пишет SQL напрямую.
```

**Плюсы:** компактно, быстро читается, дёшево по токенам
**Минусы:** теряет WHY ("предпочитает PostgreSQL" - но почему? из-за JSONB? опыта? миграции?)

### 2. Verbatim (MemPalace approach)

```
Диалог → raw текст сохраняется целиком → поиск по embeddings
```

**Данные MemPalace:** verbatim + ChromaDB embeddings = 96.6% recall на LongMemEval.
Extraction-based системы (Mem0, Zep) = ~85%. Разница = 11.6%.

С Haiku rerank ($0.001/query) → 100%.

**Плюсы:** ничего не теряется, контекст и причины сохранены
**Минусы:** нужен vector DB, больше токенов при retrieval, сложнее инфра

### 3. Hybrid (рекомендуемый)

```
Диалог → extraction для L0/L1 (всегда загружается)
       → verbatim для L2/L3 (загружается по запросу через поиск)
```

**4-слойная модель (из MemPalace):**

| Слой | Что | Токены | Когда |
|------|-----|--------|-------|
| L0 | Identity (кто пользователь) | ~50 | Всегда |
| L1 | Critical facts (правила, запреты) | ~120 | Всегда |
| L2 | Project context | ~500 | По запросу |
| L3 | Historical details | ~2000 | По запросу |

**L0+L1 = ~170 токенов на старте. $10/год vs $507/год для full loading.**

## Реализация в Claude Code

### Без vector DB (чистый markdown)

Layered loading через MEMORY.md:
```markdown
## Always Load (L0+L1)
- [user_profile](user_profile.md) — identity
- [rules](feedback_*.md) — критичные правила

## On Demand (L2+L3)
- [projects](project_*.md) — загружать когда тема релевантна
- [articles](article_*.md) — справочно
```

### С vector DB (для >200 memory записей)

Если записей больше ~200, линейный поиск по MEMORY.md перестаёт работать:
- ChromaDB (local, Python) или SQLite FTS5
- Embedding при сохранении, similarity search при загрузке
- MemPalace-style hierarchical tags для filtering

## Temporal validity

Добавить `created: YYYY-MM-DD` в frontmatter каждой memory записи.
При использовании записи старше 30 дней - проверять актуальность.

```yaml
---
name: project_api_rewrite
type: project
created: 2026-03-15
---
```

## Когда какой подход

| Ситуация | Подход |
|----------|--------|
| <50 memory записей | Extraction + layered MEMORY.md |
| 50-200 записей | Hybrid (L0/L1 extraction + L2/L3 on demand) |
| >200 записей | Vector DB (ChromaDB) + hierarchical tags |
| Критично не терять контекст | Verbatim + rerank |
| Экономия токенов приоритет | Extraction only |
