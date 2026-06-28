#!/usr/bin/env python3
"""Stop hook: queue a finished session for feedback-distillation (learn-from-corrections).

Implements the *capture* half of the learn-from-corrections loop (rules/learn-from-corrections.md):
the agent should learn a lesson every time the user corrects its solution, but capture decays
when it is manual. This hook makes capture automatic and cheap.

Design is evidence-driven. We independently tested a keyword *detector* for corrections and it
failed (held-out F1 0.42, missed ~60% of real corrections — see the learn-from-corrections study).
So this hook does NO keyword judgment. It only decides, deterministically, whether a session had
enough real back-and-forth to be worth an LLM distill pass later, and if so appends a pointer to a
queue. The semantic "is this a durable correction" judgment happens in the deferred, human-gated
distill step (an LLM, which clears F1 0.97 on the same test) — never here, never auto-writing rules.

NON-BLOCKING: always exits 0 with no stdout. It must never trap the user at session end.

Opt out: env CLAUDE_SKIP_FEEDBACK_CAPTURE=1, or touch ~/.claude/.skip-feedback-capture.

Register in ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/session-feedback-capture.py",
        "statusMessage": "Queueing session for feedback-distill..."
      }]
    }]
  }
}
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import datetime as _dt
from pathlib import Path

# A session is worth distilling only if the user actually reacted to the agent's work.
# >= 2 genuine human turns => a back-and-forth where a correction could have occurred.
# This is a high-recall *session-level* gate (cheap, deterministic); the LLM step does precision.
MIN_USER_TURNS = 2

FEEDBACK_DIR = Path.home() / ".claude" / "feedback"
QUEUE_PATH = FEEDBACK_DIR / "queue.jsonl"
SKIP_MARKER = Path.home() / ".claude" / ".skip-feedback-capture"


def _disabled() -> bool:
    val = os.environ.get("CLAUDE_SKIP_FEEDBACK_CAPTURE", "").strip().lower()
    if val in {"1", "true", "yes", "on"}:
        return True
    return SKIP_MARKER.exists()


def count_user_turns(transcript_path: str | None) -> int:
    """Count genuine human turns in a JSONL transcript.

    Skips tool_result echoes (which are role=user) and empty messages. Fail-open:
    returns 0 if the transcript is missing/unparseable (=> session not queued).
    """
    if not transcript_path:
        return 0
    p = Path(transcript_path)
    if not p.exists():
        return 0
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0
    n = 0
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (obj.get("type") or obj.get("message", {}).get("type")) == "summary":
            continue
        role = obj.get("role") or obj.get("message", {}).get("role")
        if role != "user":
            continue
        content = obj.get("content")
        if content is None:
            content = obj.get("message", {}).get("content")
        # Skip tool_result-only user messages (not a human turn).
        if isinstance(content, list):
            if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                continue
            text = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            text = content if isinstance(content, str) else ""
        if text.strip():
            n += 1
    return n


def already_queued(session_id: str) -> bool:
    if not session_id or not QUEUE_PATH.exists():
        return False
    try:
        for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("session_id") == session_id:
                return True
    except OSError:
        return False
    return False


def enqueue(record: dict) -> None:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    with QUEUE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    if _disabled():
        return 0
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        event = {}

    transcript_path = (
        event.get("transcript_path")
        or event.get("transcriptPath")
        or event.get("transcript")
        or os.environ.get("CLAUDE_CODE_TRANSCRIPT_PATH")
    )
    session_id = event.get("session_id") or event.get("sessionId") or ""
    cwd = event.get("cwd") or str(Path.cwd())

    if already_queued(session_id):
        return 0

    n_user_turns = count_user_turns(transcript_path)
    if n_user_turns < MIN_USER_TURNS:
        return 0  # not enough back-and-forth to be worth a distill pass

    enqueue(
        {
            "ts": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "session_id": session_id,
            "cwd": cwd,
            "transcript_path": str(transcript_path) if transcript_path else "",
            "n_user_turns": n_user_turns,
            "status": "pending",
        }
    )
    return 0


def _self_test() -> int:
    """Synthesize a transcript, run the parser + enqueue against a temp HOME, assert it queues."""
    import io

    # 1) user-turn counting ignores tool_result + empty, counts real turns.
    tmp = Path(tempfile.mkdtemp())
    tx = tmp / "transcript.jsonl"
    tx.write_text(
        "\n".join(
            [
                json.dumps({"type": "summary", "summary": "x"}),
                json.dumps({"type": "user", "message": {"role": "user", "content": "сделай датасет"}}),
                json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]}}),
                json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "out"}]}}),
                json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "нет, всегда оригиналы"}]}}),
            ]
        ),
        encoding="utf-8",
    )
    assert count_user_turns(str(tx)) == 2, "should count 2 human turns (not tool_result/summary)"
    assert count_user_turns(str(tmp / "missing.jsonl")) == 0, "missing transcript => 0 (fail-open)"

    # 2) enqueue + dedup against a temp queue.
    global FEEDBACK_DIR, QUEUE_PATH
    FEEDBACK_DIR = tmp / "feedback"
    QUEUE_PATH = FEEDBACK_DIR / "queue.jsonl"
    assert not already_queued("sess-1")
    enqueue({"session_id": "sess-1", "status": "pending"})
    assert already_queued("sess-1"), "dedup must see the queued session"

    # 3) end-to-end main() with a stubbed Stop event.
    event = {"transcript_path": str(tx), "session_id": "sess-2", "cwd": str(tmp)}
    sys.stdin = io.StringIO(json.dumps(event))
    main()
    assert already_queued("sess-2"), "main() must queue a 2-turn session"
    print("self-test OK")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    sys.exit(main())
