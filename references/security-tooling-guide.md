# Security Tooling for Claude Code

Ready-to-use security tools for Claude Code. Install guide and usage patterns.

## 1. Anthropic /security-review (built-in command)

**Source:** github.com/anthropics/claude-code-security-review

**Install:**
```bash
mkdir -p .claude/commands
curl -sL -o .claude/commands/security-review.md \
  https://raw.githubusercontent.com/anthropics/claude-code-security-review/main/.claude/commands/security-review.md
```

**Use:** `/security-review` in any Claude Code session. Analyzes pending changes on current branch via git diff. Focuses on HIGH/MEDIUM confidence, exploitable vulnerabilities only.

**Also available as GitHub Action:**
```yaml
- uses: anthropics/claude-code-security-review@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 2. Trail of Bits Skills (38 security plugins)

**Source:** github.com/trailofbits/skills (2400+ stars)

**Install (clone for reference):**
```bash
git clone --depth 1 https://github.com/trailofbits/skills.git .claude/trailofbits-skills
```

**Key security skills:**

| Skill | What it does |
|---|---|
| `static-analysis` | Run static analysis tools, interpret results |
| `variant-analysis` | Find variants of known vulnerabilities |
| `entry-point-analyzer` | Map attack surface entry points |
| `fp-check` | Check if a security finding is a false positive |
| `differential-review` | Security-focused diff review |
| `audit-context-building` | Build context for security audits |
| `constant-time-analysis` | Check for timing side-channel vulnerabilities |
| `zeroize-audit` | Verify secrets are properly zeroed in memory |
| `insecure-defaults` | Find insecure default configurations |
| `sharp-edges` | Identify API misuse patterns |
| `supply-chain-risk-auditor` | Audit dependency supply chain risks |
| `building-secure-contracts` | Smart contract security review |
| `semgrep-rule-creator` | Create custom Semgrep rules for findings |
| `semgrep-rule-variant-creator` | Generate variant rules from existing Semgrep rules |
| `yara-authoring` | Write YARA rules for malware/pattern detection |
| `burpsuite-project-parser` | Parse Burp Suite project files |

**Usage:** Read skill's SKILL.md, follow its instructions in Claude Code session.

---

## 3. sast-skills (14 vulnerability modules)

**Source:** github.com/utkusen/sast-skills

**Install:**
```bash
git clone https://github.com/utkusen/sast-skills.git
# Copy your project code into sast-skills/sast-files/
# Open sast-skills/ as workspace in Claude Code
```

**What it does:** CLAUDE.md orchestrates 14 parallel vulnerability detection modules with two-phase verification. Outputs structured reports to `sast/` folder.

**Modules:** SQL injection, XSS, RCE, SSRF, GraphQL injection, XXE, template injection, JWT flaws, auth bypass, path traversal, IDOR, unsafe file upload, business logic flaws.

**Note:** Workspace-as-tool pattern - you point Claude Code at sast-skills workspace, not install it into your project.

---

## 4. Our tools (plan-swarm-review + vulnerability KB)

**Already installed in this config:**

| Tool | Location | What |
|---|---|---|
| `/plan-swarm-review` (code mode) | `.claude/skills/plan-swarm-review/` | Multi-agent security review with 5 diverse perspectives |
| Vulnerability KB (agent index) | `references/vulnerability-kb.md` in plan-swarm-review | CWE Top 10 detection heuristics |
| Vulnerability KB (full entries) | `knowledge-vault/docs/security/cwe/` | 10 Vul-RAG format articles |
| `/security-review` | `.claude/commands/security-review.md` | Anthropic's built-in security diff review |

---

## Recommended pipeline

### Quick check (1 min)
```
/security-review
```

### Standard audit (5-10 min)
```
1. /security-review                    # quick scan
2. /plan-swarm-review (code mode)      # multi-agent with 3-5 perspectives
```

### Deep audit (30-60 min)
```
1. semgrep --config auto .             # SAST baseline (if installed)
2. /security-review                    # Anthropic quick scan
3. /plan-swarm-review (code mode)      # multi-agent diverse review
4. Trail of Bits: entry-point-analyzer # map attack surface
5. Trail of Bits: variant-analysis     # find variants of found issues
6. Trail of Bits: fp-check             # verify findings are real
```

### Multi-session audit (with mclaude, 1-2 hrs)
See `mclaude/docs/security-audit-recipe.md` for the full 4-5 agent coordinated workflow.
