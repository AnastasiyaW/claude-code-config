# Safety: Destructive Git Operations

## Правило (advice layer)

Git команды которые перетирают историю или теряют uncommitted работу - требуют подтверждения:
- `git reset --hard` - теряется всё uncommitted
- `git push --force` (без `--force-with-lease`) - перезаписывает remote, может затереть чужие commits
- `git branch -D` - удаляет ветку без проверки merged
- `git clean -fdx` - удаляет все untracked + ignored файлы (включая `.env`, node_modules, build artifacts)
- `git checkout -- .` / `git restore .` - уничтожает локальные правки
- `git filter-branch` / `git filter-repo` - переписывает всю историю
- Force delete refs к `main`/`master`/`prod`
- `git gc --prune=now --aggressive` после `reflog expire=now` - физическое удаление unreachable commits

## Hook (mechanical enforcement)

`hooks/git-destructive-guard.py`. Обход: `CLAUDE_ALLOW_GIT_DESTRUCTIVE=1`.

## Безопасные альтернативы

| Деструктив | Безопасный аналог |
|---|---|
| `git reset --hard HEAD` | `git stash` + `git reset --keep` |
| `git push --force` | `git push --force-with-lease` (fails если remote обновился) |
| `git branch -D feature` | `git branch -d feature` (fails если unmerged), потом merge и delete |
| `git clean -fdx` | `git status` + targeted `rm` для конкретных файлов |
| `git checkout -- .` | `git diff` сначала, потом targeted `git checkout -- path` |

## Real-world провалы

- **Production перезаписан**: `git push --force` без проверки что remote обновился. Коллега успел push между fetch и force, его commits затёрты. Восстановление через reflog если повезёт успеть
- **`reset --hard` на untracked работу**: полдня работы, не commit, `git reset --hard HEAD` "чтобы откатить". Файлы ушли из working tree, но IDE-буфер их удерживает - восстановлены из IDE undo history. Не у всех есть этот буфер
- **Проект из подпапки "перенесён"**: при попытке rearrange структуры всё из подпапки уехало, работает только сами имена файлов. Восстановление из README + памяти
- **БД обнулена без бэкапов**: коммит production database scheme с compiled seed data. Force push затёр предыдущую версию. Без retention = без recovery

## Почему `--force-with-lease` важнее `--force`

`--force-with-lease` fails если remote branch получил новые commits с момента твоего последнего fetch. Это защищает от race condition: другой человек pushed, ты не знаешь, твой force затрёт. С `--force-with-lease` push откажется, ты сделаешь fetch+rebase, потом push.

Паттерн архитектурной защиты: некоторые команды выдают GitHub tokens **без прав на удаление** своим агентам. Это мешает force-push/branch delete на уровне API. Наш hook - такая же идея на уровне bash команд.

## Что hook НЕ покрывает

- Force push через другой инструмент (GitHub Desktop, lazygit, IDE plugin) - они не проходят через Bash tool
- `git reflog expire` через aliases
- Rebase -i который "случайно" drop коммиты (interactive rebase не автоматически destructive, но легко стать)

## Tuning

Для проектов где force push норма (например personal repos, feature branches с rewritable history) - добавляй `CLAUDE_ALLOW_GIT_DESTRUCTIVE=1` в `.env` проекта или `.envrc`.

Но для любой команды с shared main/master ветку - hook должен оставаться активным.
