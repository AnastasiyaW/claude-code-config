# DESIGN.md Pattern: Brand Config as Runtime Context

**Released:** April 2026, following the launch of Claude Design (Anthropic Labs).

## Summary

DESIGN.md is a convention: a markdown file at the root of a project that describes the visual design system in terms the agent can use at generation time. It plays the same role for visual output that CLAUDE.md plays for code style — a runtime config that the agent reads on every relevant task, not human documentation.

The convention gained traction because Claude Design and the surrounding tool ecosystem (getdesign.md, bluzir/claude-code-design) converged on it as the lowest-friction way to carry brand identity across sessions.

---

## What DESIGN.md Contains

A working DESIGN.md answers six questions. Each should resolve to concrete tokens the agent can act on, not prose.

1. **Typography** — brand face, display face, mono face. Scale (H1 → caption). Line-heights. Weights used.
2. **Color tokens** — primary, secondary, accents. Neutral scale (tinted, never pure gray). Semantic colors (success / warning / error / info). Dark-mode pairing.
3. **Spacing scale** — the rhythmic unit (4px / 8px / Golden / custom). Standard gaps, standard margins, standard paddings.
4. **Radius and elevation** — corner radii for cards / buttons / inputs. Shadow tokens if used. Border tokens.
5. **Component patterns** — preferred patterns for buttons, forms, cards, navigation. Anti-patterns (see [Principle 23](../principles/23-anti-pattern-as-config.md)).
6. **Motion** — preferred easings, standard durations, reduced-motion fallback.

Optional but high-value:
- **Voice and tone** for copy (confidence level, formality, humor band)
- **Photography style** (if brand uses imagery)
- **Exclusions** — explicit "we do not use X, Y, Z"

---

## Comparison With Related Conventions

| File | Scope | Read when |
|---|---|---|
| **CLAUDE.md** | Code style, project architecture, agent behavior | Every session in project root |
| **AGENTS.md** | Cross-agent contract, universal instructions | Every session, every supported agent |
| **DESIGN.md** | Visual system: type / color / spacing / motion | Visual output tasks (HTML, decks, slides, illustrations) |
| **.cursorrules / .windsurfrules** | Agent runtime config (tool-specific) | Agent bootstrap |
| **package.json** | Dependencies, build scripts | Build tools |

DESIGN.md and CLAUDE.md are orthogonal — a project can have both, with CLAUDE.md referencing DESIGN.md for "any UI task, read DESIGN.md first."

---

## Three Approaches to the Same Problem

### 1. Claude Design (Anthropic Labs, 2026-04-17)

**URL:** https://www.anthropic.com/news/claude-design-anthropic-labs
**Model:** Opus 4.7
**Access:** Pro / Max / Team / Enterprise
**General availability:** 2026-05-31

Canvas-based chat+edit product on claude.ai. Generates prototypes, slides, one-pagers, design systems, animated videos. Exports to Canva / PDF / PPTX / standalone HTML. Packages results as a "handoff bundle" that Claude Code accepts as one instruction.

**DESIGN.md fits:** Claude Design reads a project's codebase and existing design tokens to build a design system. If `DESIGN.md` exists it is honored as the source of truth; the canvas starts pre-configured. New projects write a DESIGN.md back into the repo for consistency.

**Strengths:** Canvas editing (direct manipulation), multi-user internal share links, Opus 4.7 design quality, first-party Canva export, tight handoff to Claude Code.

**Weaknesses:** Cloud-only (no offline). Closed — cannot inspect the prompts. Locked to claude.ai runtime. Group mode single-session at launch.

### 2. getdesign.md (VoltAgent, community)

**URL:** https://getdesign.md/
**Repository:** awesome-design-md (community maintained)
**Access:** Open, no auth

Curated collection of 69 DESIGN.md files extracted from well-known brands: Linear, Stripe, Ferrari, Wired, Figma, Notion, Vercel, Airbnb, Spotify, Apple, Uber, Framer, Sentry, Raycast, Shopify, Tesla, Mastercard, IBM, Lamborghini, and more.

