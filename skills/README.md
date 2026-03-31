# Skills Catalog

Custom skills for Claude Code. Each skill is a self-contained SKILL.md file with YAML frontmatter that Claude Code loads as a slash command.

## Installation

Copy any skill folder to `~/.claude/skills/`:

```bash
# Single skill
cp -r skills/development/deep-review ~/.claude/skills/

# All skills
cp -r skills/*/* ~/.claude/skills/
```

Or use the install script from the repo root:

```bash
./install.sh
```

After copying, the skill becomes available as `/skill-name` in Claude Code.

---

## Development

| Skill | Command | Description |
|---|---|---|
| [deep-review](development/deep-review/) | `/deep-review` | Parallel competency-based code review. Launches 8 independent reviewers (security, performance, architecture, database, concurrency, error-handling, frontend, testing), each with a focused checklist. Synthesizes findings into FIX/DEFER/ACCEPT triage. |

## AI/ML

| Skill | Command | Description |
|---|---|---|
| [diffusion-engineering](ai-ml/diffusion-engineering/) | `/diffusion-engineering` | Practical diffusion model engineering: architectures (UNet/DiT/Flow/Flux), schedulers, LoRA training, memory optimization (AMP/ZeRO/FSDP), text encoder fusion, Diffusers. |
| [flux2-lora-training](ai-ml/flux2-lora-training/) | `/flux2-lora-training` | LoRA training for FLUX.2 Klein 9B and Qwen Image Edit 2511. Resolution expansion, VAE fine-tuning, multi-reference training, dataset preparation. |
| [flux2-klein-prompting](ai-ml/flux2-klein-prompting/) | `/flux2-klein-prompting` | Prompt engineering for FLUX.2 Klein: semantic structure, composition, style direction, T2I/I2I templates, multi-reference workflows. |
| [vlm-segmentation](ai-ml/vlm-segmentation/) | `/vlm-segmentation` | VLM + segmentation engineering: SAM2/3, Florence-2, YOLO-World, Grounding DINO, GPU deployment (MIG/MPS), transfer learning, open-vocab detection. |
| [forensic-prompt-compiler](ai-ml/forensic-prompt-compiler/) | `/forensic-prompt-compiler` | Reverse-engineer images into high-fidelity generation prompts. Observation-only methodology for any image model (Midjourney, FLUX, SD, Ideogram). |

## Frontend

| Skill | Command | Description |
|---|---|---|
| [frontend-design](frontend/frontend-design/) | `/frontend-design` | Production-grade web interfaces: React/Vue/Svelte, Tailwind CSS, responsive design, visual styles (glassmorphism, neomorphism, material), animations, accessibility (WCAG/ARIA). |

## Architecture

| Skill | Command | Description |
|---|---|---|
| [harness-design](architecture/harness-design/) | `/harness-design` | Multi-agent harness architecture: Generator-Evaluator pattern, Sprint Contracts, context management, quality criteria calibration. For long-running app development. |

## iOS

| Skill | Command | Description |
|---|---|---|
| [ios-development](ios/ios-development/) | `/ios-development` | iOS app development: Swift/SwiftUI/UIKit, architecture (MVVM/TCA/VIPER), CoreData/SwiftData, Metal/GPU, App Store submission. |

## Writing

| Skill | Command | Description |
|---|---|---|
| [humanize-english](writing/humanize-english/) | `/humanize-english` | Make AI-generated text sound natural: burstiness, perplexity, banned words, tone control. Passes AI detection. |

---

## Recommended External Skills

These are not included in this repo but are excellent complements:

| Tool | Install | What it does |
|---|---|---|
| [gstack](https://github.com/nichochar/gstack) | `npm i -g @nichochar/gstack` | 20+ dev workflow skills: /review, /qa, /ship, /investigate, /design-review, /retro, and more |
| [hookify](https://github.com/anthropics/claude-code-plugins) | Claude Code plugin marketplace | Create hooks to prevent unwanted behaviors |
| [semgrep](https://github.com/anthropics/claude-code-plugins) | Claude Code plugin marketplace | Static analysis integration |
