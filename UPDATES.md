# Updates

Changelog for claude-code-skills. Newest first.

---

## 2026-03-31

### Added: Supply Chain Defense (Principle 09)

Package age gating as defense against supply chain attacks. Two config lines that block packages published less than 7 days ago:

```ini
# ~/.npmrc
min-release-age=7
```

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

Most malicious packages are caught within 1-3 days. The 7-day delay eliminates the attack window with near-zero friction to your workflow. See [principles/09-supply-chain-defense.md](principles/09-supply-chain-defense.md) for full details including per-manager configs, CI considerations, and defense-in-depth layers.

### Fixed: 6 skills were ZIP archives, not readable on GitHub

`diffusion-engineering`, `vlm-segmentation`, `flux2-klein-prompting`, `forensic-prompt-compiler`, `ios-development`, `frontend-design` - all now properly extracted with SKILL.md + references/ as readable markdown.

### Updated: Memento references replaced

The `mderk/memento` repo appears to have been removed from GitHub. All references updated to point to active alternatives: [task-orchestrator](https://github.com/jpicklyk/task-orchestrator), [inngest/agent-kit](https://github.com/inngest/agent-kit). The deterministic orchestration principles remain valid and well-documented.

### Freshness check: all 10 concepts reviewed

| Concept | Status |
|---------|--------|
| Generator-Evaluator | Current - now a standard primitive |
| Proof Loop | Current - watch formal verification + LLM space |
| Autoresearch | Very current - 21K stars, ecosystem explosion |
| HyperAgents | Current - Meta released code |
| HACRL | Current - conceptual pattern is actionable |
| Structured Reasoning | Current - 78%->88% accuracy validated |
| Codified Context | Current - 1M window adjusts urgency, not principle |
| Memento | Repo gone - principles live in alternatives |
| Context Engineering | Current - update for 1M context realities |
| Multi-Agent Decomposition | Current - trend toward adaptive routing |

---

## 2026-03-30

### Initial release

8 architectural principles, 4 alternative comparison docs, 10 skills, CLAUDE.md template. Covers: harness design, proof loops, autoresearch, deterministic orchestration, structured reasoning, multi-agent decomposition, codified context, skills best practices.
