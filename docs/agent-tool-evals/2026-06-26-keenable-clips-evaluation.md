# Keenable and Clips Evaluation - 2026-06-26

## Scope

Evaluate two candidate agent-workflow tools:

- Keenable: search/fetch backend for agents.
- Clips / Agent-Native: agent-readable screen-recording and visual bug-report workflow.

## Keenable Result

Decision: approved for controlled pilot.

Evidence:

- Installed Keenable CLI `0.1.22` on Windows after the normal PowerShell execution policy blocked direct script execution; reran with process-local `-ExecutionPolicy Bypass`.
- Ran fixed search/fetch smoke suite:
  - `agent_native_clips`
  - `keenable_mcp_codex`
  - `cpp_memory_windows`
  - `agent_handoff_hooks`
  - `security_release_signing`
  - `fetch_keenable_skill`
- Local evidence was captured in a timestamped `reports/agent-tool-evals/`
  directory in the private hub; this public note keeps only non-sensitive
  commands and aggregate results.
- All commands returned structured output.
- `keenable fetch https://keenable.ai/SKILL.md` returned clean YAML/Markdown suitable for agent parsing.
- Search results surfaced primary sources for agent-native and Keenable MCP, plus docs for Windows signing and C++ memory topics.

Measured timings:

| Probe | Time |
|---|---:|
| agent_native_clips | 7378 ms |
| keenable_mcp_codex | 381 ms |
| cpp_memory_windows | 398 ms |
| agent_handoff_hooks | 729 ms |
| security_release_signing | 365 ms |
| fetch_keenable_skill | 799 ms |

Known limitation:

- First query was slow, likely cold/network/index path. Keep Keenable as a pilot backend, not the only search tool yet.
- If Keenable MCP is enabled, define a routing rule. The Keenable docs warn that leaving duplicate search/fetch tools active causes inconsistent tool choice.

Adoption:

- Keep CLI installed.
- Use on research-heavy tasks where primary-source discovery matters.
- Do not globally replace existing web search until a 5-query comparison shows consistent quality improvement.

## Clips / Agent-Native Result

Decision: approved for a single real-clip pilot, not full adoption yet.

Evidence:

- Official template markdown is available at `https://agent-native.com/templates/clips.md`.
- Official GitHub README describes Clips as a Loom/Jam-like template for screen recording with transcripts, share links, browser debug capture, timestamped frames, and agent-readable bug-fix context.
- The hosted app exists at `https://clips.agent-native.com/`.

Why not full adoption yet:

- No real local bug clip was recorded and replayed through an agent in this pass.
- Effectiveness depends on whether the shared clip URL/API exposes enough transcript/frame/log metadata for an agent to act without human re-explanation.

Pilot acceptance criteria:

1. Record or import one real bug/UX clip.
2. Give the agent only the clip link/API output.
3. Agent must recover:
   - transcript,
   - timestamped visual evidence,
   - browser/debug logs if present,
   - concrete reproduction steps,
   - actionable fix/report tasks.
4. If the agent can produce a useful issue/fix plan without extra human narration, adopt Clips as optional evidence format for UI/installer/browser bugs.

## Local System Result

The handoff/memory loop and hook discipline were also hardened during this evaluation.

Proof:

```text
python scripts\test_review_handoff_memory_loop.py
5 tests OK

python scripts\test_task_completion_hooks.py
4 tests OK

python scripts/review_handoff_memory_loop.py --root . --strict-legacy --write-report
fail=0 warn=0 pass=true

powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1
Hub agent-docs health check passed
```

The new hook-discipline test proves that the stop phrase guard blocks endings that try to leave reachable work as an optional follow-up.
