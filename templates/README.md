# Starter Templates

Drop-in configuration files for common project types. Each template is a starting point - customize for your project.

## Available Templates

| Template | Target | Size |
|---|---|---|
| [CLAUDE-web-app.md](CLAUDE-web-app.md) | Web applications (React, Vue, Next.js, etc.) | ~80 lines |
| [CLAUDE-ml-project.md](CLAUDE-ml-project.md) | ML/AI projects (training, inference, data pipelines) | ~80 lines |
| [CLAUDE-library.md](CLAUDE-library.md) | Libraries and packages (npm, PyPI, crates.io) | ~70 lines |
| [REVIEW.md](REVIEW.md) | Code review guidelines (any project type) | ~60 lines |
| [chronicle.md](chronicle.md) | Project chronicle for long-running projects | ~30 lines |
| [memory-project.md](memory-project.md) | Memory file for tracking a project | ~25 lines |
| [memory-reference.md](memory-reference.md) | Memory file for reference material | ~20 lines |
| [proof-plan.md](proof-plan.md) | Verification plan with acceptance criteria | ~30 lines |

## How to Use

1. Copy the relevant template to your project root
2. Rename to `CLAUDE.md` (or `REVIEW.md` for review template)
3. Fill in project-specific values (marked with `{{placeholder}}`)
4. Remove sections that don't apply
5. Add project-specific rules

## Design Principles

- **Under 150 lines** - fits in a single KV-cache prefix for efficiency
- **Commands before prose** - `npm test`, `cargo build` before explanations
- **Code over descriptions** - style shown by example, not described in words
- **No linting rules** - use deterministic tools (eslint, ruff) instead
- **No general programming advice** - only project-specific, non-obvious rules
