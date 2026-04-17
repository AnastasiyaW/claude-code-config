# Safety: API Key Leak Detection in Output

## Правило (advice layer)

Не печатать содержимое API keys / credentials в tool output. Это:
- Попадает в Claude Code context → может быть compressed в compacted state → могут утечь в logs / telemetry
- Видно человеку-читателю → shoulder surfing / screenshots
- Остаётся в terminal history / tmux buffer / editor undo history

## Hook (detective control - не preventive)

`~/.claude/scripts/detect_api_key_leak.py` работает PostToolUse. Срабатывает на любой tool с output:
- Bash stdout/stderr
- Read file content
- Grep matches

Смотрит output на well-known API key patterns:

| Pattern | Pattern regex |
|---|---|
| Anthropic | `sk-ant-[A-Za-z0-9\-_]{32,}` |
| OpenAI | `sk-(?:proj-)?[A-Za-z0-9]{32,}` |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| GitHub fine-grained | `github_pat_[A-Za-z0-9_]{80,}` |
| AWS access | `(AKIA\|ASIA)[0-9A-Z]{16}` |
| AWS secret | `aws_secret_access_key` + `[A-Za-z0-9/+=]{40}` |
| Stripe live | `(sk\|rk\|pk)_live_[0-9a-zA-Z]{24,}` |
| Stripe test | `(sk\|rk\|pk)_test_[0-9a-zA-Z]{24,}` |
| Slack | `xox[baprs]-[A-Za-z0-9\-]{10,}` |
| Google API | `AIza[0-9A-Za-z_\-]{35}` |
| Private key block | `-----BEGIN * PRIVATE KEY-----` |
| JWT | `eyJ*.eyJ*.*` (three base64url segments) |
| Generic bearer | `Bearer [40+ chars]` |

## Почему detective а не preventive

PostToolUse срабатывает после выполнения - tool уже вернул output. Блокировать retroactively нельзя: значения в output, output в context, context уже содержит ключ.

**Hook эмитит громкое warning в stderr** с:
- Redacted snippet (first 8 chars + last 4 чтобы идентифицировать какой ключ)
- Tool которое выдало output
- Action items: rotate key, audit git history, check logs

Это даёт user возможность немедленно отреагировать (rotate) даже если prevention не сработала.

## Связь с block_secrets

- `block_secrets.py` - preventive layer (PreToolUse). Не даёт читать файлы с секретами
- `detect_api_key_leak.py` - detective layer (PostToolUse). Ловит секреты которые попали в output любым способом (включая способы которые block_secrets пропустил: hardcoded values in code, environment variables, ps output, etc)

Работают вместе. Первый предотвращает 80% сценариев, второй ловит остальные 20% и хотя бы уведомляет.

## Real-world трагедия которая мотивирует detective layer

Из практики AI-кодинга: агенту попросили "скопировать .env в .env.backup". Агент сделал `cp .env .env.backup && cat .env.backup`. `cp` не триггерит block_secrets (не read verb), `.env.backup` - уже не совпадает с паттерном .env. Значения утекли в output. Без detective layer - незамеченная утечка.

## Что hook НЕ покрывает

- Секреты в base64 или другом encoding - поиск по плоскому regex не catch
- Keys которые короче min length (16 chars) - regex специально требует длину, чтобы уменьшить false positives
- Custom / corporate token formats не в PATTERNS list. Добавлять project-specific patterns если известны

## False positive tuning

Regex могут fire на test data, примеры в документации, fake keys в README. Если это частое - hook всё равно правильно alerts ("проверь что это fake"), просто шумно.

Для code review workflow - добавить `detect-secrets` или `gitleaks` в pre-commit hooks, они имеют более sophisticated heuristics (entropy analysis etc).

## Rotation workflow после alert

Если hook сработал:

1. **Немедленно rotate ключ** в соответствующем сервисе (AWS console, GitHub settings, Anthropic console)
2. **Audit git history** - was ли ключ закомичен?
   ```bash
   git log -p --all -S 'sk-ant-...' | head
   ```
3. **Audit Claude context logs** если есть - ключ в context теперь
4. **Consider session compromised** - closing без handoff, rotate + start fresh
5. **Fix the leak source** - убрать hardcoded value, перенести в env/secret manager
