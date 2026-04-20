# Principle 17: DBS Framework for Skill Creation

## Direction / Blueprints / Solutions

When creating a skill from research material, split the content into three categories:

### Direction (-> SKILL.md core)

Step-by-step logic, decision trees, error handling. The "how to think about this" part.

- When to use approach A vs B
- Decision flowcharts
- Error recovery paths
- Edge case handling

This becomes the main body of SKILL.md.

### Blueprints (-> references/)

Static reference materials that don't change between invocations.

- Templates (email templates, code scaffolds, config snippets)
- Tone/style guidelines
- Classification rules and taxonomies
- Lookup tables, parameter ranges

These become companion files in `references/` directory.

### Solutions (-> scripts/)

Tasks requiring deterministic code, not LLM reasoning.

- API calls (fetch data, post results)
- Data formatting (CSV -> JSON, markdown -> HTML)
- Calculations (pricing, metrics, scoring)
- File operations (rename, move, validate)

These become executable scripts in `scripts/` directory.

## Why this matters

Without DBS, skills become monolithic SKILL.md files where logic, data, and code are mixed together. The model has to parse everything every time, wasting tokens and reducing reliability.

With DBS:
- **Direction** is loaded into context (the model needs to reason about this)
- **Blueprints** are loaded on demand (only when the specific template is needed)
- **Solutions** are executed, not reasoned about (deterministic = no hallucination)

## Example

Creating a "competitor analysis" skill:

```
skills/competitor-analysis/
  SKILL.md              # Direction: analysis framework, scoring rubric,
                        # when to compare pricing vs features vs UX
  references/
    scoring-matrix.md   # Blueprint: 1-10 scale definitions per dimension
    report-template.md  # Blueprint: final report structure
  scripts/
    fetch-pricing.py    # Solution: scrape competitor pricing pages
    generate-chart.py   # Solution: create comparison chart from data
```

## Integration with /skill-creator

Claude Code's built-in `/skill-creator` meta-skill can use the DBS framework automatically. When feeding it research output, explicitly label sections as D, B, or S to guide the generation.

## Source

Adapted from @hooeem's NotebookLM integration guide (April 2026), which formalized this pattern for converting Deep Research output into Claude Code skills.
