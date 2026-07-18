---
name: massed-compute-ops
description: Operate Massed Compute GPU virtual machines through its MCP server. Use when the user mentions Massed Compute, massedcompute, MassedCompute, asks what GPU is available, wants to choose or launch training/inference VMs, inspect running instances, configure SSH access, audit hourly spend or billing runway, restart a VM, or terminate rented compute safely.
---

# Massed Compute operations

Use the Massed Compute MCP tools as the live source of truth for inventory, pricing, account state, and instances. Read [references/recipes.md](references/recipes.md) before the first account operation in a session.

## Operating rules

1. Validate the token before account work. If authentication is missing, request only `MC_TOKEN`; never request the account password.
2. Use live inventory and image compatibility data. Do not recommend a SKU or quote a price from memory.
3. Before a launch, check token scope, billing settings, SSH keys, current capacity, price, compatible images, requested region, instance count, and naming.
4. Treat launch and restart as cost-affecting reversible operations. State the chosen SKU, region, quantity, hourly cost, image, and name, then execute when within the user's request.
5. Treat termination and SSH-key deletion as destructive. Show exact targets and costs, obtain explicit unambiguous user confirmation, call the tool, then re-list state to verify the target is gone.
6. Never expose or persist VM passwords in chat, skill files, Git, or memory. MCP redacts them; the user can read them in the Massed Compute site if needed.
7. After launch, poll instance state until usable, then provide the exact SSH target and record the instance UUID/name/GPU/region in the relevant project handoff or run journal.
8. For long training jobs, preserve resumability: confirm durable storage/checkpoints, record shutdown criteria, and audit burn rate before leaving the job unattended.

## Workflow router

- Inventory or GPU choice: call `gpu_inventory_list` and `images_list`; rank two or three live options by VRAM fit, availability, total hourly cost, and architecture constraints.
- Launch: call `account_token_validation`, `account_billing`, `ssh_keys_list`, `gpu_inventory_list`, and `images_list` before `instances_launch`; verify with `instances_get` or `instances_list`.
- Status: call `instances_list`; use `instances_get` for exact details. Report UUID, name, GPU, region, state, age, and hourly cost.
- Spend audit: combine `instances_list`, live product pricing, and `account_billing`; calculate per-instance and fleet hourly/daily burn plus recharge runway when balances are available.
- Restart: inspect the instance first, restart only the named UUID, then poll until healthy.
- Terminate: follow the destructive confirmation rule above; never terminate from a vague description without resolving it to exact UUIDs.
- SSH keys: list before creating. Add only a public key with a clear device name. Deletion requires exact disclosure, confirmation, and post-delete verification.

## Tool availability

Read-only tokens expose inventory, images, instances, coupons, token validation, billing, and SSH-key listing. Full-access tokens additionally expose launch, restart, terminate, SSH-key creation, and SSH-key deletion. If a mutation tool is absent, identify the token scope as the cause instead of guessing.

## Gotchas

- A 401 usually means the token was truncated; re-copy it unchanged.
- A 402 on launch means recharge billing is not configured.
- GPU/image compatibility is enforced; SXM-only and PCIe images are not interchangeable.
- A 429 is a rate limit; wait briefly and retry without duplicating a launch.
- `instances_list` and `instances_get` redact cleartext VM passwords before the model sees them.
- Environment-variable changes require a new Codex process before MCP authentication is available.

## Troubleshooting

- No Massed Compute tools: verify the MCP entry, `MC_TOKEN`, network access, and restart Codex.
- Read tools exist but launch/terminate does not: replace the read-only API key with a full-access key only if mutations are required.
- Launch failed after a timeout: list instances before retrying; the first request may have succeeded.
- Cannot SSH: verify instance state, registered public key, username/image instructions, host/port, and local private-key availability.
- Unclear or stale price: refresh `gpu_inventory_list`; never reuse an old quote.
