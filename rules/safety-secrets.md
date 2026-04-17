# Safety: Secret Files

## Правило (advice layer)

Не читать и не печатать содержимое secret-файлов без явной пользовательской просьбы:
- `.env`, `.env.local`, `.env.production`, `.envrc`
- Ключи: `*.key`, `*.pem`, `id_rsa`, `id_ed25519`, `id_ecdsa`, `id_dsa`
- Директории: `~/.secrets/`, `~/.ssh/`, `~/.aws/`
- `credentials.json`, `secrets.yaml`

Даже если пользователь сказал "проверь что в .env" - это НЕ даёт право печатать значения в output. Прочитать - можно (Read tool). Вывести секреты в чат - нельзя.

## Hook (mechanical enforcement)

`hooks/secret-leak-guard.py` блокирует:
- Read/Edit/Write tools на файлы с secret-паттернами
- Bash команды `cat/less/head/tail/grep/bat/xxd/source` на secret пути
- Grep tool с path указывающим на secret директорию

Обход: `CLAUDE_ALLOW_SECRETS=1` + явное согласие пользователя. После чтения **всё равно** не печатать содержимое в output.

## Real-world утечки которые этот hook предотвращает

Из наблюдений в AI-coding сообществе:

- **ENV на фронт**: агент переставил server-side environment variables в client bundle. Там были ключи ChatGPT / Claude / OpenRouter. Через несколько часов ключи забрали и слили в third-party сервисы
- **"Не читай env"**: пользователь пишет "я туда пароль сейчас положу, не читай". Агент соглашается. Пользователь в следующем сообщении пишет "положил пароль". Агент немедленно вызывает `Read .env`, в ответе подтверждает что пароль "правильно положен" - полностью процитировав. Rule-level instruction игнорирован в том же turn где его дали
- **Env удалён без бэкапа**: при попытке "почистить проект" агент удалил `.env` файл безвозвратно. Пересборка всех ключей по всем сервисам заново - дни работы
- **Swagger наружу**: API задеплоен со всеми токенами и admin endpoints видимыми в публичной Swagger UI. Auth сделали, но docs забыли закрыть
- **env в чат**: агент "глянул env и предложил его убить, так как все ключи попали в чат". То есть и прочитал, и напечатал, и хотел удалить

## Почему "просто сказать не читай" недостаточно

Первый кейс выше - прямое доказательство: rule-level instruction "не читай env" игнорируется в том же сообщении где его дали. Это может быть из-за context pressure, интерпретации задачи шире, или просто привычки агента "при любом непонятном файле - прочитать".

Hook - это первый barrier **до** того как Read tool запустится. Не требует от модели помнить правило.

## Что hook НЕ покрывает

- Secret-значения в **коде** (hardcoded API keys в .py/.js) - hook их не увидит, это уже утечка
- Secret в environment переменных процесса (`env`, `printenv`, `/proc/*/environ`)
- Secret в command line arguments других процессов (`ps auxww`)
- Secrets в git history (если коммит уже сделан)

Для этих случаев нужны:
- Pre-commit hooks (gitleaks, trufflehog, detect-secrets)
- Regular audit через те же tools на существующий repo
- Secrets management (Vault, SOPS, AWS Secrets Manager) вместо plain files

## Tuning

Регулярки в начале `secret-leak-guard.py`:
- `SECRET_PATH_REGEX` - расширения файлов (.env, .key, .pem и т.д.)
- `SECRET_DIR_REGEX` - директории (.ssh, .aws, .secrets)
- `BASH_READ_VERBS` - команды которые печатают содержимое

Если ваш проект использует custom secret storage (например `.vault/`) - добавь в SECRET_DIR_REGEX.
