# conventions -- how we write code in this repo

Idioms the existing code follows. If you are adding a new file, match
this list. If you are editing, match the style already there unless
you have a reason documented in `decisions.md`.

<!-- Keep sections that apply, delete the ones you do not need. Fill
each section with *your* stack-specific rules. Example stubs below. -->

## Imports

<!-- e.g. `from __future__ import annotations` at top; stdlib ->
third-party -> first-party with blank lines between -->

## Async / concurrency

<!-- async idioms, when to gather vs await-in-loop, session scopes -->

## Error handling

<!-- when to catch, when to let propagate, custom exception hierarchy,
whether to log-and-reraise or log-and-swallow -->

## Logging

<!-- module-level logger convention, levels, what must NOT be logged
(secrets), per-library overrides -->

## Types

<!-- annotations policy, None vs Optional, runtime coercion at
boundaries, dataclass vs dict -->

## Data classes and models

<!-- ORM conventions, where business logic goes, nullable policy -->

## Settings and env

<!-- pattern for reading env, secret wrapping, single choke point -->

## Tests

<!-- test layout, naming, source-level vs live vs integration, regression
tests carrying finding IDs in docstrings -->

## Commits

<!-- commit message format (conventional commits?), one-concern-per-
commit policy, co-author lines for agent-assisted work -->

## File layout

<!-- per-package __init__ conventions, file-per-class policy, splitting
thresholds -->

## Documentation

<!-- module docstrings, function docstrings when required, inline
comment policy, review-finding cross-references in code -->

## Naming

<!-- case conventions, private prefix rules, boolean field naming -->

## What we specifically avoid

<!-- anti-patterns list: global state, reflection as control flow,
string interpolation in SQL, pre-commit-only enforcement, etc. -->
