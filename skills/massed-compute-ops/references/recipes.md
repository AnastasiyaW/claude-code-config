# Massed Compute recipes and locations

## Canonical endpoints and local locations

- Documentation: `https://vm-docs.massedcompute.com/docs/category/mcp`
- MCP endpoint: `https://vm.massedcompute.com/api/mcp`
- API-key page: `https://vm.massedcompute.com/settings/api`
- Codex MCP config: `%USERPROFILE%\.codex\config.toml` on Windows or `$HOME/.codex/config.toml` on Unix
- Token source: user environment variable `MC_TOKEN`
- Canonical skill source: `%USERPROFILE%\.claude\claude-code-config\skills\massed-compute-ops`
- Codex installed skill: `%USERPROFILE%\.codex\skills\massed-compute-ops`
- Claude installed skill: `%USERPROFILE%\.claude\skills\massed-compute-ops`
- Claude keyword router: `%USERPROFILE%\.claude\claude-code-config\hooks\keyword-skill-router.py`

## Access bootstrap

The user supplies only:

1. A full-access API token copied unchanged from the API-key page when VM lifecycle operations are wanted. A read-only token is enough for inventory and billing audits.
2. Confirmation that billing recharge amount and threshold are configured.
3. The SSH public key to register, if the desired key is not already on the account. Keep the matching private key local; do not upload or paste it.

Account email, account password, website cookies, VM passwords, and payment-card details are not required.

Codex configuration:

```toml
[mcp_servers.massed-compute]
url = "https://vm.massedcompute.com/api/mcp"
bearer_token_env_var = "MC_TOKEN"
enabled = true
```

On Windows, persist the token for future processes with:

```powershell
[Environment]::SetEnvironmentVariable('MC_TOKEN', '<token>', 'User')
```

Also set `$env:MC_TOKEN` for the current process when immediate testing is needed. Restart Codex after changing the persistent value.

## Safe launch recipe

1. Validate token and scope.
2. Read billing settings and ensure recharge is configured.
3. List SSH keys; create the named public key only when absent.
4. List live GPU inventory and compatible images.
5. Resolve workload requirements: framework, model size, precision, batch/resolution, GPU count, expected duration, region, storage, and budget.
6. Present the selected SKU, image, count, region, hourly/fleet cost, and names.
7. Launch once. If the response is ambiguous, list instances before retrying.
8. Poll by UUID until ready; provide SSH coordinates and write the durable run record.

## Training-run recipe

Before starting training, verify dataset and base model are already on durable storage or have a measured transfer path. Record command/config path, output/checkpoint path, instance UUID, GPU SKU, hourly cost, start time, checkpoint cadence, expected stop condition, and recovery command. During long runs, inspect live process/GPU/log/checkpoint evidence rather than assuming progress.

## Cost-audit recipe

List instances and live inventory pricing. Report each instance's UUID/name/GPU/region/state/age/hourly rate, total hourly and daily burn, long-running or idle-looking instances, recharge settings, and estimated runway. Do not terminate during an audit; route cleanup through the termination recipe.

## Termination recipe

Resolve filters to exact instances. Show UUID, name, GPU, region, state/uptime, hourly cost, and any checkpoint/sync risk. Ask for explicit confirmation naming the targets. Terminate only those UUIDs, then re-list instances and state whether each target is confirmed absent.

## Official MCP tools

Read-only and full: `gpu_inventory_list`, `images_list`, `instances_list`, `instances_get`, `coupon_information`, `coupon_accepted_products`, `account_token_validation`, `account_billing`, `ssh_keys_list`.

Full only: `instances_launch`, `instances_restart`, `instances_terminate`, `ssh_keys_create`, `ssh_keys_delete`.

## Source documentation

- Overview: `https://vm-docs.massedcompute.com/docs/mcp/overview`
- Client setup: `https://vm-docs.massedcompute.com/docs/mcp/setup`
- Tools: `https://vm-docs.massedcompute.com/docs/mcp/tools`
- Vendor skills: `https://vm-docs.massedcompute.com/docs/mcp/skills`
- Troubleshooting: `https://vm-docs.massedcompute.com/docs/mcp/troubleshooting`
