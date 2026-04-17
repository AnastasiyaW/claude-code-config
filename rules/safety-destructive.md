# Safety: Destructive Commands

## Правило (advice layer)

Перед любой деструктивной командой - подтверждать у пользователя. Деструктивные = те, которые НЕЛЬЗЯ откатить без бэкапа:
- `rm -rf /`, `rm -rf ~`, `rm -rf *` в корневых директориях
- SQL: `DROP TABLE|DATABASE|SCHEMA`, `TRUNCATE TABLE`, `DELETE FROM x` без `WHERE`
- Контейнеры: `docker system prune -a --volumes`, `docker-compose down -v`, mass `docker rm -f`
- K8s: `kubectl delete namespace`, `kubectl delete --all`
- Диск: `mkfs`, `dd if=x of=/dev/...`

## Hook (mechanical enforcement)

Скрипт `hooks/destructive-command-guard.py` срабатывает PreToolUse на Bash и останавливает выполнение.

Регистрация в `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python /abs/path/to/hooks/destructive-command-guard.py"
      }]
    }]
  }
}
```

Обход (только когда пользователь явно подтвердил): `CLAUDE_ALLOW_DESTRUCTIVE=1` в той же сессии перед командой.

## Почему два слоя

Rule можно "забыть" под context pressure, особенно в длинной сессии или после compaction. Hook - не может: каждый Bash tool call проходит через него механически. Это IAEA defence-in-depth принцип (INSAG-10): несколько независимых барьеров защиты.

## Real-world провалы которые этот hook предотвращает

Коллекция провалов из практики AI-coding сообщества (апрель 2026):

- **Codex quoting bug**: создавая GitHub issue через `gh`, неверно escaped кавычки привели к тому что substring `dropdb ...` внутри текста тикета **выполнился** как отдельная команда. Локальная база дропнута
- **Debug-сессия на проде**: агенту поручили отладить скрипт синка Grafana дашбордов на "боевой" Grafana. После нескольких попыток агент удалил всю Grafana
- **"Снести и переустановить"**: на проде без бэкапа - классика. Часто в попытке "починить" какой-то сервис
- **Тесты дропают прод**: тесты случайно лазят в продовую базу и рандомно дропают таблицы. Особенно коварно потому что не каждый раз - выглядит как flakiness

## Что hook НЕ покрывает

- Деструктив через длинные цепочки скриптов (скрипт пишется, потом запускается - hook видит только `./script.sh`)
- Shell aliases которые скрывают реальную команду
- Database клиенты запускающие query из файла (`psql -f drop.sql`) - файл не виден в Bash command
- Python/Node код вызывающий DB client API напрямую

Этот gap требует или код-ревью файлов перед запуском, или дополнительного hook на PostToolUse Write с проверкой содержимого новых .sh/.sql файлов.

## Tuning

Паттерны в начале `destructive-command-guard.py` в массиве `PATTERNS`. Настроены так чтобы:
- `rm -rf /tmp/anything` - проходит (tmp обычно безопасен)
- `rm -rf /` или `rm -rf /etc/*` - блокируется
- `rm -rf ~` или `rm -rf $HOME` - блокируется

Если появляются false positives в твоём workflow - сужай regex, не убирай categorу целиком. Лучше специфичная exception чем broad disabled rule.