**How to use:** Download the DESIGN.md for a brand you are emulating → drop into your project root → any coding agent that reads project files picks it up automatically.

**Strengths:** Instant brand fidelity without setting up a system. Free. Works with every agent runtime.

**Weaknesses:** Static snapshots (brands evolve). No direct preview — you trust the file describes the brand accurately. Risk of over-literal mimicry if used without adaptation.

**Not affiliated with `hesreallyhim/awesome-claude-code`.** The latter is a general Claude Code meta-list (skills / plugins / hooks), not a design collection. Common confusion in community posts.

### 3. bluzir/claude-code-design (CLI reproduction of Claude Design)

**URL:** https://github.com/bluzir/claude-code-design
**License:** MIT

A research-quality reproduction of Claude Design's output types — HTML decks, interactive prototypes, design systems, animated videos — through Claude Code skills instead of a canvas web app.

**Architecture (20 skills + 4 atomic commands):**
- **Primary outputs:** `/make-deck`, `/interactive-prototype`, `/wireframe`, `/animated-video`, `/create-design-system`.
- **Ingestion:** `/ingest-github`, `/ingest-screenshot`, `/ingest-figma`, `/use-design-system`.
- **Iteration:** `/make-tweakable`, `/apply-tweaks`, `/inspect`, `/verify-artifact`.
- **Organization:** `/done` (auto-registers artifact into `assets.html` with inferred group).
- **Export:** `/export-pptx`, `/export-pdf`, `/export-standalone`, `/handoff`.

**Dependencies:** Chrome DevTools MCP (preview + screenshot + snapshot) + monolith (standalone HTML bundler) + pptxgenjs + puppeteer.

**DESIGN.md fits:** `/create-design-system` reads `theme.*`, `tokens.*`, `tailwind.config.*`, `_variables.*` from codebase and can persist the result to `~/.claude/design-systems/<name>/` — a cross-project brand registry.

**Strengths:** Portable (works on every runtime that supports Claude Code skills). Open source. Auditable prompts. Works offline except for MCP calls. Cross-project registry means one brand, many projects.

**Weaknesses:** Terminal-first (no canvas workspace). Chrome DevTools MCP round-trip is ~6-10s, so live preview is slower than Claude Design's sub-second loop. Single-user by design. macOS-first (uses `open`, `brew`); Linux/Windows need minor adaptation.

**Parity claim:** deck navigation, device frames (iPhone 15 Pro / Pixel 8 / macOS / browser), design canvas, Stage/Sprite timeline with Remotion-compatible API, ingestion, tweakable panel, PPTX/PDF/standalone export, visual verification with vision. Not reproducible in terminal: sub-second live preview, real-time multi-user, share URL, canvas sketch pad.

---

## Integration With Our Principles

### Principle 07 (Codified Context)

DESIGN.md is runtime config, not documentation. Same rule applies as CLAUDE.md: keep it tight, make it scannable, update it when brand evolves. A DESIGN.md that drifts from the actual design is worse than no DESIGN.md — it gives the agent false confidence.

### Principle 08 (Skills Best Practices)

Pair DESIGN.md with a project skill that calls it out: `skills/design-apply/SKILL.md` whose description includes "Use when generating any UI, slide, or visual asset" and whose body says "Before generating, read DESIGN.md from project root."

### Principle 23 (Anti-pattern as Config)

DESIGN.md plus an anti-patterns.md is the complete positive + negative pair. The design system says "these are the choices"; the anti-patterns say "these are the things to avoid even when tempted."

### Principle 11 (Documentation Integrity)

DESIGN.md references specific token values. If those token values drift (refactor, library migration), the DESIGN.md becomes stale. Add to the drift validator's scope: values declared in DESIGN.md must exist in the codebase.

---

## When to Adopt Which Option

