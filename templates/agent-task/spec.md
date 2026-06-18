# Task Spec: {{task_id}}

## Objective

{{one_sentence_objective}}

## Scope

- In scope: {{in_scope}}
- Out of scope: {{out_of_scope}}

## Global Constraints

- Repository/branch boundary: {{repo_and_branch}}
- Allowed write locations: {{allowed_write_paths}}
- Forbidden operations: {{no_go_operations}}
- External side effects allowed: {{external_side_effects_policy}}
- Budget/time constraints: {{budget_or_time_constraints}}
- Required evidence: {{evidence_requirements}}

## Acceptance Criteria

- AC1: {{criterion_1}}
- AC2: {{criterion_2}}
- AC3: {{criterion_3}}

## Verification Commands

```bash
{{verification_command_1}}
{{verification_command_2}}
```

## Fresh Verifier Instructions

Verify only the final repo state and evidence in this task directory. Do not trust builder claims. Write the result to `verdict.json`.
