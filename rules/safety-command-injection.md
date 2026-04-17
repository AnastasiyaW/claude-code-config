# Safety: Command Injection via Shell Substitution

## Правило (advice layer)

Shell substitution (`$(...)` и backticks) внутри больших команд - главный класс non-obvious багов где текст становится командой. Это не про "не используй $()", это про "в каких контекстах $() исполняется до того как ты думаешь".

Суть проблемы:
```bash
gh issue create --body "Текст тикета с командой $(dropdb prod)"
```

Ты думал: строка с литеральным описанием. Shell думал: выполни dropdb, результат вставь в body. Результат: база дропнута.

## Hook (mechanical enforcement)

`~/.claude/scripts/block_command_injection.py` смотрит на каждую Bash команду и:
1. Находит все `$(...)` и `` `...` `` substitutions
2. Для каждой проверяет body:
   - **Trivial** (`pwd`, `date`, `whoami`, `hostname`, `id`, `uname`, `basename`, `dirname`, `echo`, etc) → проходит молча
   - **Destructive verb inside** (`dropdb|rm -rf|kubectl delete|killall|shutdown|curl...|sh`) → hard block
   - **Non-trivial** (любая команда не из whitelist) → advisory block

Обход: `CLAUDE_ALLOW_INJECTION=1`.

## Real-world проявление

Классический случай из Telegram чата AI-разработчиков 16 апреля 2026:
> Codex недавно. Ему надо было создать github issue на базе плана, в плане была команда дропа локальной базы. Codex напутал с кавычками, вместо прокидывания текста тикета как аргумента к gh, команда сама выполнилась и дропнула локальную базу.

Вариации этого же паттерна:
- `echo "Деплой в $(dropdb staging)"` - лог с "сайд эффектом"
- `curl -X POST --data "$(генерация payload)"` - payload включает substitution которое агент написал для "удобства"
- `grep "$(cat secrets.txt)"` - прочитал secrets.txt, вставил в grep pattern, если secrets.txt содержит shell metacharacters - interpretation
- `slack-notify "Result: $(последняя команда которая почему-то падает и роняет весь скрипт)"`

## Защита которая работает без hook

**Одинарные кавычки вместо двойных** - всё внутри `'...'` literal, substitution не срабатывает:
```bash
gh issue create --body 'Текст с $(dropdb)'  # safe - literal
```

**Heredoc без expansion**:
```bash
gh issue create --body "$(cat <<'EOF'
Текст с $(dropdb)
EOF
)"
```
Заметить single quotes around EOF - disables expansion.

**Передача через stdin / файл**:
```bash
printf '...' | gh issue create --body-file -
```

**`--body-file` вместо inline `--body`**: читает из файла, никаких substitutions.

## Whitelist для trivial

В `block_command_injection.py` в `TRIVIAL_CMDS` set:
```python
TRIVIAL_CMDS = {
    "pwd", "date", "whoami", "hostname", "id", "uname", "echo", "printf",
    "basename", "dirname", "realpath", "readlink",
    "cat", "head", "tail", "which", "command", "type",
    "tr", "cut", "wc", "sort", "uniq", "git",
    "node", "python", "python3",
}
```

Добавлять свои проект-специфичные safe commands только если они:
- Не принимают user input который может быть malicious
- Не могут вызвать side effects
- Не делают network requests

Особенно **не добавлять** в whitelist: curl, wget, ssh, docker, kubectl, terraform, ansible.

## Что hook НЕ покрывает

- Substitution с `$(variable)` где `$variable` содержит malicious command - hook видит только literal substring
- Escape через `eval`, `bash -c`, `sh -c` - классический injection vector
- Python/Node subprocess calls - другой язык, другой hook
- Command injection в SQL (different context, нужен ORM / prepared statements)

Для этих случаев нужна более глубокая защита - code review или static analysis tools (semgrep правила).
