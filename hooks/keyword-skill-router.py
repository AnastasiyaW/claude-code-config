#!/usr/bin/env python3
"""UserPromptSubmit: detect natural-language keywords and suggest matching skills.

Inspired by oh-my-claudecode's keyword detection hook. Instead of requiring
users to know skill names, this hook scans the user's message for trigger
phrases and outputs a suggestion that the agent can act on.

Non-blocking: outputs a suggestion, does not force skill invocation.
The agent decides whether the suggestion is relevant.

Setup in settings.json:
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python hooks/keyword-skill-router.py"
      }]
    }]
  }
}
"""
from __future__ import annotations

import json
import re
import sys

# ─── Keyword → Skill mapping ───
# Each entry: pattern (regex, case-insensitive) → skill name + description
# Patterns should be specific enough to avoid false positives on normal conversation
ROUTES = [
    # Retouch native / low-level memory
    {
        "patterns": [
            r"\b(retouch-app|retouch plugin|photoshop plugin|uxp hybrid|uxp.*native|native addon|neural plugin|нейро\w*.*плагин|плагин.*нейро\w*)\b",
            r"\b(плагин|plugin)\b.*\b(ретуш|retouch|photoshop|uxp)\b.*\b(c\+\+|native|натив|memory|памят|abi|onnx|directml|coreml|metal|gpu|buffer|tensor)\b",
            r"\b(ретуш|retouch)\b.*\b(плагин|plugin|нейро\w*|onnx|directml|coreml|metal)\b.*\b(memory|памят|c\+\+|native|натив|buffer|tensor)\b",
        ],
        "skill": "native-cpp-memory",
        "description": "REQUIRED for retouch/native/neural plugin memory, ABI, tensor, GPU, and C++ ownership work",
        "refs": [
            "references/retouch-native.md",
            "references/low-level-retouch-memory.md",
            "references/windows-memory-abi.md",
            "references/macos-memory-abi.md",
            "references/advanced-cpp.md",
        ],
        "required": True,
    },
    # Planning & Architecture
    {
        "patterns": [
            r"\b(спланируй|составь план|plan this|make a plan|design the approach)\b",
            r"\b(архитектур|architect)\b.*\b(реши|спроектируй|design|plan)\b",
        ],
        "skill": "plan",
        "description": "Structured planning with acceptance criteria",
    },
    # Code Review
    {
        "patterns": [
            r"\b(сделай ревью|code review|review this|проверь код|review the pr)\b",
            r"\b(pr review|pull request review)\b",
        ],
        "skill": "deep-review",
        "description": "Parallel competency-based code review (security, perf, arch)",
    },
    # Security
    {
        "patterns": [
            r"\b(проверь безопасность|security review|security audit|check security)\b",
            r"\b(найди уязвимост|find vulnerabilit|pentest)\b",
        ],
        "skill": "security-review",
        "description": "Security vulnerability analysis",
    },
    # Handoff
    {
        "patterns": [
            r"\b(подготовь handoff|prepare handoff|save context|write handoff)\b",
            r"\b(сохрани контекст|перенеси контекст|закрываем сессию)\b",
            r"\b(подбей.*беседу.*для.*чат|сделай передачу)\b",
        ],
        "skill": "handoff",
        "description": "Write structured handoff for session transition",
    },
    # Research
    {
        "patterns": [
            r"\b(deep research|глубокий ресерч|исследуй|investigate this)\b",
            r"\b(разбери.*подробно|dig into|deep dive)\b",
        ],
        "skill": "investigate",
        "description": "Systematic investigation with root cause analysis",
    },
    # Debugging
    {
        "patterns": [
            r"\b(не работает|doesn.t work|broken|сломал|debug this)\b.*\b(помоги|fix|почини|разберись)\b",
            r"\b(почему.*ошибк|why.*error|что не так|what.s wrong)\b",
        ],
        "skill": "investigate",
        "description": "Root cause investigation (Iron Law: no fixes without root cause)",
    },
    # Simplify / Clean
    {
        "patterns": [
            r"\b(упрости|simplify|clean up|почисти код|refactor)\b",
        ],
        "skill": "simplify",
        "description": "Review changed code for reuse, quality, and efficiency",
    },
    # Init new project
    {
        "patterns": [
            r"\b(настрой проект|init|initialize|set up claude)\b.*\b(claude|project)\b",
            r"\b(создай claude\.md|create claude\.md)\b",
        ],
        "skill": "init",
        "description": "Initialize CLAUDE.md with codebase documentation",
    },
]


def detect_keywords(user_message: str) -> list[dict]:
    """Return matching skills for the user's message."""
    matches = []
    for route in ROUTES:
        for pattern in route["patterns"]:
            if re.search(pattern, user_message, re.IGNORECASE):
                matches.append({
                    "skill": route["skill"],
                    "description": route["description"],
                    "refs": route.get("refs", []),
                    "required": route.get("required", False),
                })
                break  # one match per route is enough
    return matches


def main() -> int:
    # Read the hook event from stdin
    try:
        raw_input = sys.stdin.read().lstrip("\ufeff")
        event = json.loads(raw_input)
    except (json.JSONDecodeError, EOFError):
        return 0

    # Extract user message
    # UserPromptSubmit event structure may vary - try common paths
    message = ""
    if isinstance(event, dict):
        message = event.get("message", "")
        if not message and "content" in event:
            message = event["content"]
        if not message and "prompt" in event:
            message = event["prompt"]
        if not message and "user_prompt" in event:
            message = event["user_prompt"]

    if not message or len(message) < 5:
        return 0

    matches = detect_keywords(message)
    if not matches:
        return 0

    # Output suggestions (agent sees this in context)
    suggestions = []
    for m in matches:
        prefix = "  REQUIRED" if m.get("required") else "  /"
        if m.get("required"):
            suggestions.append(f"{prefix}: Use skill {m['skill']} - {m['description']}")
        else:
            suggestions.append(f"{prefix}{m['skill']} - {m['description']}")
        if m.get("refs"):
            suggestions.append(f"    refs: {', '.join(m['refs'])}")

    print(f"[skill-router] Detected {len(matches)} matching skill(s):")
    for s in suggestions:
        print(s)
    print("[skill-router] Consider invoking the suggested skill if relevant.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
