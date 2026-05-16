# Agent Tool Design - risk taxonomy + permission decisions + draft/commit

## Принцип (2026-05-16)

Когда строится **новый** агент через Claude Agent SDK / Managed Agents / собственный harness (Python/TS обёртка над `anthropic.Messages.create` с tool_use, MCP server, custom orchestrator), tool registry должен иметь **формальный design language**:

1. **Risk taxonomy** на каждый tool (классификация на этапе декларации)
2. **Permission decision object** (структурированный ответ runtime'а до выполнения)
3. **Draft/commit naming pattern** для всего что необратимо или внешне-видимо
4. **Structured tool result** с `next_valid_actions` (а не сырой blob)

Это **дополняет** runtime safety hooks из `rules/safety-*` (block_destructive, block_git_destructive и т.д.) - те ловят опасные команды в Bash CLI. Это правило про **design-time** для tools которые мы сами объявляем модели.

Источник: skill `agents-best-practices` от Denis Sergeevitch (MIT, https://github.com/DenisSergeevitch/agents-best-practices) `references/tools-and-permissions.md`. Адаптировано к нашей терминологии.

## 1. Tool Risk Taxonomy

Каждый tool классифицируется одним из 15 классов. Класс задаёт permission policy по умолчанию.

| Risk class | Что входит | Default permission |
|---|---|---|
| `read_only` | get, list, fetch, query (no side effects) | allow |
| `search_only` | search index, vector lookup | allow |
| `compute_only` | parse, transform, calculate в sandbox | allow |
| `draft_only` | generate text/markup без send | allow |
| `write_local` | edit local file/artifact | allow scoped |
| `write_internal` | mutate own DB/state | approval-gated |
| `write_external` | mutate чужую систему через API | approval required |
| `financial` | money movement, billing, refunds | approval + strong auth |
| `communication` | send email/SMS/Slack/Telegram | draft -> approval -> send |
| `identity_access` | rotate keys, grant/revoke perms | approval + strong auth |
| `security_sensitive` | TLS certs, encryption keys | approval + audit |
| `process_execution` | shell, subprocess, eval | sandbox + allowlist |
| `network_open_world` | curl arbitrary URL, browse web | sandbox + egress log |
| `destructive` | delete, drop, truncate, force-overwrite | deny by default |
| `privileged_admin` | sudo, root, IAM admin | manual only |

Обязательно declarable в tool schema:

```yaml
tool: send_customer_email
risk_class: communication
side_effects: external_communication
permission_default: approval_required
```

## 2. Permission Decision Object

Permission engine возвращает **один из 7 типов** перед каждым tool execution:

```python
class PermissionDecision:
    type: Literal[
        "allow",                  # execute now
        "deny",                   # block with reason
        "ask_user",               # surface question to user, pause
        "approval_required",      # require explicit approval token
        "require_stronger_auth",  # MFA / re-auth before proceed
        "run_in_sandbox",         # execute но в isolated env
        "run_as_draft_only",      # execute но не commit (return draft)
    ]
    reason: str            # human-readable объяснение
    policy_rule: str       # ID правила которое сработало
    suggested_remediation: str | None  # что user/agent может сделать
```

Decision **обязательно записывается** в trace (audit log) с tool_name, args_hash, decision.type, policy_rule, timestamp.

## 3. Draft/Commit Naming Pattern

Любое необратимое или внешне-видимое действие **разделяется** на 2 tools:

| Один tool (anti-pattern) | Два tools (pattern) |
|---|---|
| `send_customer_email(case_id, body)` | `draft_customer_email(case_id) -> send_customer_email(draft_id, approval_token)` |
| `apply_database_change(sql)` | `prepare_database_change(intent) -> apply_database_change(plan_id, approval_token)` |
| `place_trade(order)` | `recommend_trade(...) -> place_trade(recommendation_id, approval_token)` |
| `delete_files(paths)` | `propose_file_deletion(paths) -> apply_file_deletion(proposal_id, approval_token)` |

Draft tool обычно `allow`, commit tool обычно `approval_required`.

**Naming convention** (выберите одно по проекту, держитесь его):

- `draft_X` -> `send_X`
- `prepare_X` -> `apply_X`
- `propose_X` -> `commit_X`
- `recommend_X` -> `execute_X`

## 4. Structured Tool Results

Tool **никогда не возвращает** raw blob. Минимум:

```json
{
  "status": "success" | "error" | "approval_required",
  "summary": "Found 3 matching cases.",
  "items": [...],
  "evidence_ref": "artifact://...",
  "next_valid_actions": ["read_case", "draft_response"],
  "limits": { "truncated": false, "total_count": 3 }
}
```

Для error:

```json
{
  "status": "error",
  "type": "permission_denied" | "invalid_arguments" | "timeout" | "rate_limited" | ...,
  "message": "Sending external email requires approval.",
  "next_valid_actions": ["draft_email", "request_approval"]
}
```

`next_valid_actions` критично: модель видит **что делать дальше** без догадок. Снижает retry loops в 2-3 раза по эмпирическим замерам.

**Результат должен быть bounded**:

- `max_result_chars: 8000` (default)
- Если больше -> store externally + return `evidence_ref`
- Никогда не возвращать 10k rows когда нужно 5

## 5. Tool Visibility (5 уровней)

Не показывать все tools всегда. Большая палитра ломает выбор + жжёт кэш + увеличивает риск misuse.

| Level | Когда видим | Примеры |
|---|---|---|
| `base` | always | help, list, search |
| `task` | после classification таска | domain-specific reads |
| `skill` | после skill activation | skill-specific tools |
| `connector` | после auth | MCP/external connector tools |
| `deferred` | через `search_tools(query)` | большой каталог редких tools |
| `sensitive` | hidden until needed AND approved | destructive/admin |

В Claude Code это уже есть на уровне `ToolSearch` (deferred) - для собственных Agent SDK apps надо реализовать аналог.

## Mechanical enforcement

Это design rule, не runtime hook. Применяется **когда пишется новый Agent SDK app или harness**.

Чек-лист перед merge нового tool:

- [ ] `risk_class` declared (одна из 15)
- [ ] Если `risk_class >= write_external` - есть парная draft tool
- [ ] Output schema typed, с `next_valid_actions`
- [ ] `max_result_chars` лимит установлен
- [ ] Permission policy записана в registry config (не в коде tool)
- [ ] Eval test покрывает: happy path + permission denied + invalid args

## Anti-patterns

- `execute_anything(command)` или `call_api(url, method, body)` - broad tools, классическая supply chain
- Tool возвращает `str` или `dict[str, Any]` без schema - модель угадывает структуру
- Send-style tool без draft pair - нет точки approval
- Permission check внутри tool (прямо в `execute()`) - должен быть **снаружи**, в permission engine
- Все tools видимы сразу - context bloat + neighbor misuse
- Result size unbounded - context overflow при большом возврате

## Связь с другими правилами

- `rules/safety-destructive.md` - runtime защита Bash CLI; **этот rule - design-time** для собственных tools
- `rules/no-guessing.md` - `next_valid_actions` снижает гадание модели о следующем шаге
- `principles/01-harness-design.md` - этот rule operationализирует "tool guardrails" слой harness
- `principles/10-agent-security.md` - permission decision object и draft/commit pattern - часть defence-in-depth

## Источники

- Denis Sergeevitch / agents-best-practices `references/tools-and-permissions.md` (MIT, 2026)
- Anthropic - "Writing effective tools for agents" engineering post
- OpenAI tools and function calling guides
