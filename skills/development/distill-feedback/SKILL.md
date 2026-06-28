---
name: distill-feedback
description: Turn captured user-correction signals into durable rules (learn-from-corrections loop). Use when - /distill-feedback, "process feedback queue", "what corrections did I give you", "encode lessons from my corrections", session-feedback-capture queued sessions, "обнови правила по моим поправкам", "разбери очередь обратной связи". Reads ~/.claude/feedback/queue.jsonl, LLM-semantically detects durable corrections, proposes atomic rules, applies human-gated via delta-merge. Do NOT use to act on a single in-session correction (just apply the fix directly) or to hand-edit settings.json behaviors; this only mines the queued feedback backlog into durable rules.
---

# distill-feedback — close the learn-from-corrections loop

The Stop hook `session-feedback-capture.py` queues finished sessions into
`~/.claude/feedback/queue.jsonl`. This skill processes that queue: it finds the user turns
that were **durable corrections** of the agent's work and turns them into rules — so the same
correction never has to be given twice.

**Why LLM-semantic, not keywords:** we independently tested a keyword detector. It scored F1
**0.42** on held-out cases and missed ~60% of real corrections (every keyword-free one, e.g.
"в следующий раз лучше через python"). An LLM applying the rubric below scored F1 **0.97** on the
same set. So detection is semantic. Evidence:
`knowledge/agent-systems/self-learning-agents/effectiveness-test/RESULTS.md` (in the private hub).

**Why human-gated:** ACE (arXiv 2510.04618) and TRACE (arXiv 2606.13174) both warn that a noisy
extractor poisons the rule set. Altering durable rules is also above the auto-act line
(`autonomy-risk-tiers.md`). So this skill **proposes**; the user approves before anything is written.

## Procedure

### 1. Extract the queue (deterministic)
```bash
python ~/.claude/skills/distill-feedback/scripts/extract_feedback_queue.py --limit 8
```
Returns JSON: `{pending, sessions:[{session_id, cwd, ts, user_turns:[...]}]}`. `--limit` bounds
the LLM pass (billing: distillation is opt-in, not every-session). If `pending` is 0, stop — nothing
to do.

### 2. Detect durable corrections (LLM-semantic, prefer a fresh sub-agent)
For independence (Generator-Evaluator), spawn a sub-agent with the **rubric** below and the
extracted `user_turns`. Ask it to return, per genuine correction: `{quote, durable_rule,
applicability_condition, confidence, session_id}`. Pass only the turns — not your own reasoning.

**RUBRIC — a user turn is a DURABLE CORRECTION** if the user pushes back on / redirects the agent's
behavior in a way that implies a STANDING preference or a mistake to avoid in future:
- explicit pushback / redirection ("no, do X instead", "wrong file again")
- reminder of a prior agreement ("we agreed you'd ask first", "мы же договаривались сначала бэкап")
- standing-preference marker ("from now on / always / never / by default / в следующий раз / впредь")
- frustration at a REPEATED mistake ("опять", "again", "you keep")
- polite redirection phrased as a question ("could you not overwrite latest.pth each time?")
- revert with a reason ("верни как было, твоя версия хуже")
- **praise THEN correction — judge the whole turn** ("great it runs, but always pin versions" = YES)

**NOT a durable correction:** new feature/task request · diagnostic question ("why did the build
fail?", "почему-то падает") · factual/info statement even with "should be / by default / never"
("deploy should be done in 5 min", "по умолчанию там 8080") · agreement ("actually that makes
sense, go ahead") · reassurance ("don't worry about the tests") · praise-only · off-topic chatter.

### 3. Dedup + draft atomic rules
For each detected correction: write it as ONE atomic rule with an applicability condition. **Dedup
against existing rules/memory** (`grep` `~/.claude/rules/` and the project memory) — if it is already
a rule, skip or propose an EDIT, not a new ADD. Cluster duplicates across sessions into one rule.

### 4. Propose (human-gate — MANDATORY)
Show the user a compact table: each proposed rule + its applicability condition + source quote +
target file + action (ADD new / EDIT existing / SUPERSEDE old / SPLIT). Ask for approval. Do NOT
write anything yet. `SUPERSEDE`/`DELETE` always need explicit confirmation.

### 5. Apply (delta-merge, never rewrite)
On approval, apply each accepted delta with the ACE discipline from `memory-maintenance.md`:
addressable ADD/EDIT only, dedup, preserve nuance (no full-file rewrite). Put it in the right home
(`file-organization-cohesion.md`): a global rule → `~/.claude/rules/`, a project-specific lesson →
that project's memory/CLAUDE.md. **If the rule is mechanically checkable** (file-name shape,
forbidden command, tool-call form), note that it should graduate to a hook/validator (deterministic
tier beats prose — `learn-from-corrections.md`).

### 6. Mark processed
```bash
python ~/.claude/skills/distill-feedback/scripts/extract_feedback_queue.py --mark-processed <session_id> ...
```
Appends to `processed.jsonl` (append-only; the queue is never rewritten). The SessionStart nudge
count drops accordingly.

## Gotchas
- **Transcript may be gone.** If a queued session's `transcript_path` no longer exists, the extractor
  yields no turns for it — mark it processed and move on (the lesson is lost; nothing to recover).
- **Don't auto-apply.** Even high-confidence corrections go through step 4. A wrong rule is worse
  than a missed one (it fires on every future session).
- **Praise-then-correction is the #1 miss.** "Спасибо, но впредь не трогай прод" IS a correction.
  The rubric handles it; don't let a praise-detector suppress it (that bug killed the keyword version).
- **Billing.** Distillation runs an LLM over user turns. Use `--limit`, run it on-demand (not a hook),
  and prefer a cheaper model for the detection sub-agent (the rubric is not hard reasoning).
- **One-off ≠ durable.** "переделай, я имел в виду src не dist" is a one-off fix, not a standing rule —
  the rubric's confidence + your judgment should drop these; only encode what generalizes.

## Troubleshooting
- *Nudge keeps showing, queue looks empty* → entries whose transcript vanished are still pending;
  run the extractor, mark the dead ones processed.
- *Extractor prints `pending: N` but `sessions: []`* → all N transcripts are missing/unreadable;
  mark them processed.
- *Want to pause capture entirely* → `touch ~/.claude/.skip-feedback-capture` (or
  `CLAUDE_SKIP_FEEDBACK_CAPTURE=1`); the Stop hook then no-ops.

## Related
- `rules/learn-from-corrections.md` — the protocol + the evidence behind LLM-semantic + human-gate
- `rules/memory-maintenance.md` — the delta-merge (ACE) discipline step 5 reuses
- `hooks/session-feedback-capture.py` (Stop, capture) · `hooks/feedback-pending-show.py` (SessionStart, nudge)
