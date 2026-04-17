# Safety: Auto-Backup Before Destructive Git Ops

## Правило (advice layer)

Если destructive git операция действительно намеренна (есть bypass `CLAUDE_ALLOW_GIT_DESTRUCTIVE=1`) - перед её выполнением должен существовать safety net. Undo должен быть возможен даже если операция пошла не так.

## Hook (automatic safety net)

`~/.claude/scripts/auto_backup_git.py`. Работает как wrapper: перед destructive command автоматически создаёт recovery point.

Триггеры + действия:
- `git reset --hard *` → `git branch claude-backup-{unix_ts}`
- `git checkout -- .` → `git branch claude-backup-{unix_ts}`
- `git clean -fdx` → `git stash push -u -m 'claude-pre-clean-{ts}'`

Срабатывает ТОЛЬКО если основной `block_git_destructive.py` уже bypassed (иначе операция и так заблокирована). То есть:
- Без bypass: block_git_destructive блокирует команду
- С bypass: block_git_destructive пропускает, auto_backup_git создаёт backup, потом команда исполняется

## Recovery примеры

**После `git reset --hard HEAD~5` с auto-backup**:
```bash
# auto-backup уже создал branch claude-backup-{ts}
git log claude-backup-{ts}  # увидеть что было
git checkout claude-backup-{ts}  # вернуться
# или cherry-pick конкретные коммиты обратно
```

**После `git clean -fdx` с auto-backup**:
```bash
git stash list  # найти claude-pre-clean-{ts}
git stash pop stash@{N}  # восстановить рабочее дерево
```

## Real-world inspiration

Из чата разработчиков:
> "делал reset head hard и потом я доставала из хэша IDE данные файлов"

IDE undo history как последняя линия обороны - не у всех есть, и ненадёжно. Explicit backup branch = всегда доступен, всегда предсказуем.

## Что hook НЕ покрывает

- Force push - backup branch local, remote уже перезаписан. Для push защита другая: всегда использовать `--force-with-lease`, не raw `--force`.
- `git gc --prune=now` - физически удаляет unreachable commits. Если backup сделан после уже выполненного reset+gc - поздно.
- `git filter-repo` / `filter-branch` - переписывает ВСЮ историю. Backup branch поможет, но ghost branches могут остаться.
- Операции на несуществующем git repo - hook silent.

## Взаимодействие с block_git_destructive

Порядок в settings.json важен:
1. block_git_destructive - первый gate (блокирует без bypass)
2. auto_backup_git - второй layer (создаёт safety net если bypass)

Оба в PreToolUse для Bash. Оба проверяют один и тот же regex pattern. Первый блокирует, второй страхует.

## Tuning

Retention: backup branches накапливаются. Добавить в workflow weekly cleanup:
```bash
# Удалить claude-backup branches старше 14 дней
git branch | grep 'claude-backup-' | while read b; do
    ts=$(echo "$b" | sed 's/.*-//')
    age=$(( ($(date +%s) - ts) / 86400 ))
    [ "$age" -gt 14 ] && git branch -D "$b"
done
```

Stash retention - управляется через `git stash drop` вручную или `git stash clear` для массовой очистки (осторожно).
