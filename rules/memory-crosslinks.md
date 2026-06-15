# Memory Cross-Links - wiki-links graph pattern

Memory files can reference each other using wiki-links `[[filename]]` (without .md extension). This creates a navigable knowledge graph without any database.

## Where to add links

**Inline** in text body:
```markdown
Training runs on [[reference_gpu_servers]] using the [[docker_production]] image.
```

**## Related** section at end of file:
```markdown
## Related
- [[reference_gpu_servers]] - trains on these servers
- [[project_model_v2]] - result of this training
- [[practice_autoresearch]] - methodology used for optimization
```

## When to add links

- When **creating** a new memory file - immediately link to existing related entries
- When **updating** a memory file - check if new connections emerged
- Only **meaningful** relationships, not links for the sake of linking
- A good test: "would navigating this link help me understand the current entry better?"

## Common clusters

| Cluster | Contains | Example links |
|---|---|---|
| Infrastructure | servers, docker, tunnels, access rules | server -> docker image -> access rules |
| Projects | active work, LoRAs, research | project -> server (where it runs) -> methodology (how) |
| Methodology | practices, patterns, articles | practice -> article (source) -> project (applied in) |
| Tools | references, repos, services | tool A <-> tool B (alternatives) |
| Feedback | corrections, rules | feedback -> context (which project/server triggered it) |

## Provenance tags - mark verified vs inferred

Adopted from the Hermes LLM-wiki pattern (2026-06-15): a memory must be honest about *how sure* each load-bearing claim is, so a future session knows what to trust vs re-verify. This is `no-guessing.md` extended into memory - the recall caveat already says "verify a named file/flag still exists before recommending"; provenance tags make that explicit at write time.

Tag **load-bearing** claims (facts that drive a decision), not every sentence - over-tagging is noise:

- `(extracted)` - taken directly from a verifiable source: code, probe/command output, docs, or a user quote. Strongest. Name the source inline where useful: `port 5877 (extracted: ssh config)`.
- `(inferred)` - my own conclusion/deduction, not stated by any single source. Next session treats it as a hypothesis.
- `(ambiguous)` - sources disagree, or the claim is unverified/uncertain. Flags "check before acting".

Notation: a short inline marker after the claim, or one provenance note per section. Keep it light. An untagged claim reads as an ordinary durable fact - reserve tags for where verified-vs-guessed actually matters (infra values, "X works/exists", capacities, anything a future session would act on).

Example:
```markdown
The GPU host has NO fail2ban (extracted: /etc/fail2ban absent, checked on host).
The flaky link is probably a snap-packaged daemon (inferred - not root-caused).
Upload ceiling ~0.5 MB/s (ambiguous - measured once, may vary by time of day).
```

## Benefits

- **Navigation**: from a project, find which servers it uses and what methodology applies
- **Context**: when reading about a server, see what projects run there
- **Discovery**: find related knowledge you forgot existed
- **No database**: graph lives in plain markdown, survives any tool change
