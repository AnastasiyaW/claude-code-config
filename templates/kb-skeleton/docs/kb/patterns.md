# patterns -- recipes for common tasks

Step-by-step guides for things we do often enough that each session
should not reinvent them. Every recipe references the `INVARIANTS` and
the regression tests that check you got it right.

<!-- Add recipes organically. Below is an example skeleton. -->

## P-1 -- <recipe name, e.g. "Add a new HTTP handler">

<short description of what you are doing and when to use this>

1. **File:** <where to create>
2. **Imports:** <what to import>
3. **Required boilerplate:** <decorators, null checks, etc>
4. **Business logic:** <pattern>
5. **Registration:** <wire into main.py / app / ...>
6. **User-facing strings:** <where they live, escaping rules>
7. **Test:** <what to add, which test file, which docstring pattern>

Do **not** <anti-pattern>. See **I-N**.

<!-- Copy block per recipe. Keep each under ~30 lines. -->
