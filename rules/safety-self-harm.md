# Safety: Self-Harm Prevention

## Правило (advice layer)

Команды которые могут отрезать агента от хоста или убить его runtime - требуют подтверждения:

**SSH lockout:**
- Edit `/etc/ssh/sshd_config` - может закрыть доступ навсегда
- `systemctl restart sshd` без backup session - если config сломан, больше не зайти
- Изменения `authorized_keys`
- Standalone rule: **никогда не перезапускать sshd если единственная сессия это текущая**

**Process harakiri (Claude Code runtime = node/bun процесс):**
- `killall node|bun|python|claude`
- `pkill -f claude` или общий `pkill node`
- Kill всего пользовательского userspace

**Network self-block:**
- `iptables -A INPUT -j DROP` без `--sport` exception
- `ufw default deny incoming/outgoing`
- `ufw deny all`

**Host reboot:**
- `reboot`, `shutdown now`, `halt`, `poweroff` - ломает handoff state если не было чекпоинта

## Hook (mechanical enforcement)

`hooks/self-harm-guard.py`. Обход: `CLAUDE_ALLOW_SELF_HARM=1` + обязательно наличие альтернативного канала на хост (второй SSH, консоль, VM console).

## Real-world провалы

- **"Закрыть изнутри себе единственный SSH порт"**: агент работал на VPS, редактировал firewall, случайно закрыл порт через который сам подключён. Вход только через rescue console hosting'а
- **Харакири через killall**: агент запущен как bun/node процесс. Пользователь попросил "почистить зависшие процессы". Агент выполнил `killall bun` - убил себя
- **sshd restart без резерва**: пользователь устанавливал новый агент на VPS, последним шагом убрал пароль root. Вспомнил что SSH ключ не добавил. Reboot VPS → больше не войти. Если порт SSH нестандартный - hosting rescue не всегда знает что делать
- **fail2ban банит себя**: несколько SSH подключений подряд для "check+fix+verify" - fail2ban видит как brute force, банит IP на 30 минут
- **Антидос банит на своём же сервере**: бот на проде, настроили rate limit 5 req/IP per hour. Начали проверять с compute машины - заблокировались сами

## Ключевой признак самозапирания

Формула: **"если эта команда сломает, у меня есть способ зайти?"**

- "да, есть второй SSH / VM console / кто-то рядом с сервером" → ОК
- "нет, только этот канал" → НЕ выполнять

Особенно коварно когда SSH порт нестандартный (не 22). Стандартный - hosting providers обычно имеют rescue консоль и знают что делать. Нестандартный - долгое восстановление.

## Почему self-harm hook отдельный от destructive

Destructive = ущерб данным/пользователю. Self-harm = ущерб способности агента продолжать помогать пользователю. Это разные категории risk:
- destructive блокируется строго, редкие bypass
- self-harm блокируется строго, bypass требует явного "у меня есть backup channel"

## Что hook НЕ покрывает

- Fork bomb или ulimit exhaustion (частично в destructive)
- SSH lockout через edit `/etc/hosts.deny`
- systemd mask через конфиг файлы (не через команду)
- Firewall lockout через NetworkManager / systemd-networkd конфиги
- Power off через BMC/IPMI

## Tuning

Паттерны в `BASH_PATTERNS` списке в `self-harm-guard.py`. Если твоя роль требует работу с sshd_config (sysadmin, DevOps) - запускай с `CLAUDE_ALLOW_SELF_HARM=1` в нужной сессии. Но стоит иметь отдельный admin-session режим, не default everyday configuration.
