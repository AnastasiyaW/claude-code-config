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

## Benefits

- **Navigation**: from a project, find which servers it uses and what methodology applies
- **Context**: when reading about a server, see what projects run there
- **Discovery**: find related knowledge you forgot existed
- **No database**: graph lives in plain markdown, survives any tool change
