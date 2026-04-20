# 22 - Visual Context Pattern: When to Show, Not Tell

**Source:** Distilled from obra/superpowers visual-companion skill (2026-04) + our own experience with UI-heavy decisions.

## Overview

Coding agents default to text because that is the channel they were trained on. But there is a class of decisions where text is the wrong medium: UI mockups, spatial relationships, visual tradeoffs between options, architecture diagrams with non-trivial topology. For these, a picture is not a nice-to-have — it is the actual requirements artifact.

The **Visual Context Pattern** is the workflow for letting an agent present visual options to a human, collect structured feedback, and iterate — without requiring special tooling, proprietary UIs, or cloud services.

The core idea is a **local HTTP server + HTML fragments + file-based event queue**. No MCP, no browser extension, no Figma plugin. It works the same on every operating system and every agent runtime.

---

## Decision Rule: When to Go Visual

Ask one question:

> *Would the user understand this better by seeing it than reading it?*

| Use visual | Use terminal |
|---|---|
| UI mockups, component layouts | Conceptual choices with text labels |
| Spatial relationships, diagrams | Requirements clarification |
| Side-by-side visual comparison | Text-based tradeoffs |
| Before/after design states | Decisions that fit in a paragraph |
| Mobile vs desktop layouts | Yes/no questions |
| Color palette selection | Architecture decisions that are really about data |

Rule of thumb: if you would naturally want to open Figma/Sketch/Miro to explain the choice, it is visual. If you would naturally write it in a PR comment, it is terminal.

---

## The Architecture

```
┌──────────────────┐   writes HTML fragment   ┌──────────────────┐
│                  │  ─────────────────────►  │   screen_dir/    │
│   Agent (LLM)    │                          │   *.html         │
│                  │  ◄─────────────────────  │                  │
│                  │   reads events JSON      └──────────────────┘
└──────────────────┘                                    │
        ▲                                               │ served by
        │ user clicks                                   │ local HTTP
        │ → events JSON                                 ▼
        │                                      ┌──────────────────┐
        │                                      │                  │
        └──────────────────────────────────────│  Browser (user)  │
                                               │                  │
                                               └──────────────────┘
                                                       │
                                                       ▼
                                               ┌──────────────────┐
                                               │  state_dir/      │
                                               │  events          │  (JSON lines)
                                               └──────────────────┘
```

Three directories and a long-running server:

- **`screen_dir/`** — agent writes HTML fragments here. Each visual turn gets a unique filename (never overwrite).
- **`state_dir/`** — local JSON state. Events, server info, current selection.
- **`state_dir/events`** — append-only JSON lines. Each user click produces one line.

The agent's loop becomes: write fragment → tell user the URL → read events on next turn → iterate.

---

## The Interactive Loop

1. **Verify server health** by reading `$STATE_DIR/server-info`. If absent or stale, start the server (`scripts/start-server.sh --project-dir /path/to/project`).
2. **Write a new HTML fragment** to `screen_dir`. Never reuse filenames — append timestamp or turn counter. The server template wraps it with CSS theme + selection infrastructure.
3. **Tell the user what is on screen** and share the URL. One sentence: "I put three layout options on the screen; click the one you prefer, or explain what is off."
4. **On the next turn, read `$STATE_DIR/events`.** Every click since your last read appears as JSON lines. Parse the latest (or all of them — click patterns reveal exploration).
5. **Iterate or advance.** If feedback demands changes, write a new fragment. If the decision is stable, push a waiting screen to free the browser and continue in text.
6. **Push a waiting screen** when transitioning back to terminal-only discussion — otherwise the last visual frame sits on screen confusing the user.

---

## Content Structure

The server provides a frame template with CSS and JS. The agent writes **fragments only** — no `<html>`, `<head>`, or `<script>` tags. This means:

- Agent cannot accidentally inject XSS or break the page
- Theme changes propagate to every fragment without rewriting
- Server can upgrade markup infrastructure without breaking existing agent code

Available structural classes (baseline, extend per project):

| Class | Purpose |
|---|---|
| `.options` container + `.option` children | Click to select. Add `data-multiselect` for multi-select. |
| `.cards` | Visual design grid |
| `.mockup` | Preview container |
| `.split` | Side-by-side comparison |
| `.mock-nav`, `.mock-sidebar`, `.mock-button`, `.mock-input` | UI skeleton primitives |
| `.subtitle`, `.section`, `.label` | Typography |

User clicks record to `events` as JSON: `{"type": "click", "target": "option-2", "text": "Dense layout", "timestamp": "..."}`.

---

## Why This Beats the Alternatives

### vs. ASCII diagrams in the terminal

ASCII works for topology (graphs, trees) but fails catastrophically on spatial relationships, color, proportion, typography. Trying to express "card padding feels too tight" in ASCII is absurd.

### vs. Asking the user to imagine

"Imagine a card with 16px padding and a 1px border" wastes working memory on reconstruction. The user's answer drifts from the actual proposal because they are half-thinking, half-picturing.

### vs. Generating a full HTML file per turn

A full HTML file means the agent owns the entire page. One mistake breaks the frame. One theme change requires rewriting every past file. Fragments let the server own the infrastructure and the agent own the content.

### vs. External tools (Figma, Miro, Excalidraw)

External tools require auth, specific integration, and usually some SaaS. They also lock you to that vendor. The fragment server is 200 lines of Python — **you own the tooling** and can adapt it per project.

### vs. Cloud-based AI design canvases (Claude Design, etc.)

Cloud canvases are powerful but opaque. You cannot audit the prompts, you cannot run offline, you cannot share the same workflow across agent runtimes (Claude Code, Codex, Cursor, Gemini CLI). The fragment server is portable.

