#!/usr/bin/env python3
"""PreToolUse(AskUserQuestion): block deferral/menu questions on reversible work.

Root cause this closes (2026-06-16): the behavioral canon "on reversible work
decide yourself and proceed; ask only for irreversible / genuine-fork decisions"
(rules/autonomy-risk-tiers.md + finish-the-task.md) was enforced only by
stop-phrase-guard, which scans the final assistant TEXT at the Stop event. But
AskUserQuestion is a TOOL CALL — its menu text lives in tool_input, never in the
scanned assistant text — so "ask via the tool" was a total enforcement blind spot
(a "куда продолжаем?" / "what next?" menu sailed straight through).

This hook scans the AskUserQuestion payload itself (question + header + option
labels) for deferral / menu / scope-degree phrasing and blocks it. A SPECIFIC
genuine fork ("Postgres or MySQL?", "delete prod table X — confirm?") does not
match these patterns and passes. Bypass for a real irreversible/fork question:
CLAUDE_ALLOW_ASK=1 in the session.

Exit conventions per safety_common: block = {"decision":"block"} on stdout.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from safety_common import allow, any_match, block, bypass, log, read_event  # noqa: E402

# Deferral / menu / scope-degree phrasing. Regex, case-insensitive.
# These signal "what should I do next / which of these / how far" — decisions the
# agent should make itself on reversible work, not punt to the user.
DEFERRAL_PATTERNS = [
    # RU — "what next / which of these / what do we do"
    r"что (дальше|делать дальше|делаем(?: дальше)?|теперь делаем|по плану дальше)",
    r"что (выбираешь|предпочитаешь|приоритетн|важнее)",
    r"что из (этого|них|трёх|двух|перечисл|предложен|вариант)",
    r"куда (дальше|продолжа|двига|ид[её]м|приложить)",
    r"\bпродолжаем\b",
    r"какой из (вариантов|подходов|трёх|двух|них)",
    r"какой (вариант|подход) (выбрать|предпочт|брать)",
    # RU — scope-degree ("how aggressive / how deep / how far") = agent's call
    r"насколько (агрессивн|глубок|далеко|сильно|подробн|широк)",
    r"в каком (объёме|масштабе)",
    # EN — what next / which of these / how far
    r"what (would you like|do you want|next|should i (do|tackle|work on|focus|start))",
    r"which (option|one|of these|of the|direction|do you (want|prefer))",
    r"how (aggressive|far|deep|much) (should|do you|to go)",
    r"want me to (keep going|continue|proceed|do)",
    r"should i (continue|proceed|keep going|also)",
]

# Generic menu headers (AskUserQuestion `header` field) that signal a deferral menu
# rather than a specific decision. Compared lowercased, exact-ish.
DEFERRAL_HEADERS = {
    "next", "next step", "scope", "direction", "priority", "objem", "объём",
    "дальше", "выбор", "приоритет", "направление", "что дальше",
}


def main() -> None:
    event = read_event()
    if event.get("tool_name") != "AskUserQuestion":
        allow()

    ti = event.get("tool_input", {})
    questions = ti.get("questions", []) or []

    texts: list[str] = []
    headers: list[str] = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        texts.append(str(q.get("question", "")))
        h = str(q.get("header", "")).strip().lower()
        headers.append(h)
        texts.append(h)
        for o in q.get("options", []) or []:
            if isinstance(o, dict):
                texts.append(str(o.get("label", "")))
    blob = "\n".join(t for t in texts if t)
    if not blob.strip():
        allow()

    hit = any_match(blob, DEFERRAL_PATTERNS)
    header_hit = next((h for h in headers if h in DEFERRAL_HEADERS), None)
    if not hit and not header_hit:
        allow()  # specific genuine-fork question — let it through

    signal = hit or f"header:{header_hit}"

    if bypass("ask", blob):
        log("WARN", "ask_question_guard", "bypass", signal, blob[:300])
        allow()

    log("BLOCK", "ask_question_guard", "deny", signal, blob[:300])
    block(
        "Deferral/menu question detected (/" + signal + "/). "
        "Канон autonomy-risk-tiers + finish-the-task: на ОБРАТИМОЙ работе НЕ "
        "спрашиваем — выбираем лучший вариант сами и делаем, отчёт ПОСЛЕ. "
        "Вопрос-меню «что дальше / куда продолжаем / насколько / which of these» "
        "= откладывание.\n"
        "Если решение реально НЕОБРАТИМОЕ или это genuine fork, который должен "
        "решить пользователь (DROP/DELETE, прод-миграция, выбор архитектуры с "
        "разными последствиями) — переформулируй как КОНКРЕТНЫЙ вопрос (не «что "
        "дальше», а «удалить таблицу X? / Postgres или MySQL?») ИЛИ выставь "
        "CLAUDE_ALLOW_ASK=1 в сессии и переспроси."
    )


if __name__ == "__main__":
    main()
