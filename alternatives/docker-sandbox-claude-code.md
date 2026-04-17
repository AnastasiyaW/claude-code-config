# Docker Sandbox for Claude Code

## When to use

When you want architectural isolation instead of (or in addition to) PreToolUse hooks. Pattern from practitioners running 5000+ agent-driven PRs with 1-2 incidents: agent runs in docker, prod changes only via CI/CD, tokens without delete rights.

**Use this sandbox when:**
- Working on production systems where a mistake is expensive (DB ops, infra changes)
- Onboarding new agent setups you don't fully trust
- Multiple agents running in parallel (risk of cross-session contamination)
- Experiments that might brick the environment

**Skip this sandbox when:**
- Quick scripts on personal projects where worst-case is `git reset`
- Already running inside a VM or devcontainer
- Cost of rebuild isn't worth vs the inconvenience of non-native tooling

## Tradeoffs vs PreToolUse hooks

| Dimension | Hooks (`rules/safety-*.md`) | Docker sandbox |
|---|---|---|
| Setup cost | 5 minutes (register hooks in settings.json) | 30-60 min (compose file, volumes, image build) |
| Coverage | Pattern-based (regex). False positives/negatives | Filesystem + network isolation. No escape without explicit volume |
| Performance | ~100ms per tool call | Near-native once container is warm |
| Learning curve | Zero | Docker basics + image hygiene |
| Recoverability | Rule only blocks - recovery depends on bypass | Worst case: destroy container, rebuild from image |
| Secret exposure | Hook can miss if secret in unusual location | Container has no access to host secrets unless mounted |

**Practical:** run both layers. Hooks catch bugs that match patterns. Sandbox catches everything else by limiting blast radius.

## Minimal compose file

```yaml
# docker-compose.claude.yml
version: "3.9"

services:
  claude-workspace:
    build:
      context: .
      dockerfile: Dockerfile.claude
    volumes:
      # Project code - editable
      - ./project:/workspace/project
      # Claude Code config - read-only (prevents agent from editing its own settings)
      - ~/.claude:/root/.claude:ro
      # Memory / handoffs - writable, but scoped
      - ./claude-state:/root/.claude-state
    environment:
      # Keep out of production by default - explicit opt-in per session
      - CLAUDE_ALLOW_DESTRUCTIVE=
      - CLAUDE_ALLOW_GIT_DESTRUCTIVE=
    working_dir: /workspace/project
    # No sensitive host paths mounted. No host network by default.
    network_mode: bridge
    # If agent needs internet but no host services:
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"
```

## Minimal Dockerfile

```dockerfile
# Dockerfile.claude
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    build-essential \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code via native installer - not npm.
# Native binary, no transitive npm deps, smaller supply-chain surface.
RUN curl -fsSL https://claude.ai/install.sh | bash

# Node / Python runtimes as needed for project work
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

WORKDIR /workspace

# Default shell = bash (not sh) for proper PreToolUse hook behavior
SHELL ["/bin/bash", "-c"]
```

## Usage pattern

```bash
# Build once
docker compose -f docker-compose.claude.yml build

# Work session - agent lives inside, host is safe
docker compose -f docker-compose.claude.yml run --rm claude-workspace bash
# Inside container:
#   claude  # start Claude Code, it sees only mounted project + scoped state
```

## Hard boundaries

**NOT mounted into container by default:**
- `~/.ssh/` - agent can't use your SSH keys
- `~/.aws/`, `~/.config/gcloud/` - agent can't touch cloud credentials
- `/var/run/docker.sock` - agent can't spawn containers (prevents escape)
- `.env` files at host root - only project's .env is visible
- Host networking - agent sees bridge network, can't touch host LAN

**Writable from container:**
- `./project/` - the actual code you're working on
- `./claude-state/` - memory, handoffs, logs

**Read-only from container:**
- `~/.claude/` - agent can read rules/skills but can't edit them
  (critical: prevents agent from silently disabling its own safety hooks)

## Production ops pattern

Agent in docker sandbox produces PRs. Deploy to prod happens via CI/CD (GitHub Actions), not direct push. GitHub token for agent has **no delete permissions** - even if agent tried force-push, API refuses.

```yaml
# .github/workflows/agent-pr-ci.yml
permissions:
  contents: read          # agent's PR can read code
  pull-requests: write    # agent can comment on PR
  # NOT granted: contents:write, admin, delete
```

This is the architectural Konstantin Dyachenko pattern: 1-2 incidents per 5000+ PRs.

## Breakout scenarios and mitigations

**Scenario 1: agent learns to write a dockerfile that escapes**
Mitigation: bind mounts are the weak point. If agent can write Dockerfile that mounts /, it gets host access. Mount host's docker socket is the kill switch - don't.

**Scenario 2: secret in environment variable inside container**
Mitigation: use Docker secrets or mount `.env` as read-only explicit file, not via env. Never `-e SECRET=...` in compose - it shows in `docker inspect`.

**Scenario 3: agent installs malicious package**
Mitigation: build images from pinned versions, scan with trivy/grype periodically. Rebuild weekly from clean base image. npm/pip supply-chain defense lives in `~/.npmrc` and `uv.toml` inside image.

**Scenario 4: network escape via container DNS**
Mitigation: use `--network none` for sessions that don't need internet. Or explicit allowlist via egress proxy (project-specific).

## When sandbox is overkill

For quick local scripts, experiments, personal projects where worst case is "oh I lost 10 min of work" - hooks alone are enough. Sandbox adds cost (docker desktop running, build time, volume sync issues) that's not justified.

The signal: "if this agent goes rogue, how expensive is the cleanup?" If the answer is <1 hour of your time, hooks are fine. If it's days of reconstruction, recovery of lost data, or loss of production - sandbox.

## Related

- `rules/safety-destructive.md`, `rules/safety-secrets.md`, `rules/safety-git-destructive.md`, `rules/safety-self-harm.md` - pattern-based layer, complementary to sandbox
- `principles/00-supply-chain-defense.md` - `~/.npmrc` min-release-age and uv `exclude-newer` inside docker image builds
