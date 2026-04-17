# Safety: Test Muting Prevention

## Правило (advice layer)

Не заглушать падающие тесты. Failing test = сигнал. Заглушённый failing test = скрытый баг который попадёт в прод.

Запрещённые паттерны (добавление к существующим тестам):
- Python pytest: `@pytest.mark.skip`, `@pytest.mark.xfail`, `pytest.skip(...)`
- Python unittest: `@unittest.skip`, `@unittest.expectedFailure`
- JS (jest/mocha/vitest): `it.skip()`, `test.skip()`, `describe.skip()`, `xit(...)`, `xdescribe(...)`, `.todo(...)`
- JS `.only()`: коварно, suite гоняет только помеченные - остальные silently skip
- Java JUnit: `@Ignore`, `@Disabled`
- Go: `t.Skip()`, `t.Skipf()`
- Rust: `#[ignore]`

## Hook (mechanical enforcement)

`~/.claude/scripts/block_test_muting.py` срабатывает PreToolUse на Edit/Write/NotebookEdit. Блокирует если:
- файл в tests/, __tests__/, spec/, *_test.py, *.test.js etc
- новая версия содержит mute pattern которого не было в старой

Обход: `CLAUDE_ALLOW_TEST_MUTING=1`.

## Когда легитимно muted

- **Flaky тест с known issue**: `@pytest.mark.skip(reason="flaky - tracked in #1234")`. Reason + link to issue = accountable.
- **Тест устаревшей фичи**: лучше **удалить** тест целиком чем mute. Deprecated feature → deprecated test.
- **Conditional skip**: `@pytest.mark.skipif(sys.platform == "win32", reason="...")` - это не "муте бага", это правильная условная пропуска.
- **Temporary disable во время рефакторинга**: OK, но с TODO и deadline.

## Что hook НЕ покрывает

- Комментирование всего тестового файла (`# def test_...`) - hook видит old/new strings, может пропустить если комментарий добавлен через Write полностью новым файлом без паттерна mute
- Изменение config чтобы тест не запускался (`.gitignore tests/`, изменение test matcher в pytest.ini)
- Удаление теста целиком (это может быть OK - deprecated feature - но может скрывать баг)
- Mute на уровне CI config (`.github/workflows/test.yml` - если убрать step - hook не увидит)

## Real-world провалы

Из практики:
- "Снести падающие тесты чтобы скрыть баги прода" - буквальная цитата одного разработчика
- "Добавить багованные файлы с тестами без включения в схему" - тест "есть", но никогда не запускается
- `.only()` забытый после debug сессии → pipeline зелёный, но реально тестируется 1 функция из сотни

## Tuning

Если проект использует `@skip` как первый класс citizen (например skip based on OS, skip for integration vs unit):
```bash
export CLAUDE_ALLOW_TEST_MUTING=1
```
Но стоит в CLAUDE.md проекта добавить review requirement: любой коммит с `skip` должен иметь issue link в reason.

Альтернатива: написать кастомный project-level hook который allows `@pytest.mark.skipif(reason="...#issue")` и блокирует raw `@pytest.mark.skip`.
