# 09 - Supply Chain Defense: Protect Against Malicious Package Updates

## Overview

Supply chain attacks on open-source packages are increasing in frequency. The attack pattern is simple: compromise a maintainer's account, push a malicious update to a popular package, profit from the window before detection. Most poisoned packages get caught within days - but if you install them in that window, the damage is done.

The defense is equally simple: **never install packages published less than 7 days ago.** This single rule eliminates the vast majority of supply chain attacks with almost zero cost.

---

## Package Manager Configs

### npm / Node.js

```ini
# ~/.npmrc
min-release-age=7
```

This tells npm to refuse any package version published less than 7 days ago. If a legitimate package has a brand-new release, you wait a week. If it was a supply chain attack, it's been caught and yanked by then.

### uv / Python

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```

Same principle for Python's uv package manager. Packages newer than 7 days are excluded from resolution.

### pip / Python (alternative)

No native equivalent - use uv instead. For pip-only environments, pin exact versions in `requirements.txt` and review diffs on updates manually.

### cargo / Rust

No native `min-release-age` flag yet. Use `cargo-audit` + `cargo-deny` for known vulnerability detection. Pin versions in `Cargo.lock`.

### Go modules

Go's module proxy (proxy.golang.org) caches modules immutably - once fetched, the content can't change. This provides integrity but not freshness gating. Use `go mod verify` and review `go.sum` diffs.

---

## When to Apply

**Always.** Set these configs globally on every development machine and CI runner. The one-week delay is almost never a problem in practice - you rarely need a package published hours ago.

**Exception:** If you need a critical security patch released today, temporarily override:
```bash
# npm: install with explicit flag
npm install package@version --min-release-age=0

# uv: override for one install
uv pip install package==version --exclude-newer "0 days"
```

---

## Why 7 Days

- Most malicious packages are detected within 24-72 hours
- 7 days provides comfortable margin
- Shorter (e.g. 1 day) still catches most attacks but leaves less buffer
- Longer (e.g. 30 days) creates friction with legitimate updates

---

## Defense in Depth

Package age gating is one layer. Combine with:

1. **Lock files** - Always commit `package-lock.json`, `uv.lock`, `Cargo.lock`. Review diffs.
2. **Pinned versions** - Use exact versions, not ranges (`1.2.3` not `^1.2.3`).
3. **Audit tools** - `npm audit`, `cargo audit`, `pip-audit`. Run in CI.
4. **Minimal dependencies** - Every dependency is attack surface. Fewer = safer.
5. **Scope verification** - Check package scope/author before installing. Typosquatting is real.

---

## Gotchas

- **CI caches may bypass age gating** - If your CI caches `node_modules`, the config only applies on cache miss. Ensure clean installs periodically.
- **Monorepo lockfile drift** - In monorepos, one dev's `npm install` without the config can pull fresh packages. Enforce the config at repo level (`.npmrc` in repo root).
- **Transitive dependencies** - The config applies to transitive deps too (good), but you might not notice when a deep dependency is being held back (check `npm outdated`).
- **Private registries** - If you use a private npm/PyPI registry that mirrors public, ensure the mirror also respects age gating, or the freshness check happens client-side.

## See Also

- [npm min-release-age docs](https://docs.npmjs.com/cli/using-npm/config#min-release-age)
- [uv configuration reference](https://docs.astral.sh/uv/reference/settings/)
