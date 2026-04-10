# Project Rules

## Stack

{{framework}} + {{language}} + {{styling}} + {{database}}

## Commands

```bash
# Development
{{dev_command}}

# Test
{{test_command}}

# Build
{{build_command}}

# Lint
{{lint_command}}

# Type check
{{typecheck_command}}
```

## File Structure

```
src/
  components/    # Reusable UI components
  pages/         # Route-level components
  lib/           # Shared utilities, API clients
  hooks/         # Custom React/Vue hooks
  types/         # TypeScript type definitions
```

## Style Guide

```typescript
// Components: PascalCase, one component per file
// Files: kebab-case (user-profile.tsx, not UserProfile.tsx)
// Hooks: usePrefix (useAuth, useDebounce)
// Utils: camelCase functions, UPPER_SNAKE for constants

// Prefer named exports over default exports
export function UserProfile() { ... }

// Error handling: at component boundaries, not every function
// Use error boundaries for rendering, try/catch for async
```

## API Patterns

```typescript
// API calls go through lib/api.ts, not directly in components
// Use {{data_fetching}} for data fetching
// Environment-specific URLs in .env, never hardcoded
```

## Testing

```typescript
// Unit tests: *.test.ts next to the source file
// Integration tests: tests/ directory
// Test user behavior, not implementation details
// Mock external APIs, not internal modules
```

## Red Lines

1. Never commit .env files - use .env.example for templates
2. Never use `any` type without a comment explaining why
3. Never fetch data in components - use hooks or server-side
4. Never store sensitive data in localStorage - use httpOnly cookies
5. Never disable eslint rules without a comment

## Supply Chain Defense

```ini
# ~/.npmrc (or project .npmrc)
min-release-age=7
```
