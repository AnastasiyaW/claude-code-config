# Safety: Backup Retention

## Правило (advice layer)

`auto_backup_git.py` создаёт recovery branches (`claude-backup-{ts}`) и stashes (`claude-pre-clean-{ts}`) перед destructive git operations. Они не должны накапливаться бесконечно - через 14 дней retention истёк.

## Hook (Stop event cleanup)

`~/.claude/scripts/cleanup_backup_branches.py` срабатывает на завершении каждой сессии. Silent в non-git directories. Удаляет:
- Branches matching `claude-backup-\d+` с timestamp > 14 дней назад
- Stashes matching `claude-pre-clean-\d+` с timestamp > 14 дней назад

Безопасно - идемпотентно, не трогает branches/stashes которые не соответствуют ожидаемому формату. Если `git branch -D` упадёт (unmerged branch - unlikely для backup от тебя же) - hook log WARN и продолжит с другими.

## Настройки

Константа `RETENTION_DAYS = 14` в начале скрипта. Править если нужно другое retention:
- 7 дней - агрессивно, но для активной разработки 7 дней достаточно чтобы вспомнить что именно нужно восстановить
- 30 дней - консервативно, backup веток становится много (50-100)
- 1 день - не рекомендую, можно потерять recoverable state прежде чем сам поймёшь что нужно

## Safety considerations

Hook сам делает `git branch -D` - это destructive операция. Но:
1. Запускается на Stop event (не через Bash tool), значит PreToolUse hooks типа block_git_destructive не срабатывают
2. Удаляет только то что сам создал (`claude-backup-*`, `claude-pre-clean-*`)
3. Timestamp в имени - проверяется численно, невалидные форматы игнорируются
4. Работает в current working directory, не шарит все drives

## Рекомендуемый workflow

В долгих проектах периодически проверять:
```bash
git branch | grep claude-backup- | wc -l
git stash list | grep claude-pre-clean- | wc -l
```

Если числа больше 50 - retention не работает (может Stop hook не сработал) - запустить manually:
```bash
python ~/.claude/scripts/cleanup_backup_branches.py
```

Для случая когда нужно сохранить specific backup навсегда:
```bash
git branch -m claude-backup-1745000000 kept-refactor-checkpoint
# переименование убирает из retention pattern
```

## Что hook НЕ покрывает

- Backups в других git repositories (cleanup работает только в cwd)
- Backups созданные вручную (не через auto_backup_git.py)
- Remote backups (push на remote claude-backup-* - hook не удаляет remote refs, только local)

Для пункта "работать во всех repos" - можно написать cron job на user level который обходит все git repos в home.

## Что hook делает когда нечего чистить

Silent. Никакого вывода, никакого log write. Не раздражает пользователя в каждой сессии.

## Log output

Если удалил что-то, пишет в stderr:
```
[cleanup-backup] Retention: removed 3 old claude-backup branch(es), 1 old claude-pre-clean stash(es) (older than 14 days)
```