---

## Measured Impact

From practitioners of the original superpowers/visual-companion skill:

- **Style-related retries dropped from 4 per feature to 0.** The user sees the intended design once and either approves or redirects — no second-guessing after the fact.
- **Agent token usage dropped ~14%** on UI tasks, despite adding visual overhead. Reason: iteration loops shorten because visual feedback is precise.
- **User satisfaction with design decisions rose qualitatively.** Less "that is not quite what I meant" after the fact.

These numbers are from a 14-skill harness (not just visual-companion). The visual-context pattern is one of the largest contributors because design decisions were the worst offenders for "looks right in text, wrong in practice."

---

## When NOT to Use This Pattern

- **For architecture decisions that are really about data flow.** A DAG in Mermaid is fine. A UI-mockup for a pipeline is overkill.
- **For one-off yes/no questions.** The server setup cost outweighs the benefit.
- **For decisions that require code review.** Code review wants `diff`, not a mockup.
- **When the user is not at a computer.** If the user is reviewing on mobile or via a terminal-only environment, fall back to text.
- **When the decision is time-pressured.** Setting up the server, opening a browser, clicking — this takes ~30 seconds each time. Fine for deliberate choices, wrong for hot-path debugging.

---

## Integration with Other Principles

| Principle | Relationship |
|---|---|
| **01 Harness Design** | Visual context is one capability of a harness. Add it to Generator output, not just Evaluator feedback. |
| **02 Proof Loop** | Visual fragments can be durable artifacts — save `screen_dir/` into the evidence folder for a design decision. |
| **04 Deterministic Orchestration** | The server is a shell-bypass for "render a visual thing" — agent does not do HTML layout in its reasoning. |
| **07 Codified Context** | `.claude/visual/` directory stores past screens as a design decision log. |
| **08 Skills Best Practices** | Package the server + fragment templates as a reusable skill, not a one-off script. |
| **23 Anti-pattern as Config** | Visual content is where AI slop is most visible. Pair this pattern with anti-attractor enforcement. |

---

## Gotchas

- **Never reuse fragment filenames.** The server treats `screen_dir` as append-only. Reusing filenames creates race conditions between the server watching for new files and the browser caching the old URL.
- **Windows + `run_in_background`.** On Windows, Claude Code needs `run_in_background: true` when launching the server via Bash, otherwise it blocks the main session. Codex auto-detects.
- **Server binds to localhost only.** Do not expose it on `0.0.0.0` without thinking — HTML fragments contain decision state that should not leak across machines.
- **CSS class names are a contract.** If the frame template renames a class, every past fragment breaks. Pin the frame to a version; bump it deliberately.
- **Events file can grow unbounded.** On long sessions, rotate or prune. Agents only need recent events.

---

## Troubleshooting

### Agent writes fragments but browser shows blank page
- **Symptom:** HTML fragment exists in `screen_dir/`, URL returns frame but content area is empty.
- **Cause:** Fragment uses a CSS class the frame does not style, or the fragment contains `<html>` tags that get stripped.
- **Solution:** Verify fragment is body-only markup. Open browser devtools, check the inner frame for content.

### Events file exists but has no recent clicks
- **Symptom:** User clicked, agent reads `events` and sees nothing new.
- **Cause:** Browser and server disagree on the `state_dir` path (typical when agent runs in a container but browser is on host).
- **Solution:** Print `$STATE_DIR` from server-info and compare to what the browser sees in the page source.

### Frame CSS broken in some fragments
- **Symptom:** A specific fragment renders correctly alone but looks wrong inside the frame.
- **Cause:** Fragment style selectors override frame selectors (e.g., fragment-local `.option {}`).
- **Solution:** Namespace fragment CSS or use scoped selectors. Prefer adding `data-` attributes over new class names.

---

## Minimum Viable Implementation

You do not need to fork superpowers to use this pattern. A minimal viable server is a `http.server` + one directory + one JSON file:

```python
# server.py (~40 lines)
import http.server, os, json, time
from pathlib import Path

SCREEN_DIR = Path(os.environ["SCREEN_DIR"])
STATE_DIR = Path(os.environ["STATE_DIR"])
FRAME_TEMPLATE = Path(os.environ["FRAME_TEMPLATE"]).read_text()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            latest = sorted(SCREEN_DIR.glob("*.html"))[-1]
            html = FRAME_TEMPLATE.replace("{{CONTENT}}", latest.read_text())
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/click":
            # JS posts here
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            with (STATE_DIR / "events").open("a") as f:
                f.write(json.dumps({"ts": time.time(), "body": body}) + "\n")
            self.send_response(204); self.end_headers()
```

Plus a `frame.html` with the CSS theme and a JS snippet that posts clicks to `/click`. Total cost: ~100 lines of code for a reusable visual-decision infrastructure.

---

## Open Questions

- **Multi-user collaboration.** Can two reviewers click on different machines? The fragment server is single-user by design. Shared workspace requires a different architecture (WebSocket broadcast).
- **Mobile friendliness.** Most fragment-based workflows assume desktop browser. On mobile, layout and click affordances change — the frame template needs responsive treatment.
- **Long sessions and session loss.** If the user closes the browser tab, the agent has no way to re-send state. A re-open button on the frame could solve this but requires state_dir persistence.

---

## Sources

- [obra/superpowers: visual-companion](https://github.com/obra/superpowers/blob/main/skills/brainstorming/visual-companion.md)
- [superpowers release announcement](https://blog.fsck.com/2025/10/09/superpowers/)
- [Superpowers 5 update (visual brainstorming)](https://blog.fsck.com/2026/03/09/superpowers-5/)