Choose by primary constraint:

| Your situation | Choose |
|---|---|
| Client-work shop, need polish + collaboration | Claude Design (canvas + Opus 4.7) |
| Solo dev, want offline + auditable + portable | bluzir/claude-code-design |
| Want to emulate a known brand quickly | getdesign.md → drop in + adapt |
| Already have a design system in tokens | Any of the three — all can ingest |
| Need to package for handoff to Claude Code dev | Claude Design (native bundle) or bluzir `/handoff` |
| Want cross-project brand consistency | bluzir cross-project registry |

Not mutually exclusive. A common pattern: use getdesign.md for a starting DESIGN.md, refine it by hand, then generate actual UI with Claude Design on cloud or bluzir in terminal.

---

## Anti-Patterns Specific to DESIGN.md

- **DESIGN.md that is copy-pasted from a library homepage.** The tokens must describe your actual brand, not the framework's defaults.
- **DESIGN.md without a "do not use" section.** Positive tokens alone let the agent slip into generic defaults. Include the explicit exclusions ([see Principle 23](../principles/23-anti-pattern-as-config.md)).
- **DESIGN.md that lives next to a conflicting CSS.** The source of truth must be singular — either DESIGN.md drives tokens.css, or tokens.css is authoritative and DESIGN.md is a mirror. Never both authoritative.
- **DESIGN.md longer than ~300 lines.** Past this length the agent skims. Move detail to `design/` subdir and keep DESIGN.md as an index.
- **DESIGN.md with no examples.** Pure token declarations are hard for an agent to translate into layout choices. Include one example page snippet.

---

## Minimum Viable DESIGN.md

For a new project, this is the 60-line starter:

```markdown
# DESIGN.md

## Typography
- Brand: Söhne (Regular, Semibold, Buch)
- Mono: Söhne Mono
- Scale: 12 / 14 / 16 / 20 / 24 / 32 / 48 (modular scale 1.25)
- Line-height: 1.5 body, 1.1 display

## Colors
- Primary: #0A6E38 (dark forest green)
- Accent: #F5A623 (warm amber)
- Neutrals: tinted towards primary (do not use pure #000 or #888)
- Semantic: success #2D8F4E, warning #F5A623, error #C13030

## Spacing
- Unit: 8px
- Common gaps: 8 / 16 / 24 / 32 / 48 / 64

## Radii
- Buttons: 8px
- Cards: 12px
- Modals: 16px

## Motion
- Easing: cubic-bezier(0.4, 0, 0.2, 1)
- Duration: 150ms ui, 300ms panel, 600ms page
- Reduced motion: disable all non-essential transitions

## Components
- Buttons: solid primary, ghost secondary, link tertiary. Never tertiary as CTA.
- Cards: single level, no nested cards. Padding 24px. Border 1px neutral-20.
- Forms: labels above inputs, error messages below, 8px gap.

## Voice
- Confident, not smug. Specific, not vague. Direct, not terse.
- No "Unlock the power of", "Game-changing", "Seamless".

## Do not use
- Inter, Roboto, Arial, Helvetica, system-ui as brand face
- Pure black (#000) or pure gray (#888 etc.)
- Purple gradients, dark glows
- Nested cards (cards inside cards)
- Bounce or elastic easing
```

Scale from here as the brand solidifies.

---

## Sources

- [Anthropic: Introducing Claude Design](https://www.anthropic.com/news/claude-design-anthropic-labs)
- [TechCrunch: Claude Design launch coverage](https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/)
- [VentureBeat: Claude Design vs Figma](https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma)
- [getdesign.md (69 brand files)](https://getdesign.md/)
- [bluzir/claude-code-design (CLI reproduction)](https://github.com/bluzir/claude-code-design)
- [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [monolith (Rust standalone HTML bundler)](https://github.com/Y2Z/monolith)
- [Remotion (motion API inspiration)](https://www.remotion.dev)
