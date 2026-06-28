# App Pre-Launch Security Checklist

Use before launching any web app, SaaS feature, public API, auth flow, payment/API-cost
flow, or user-data collection path. This is a verification checklist, not a prompt-only
review. Every item needs an artifact: config screenshot/export, test output, code pointer,
or scanner report.

## Required Gates

1. **Privacy and data map**
   - Identify personal data collected, storage location, processors, retention, and deletion/export path.
   - Publish/update privacy policy before collecting user data.
   - Evidence: privacy policy URL/file plus data map.

2. **Database access control / RLS**
   - For Supabase/Postgres exposed schemas, RLS must be enabled and policies must be present.
   - Test anonymous, authenticated own-record, authenticated other-record, and service-role paths.
   - Evidence: SQL/policy export plus negative access tests.

3. **Auth negative-path tests**
   - Test wrong password repeated attempts, nonexistent email password reset, reused confirmation link, duplicate signup email, expired token, and cross-user resource access.
   - Evidence: automated tests or manual test log with timestamps/results.

4. **Security headers and baseline hardening**
   - Verify CSP, HSTS where HTTPS-only, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, and frame/clickjacking policy as applicable.
   - Evidence: header scan output and explicit accepted exceptions.

5. **OWASP Top 10 / ASVS-style review**
   - Check injection, broken access control, auth/session errors, XSS, SSRF, insecure design, security misconfiguration, vulnerable dependencies, logging/monitoring gaps.
   - Evidence: review report with findings and fixes/skips.

6. **Server-side validation**
   - Client validation is UX only. Repeat every security/business validation on server/API boundary.
   - Evidence: tests that bypass browser JavaScript and hit API directly.

7. **Sensitive data exposure audit**
   - Confirm `.env` values do not enter frontend bundles.
   - Confirm API responses are least-data / no overbroad DTOs.
   - Confirm logs redact credentials, tokens, PII, and paid-provider payload secrets.
   - Evidence: bundle grep, API response samples, log redaction tests.

8. **API key boundary**
   - No private API keys in browser/mobile client bundles. Use server-side calls, scoped publishable keys, or backend proxy.
   - Evidence: bundle/source grep and runtime network inspection.

9. **Rate limiting and cost guardrails**
   - Rate-limit public endpoints, auth endpoints, and every route that can trigger paid APIs or expensive jobs.
   - Add per-user/per-IP/per-token quotas and budget alerts for paid providers.
   - Evidence: load/abuse test proving 429/deny and cost cap behavior.

10. **Bot and CORS controls**
    - Add bot friction such as Cloudflare Turnstile on public forms where abuse matters.
    - Restrict CORS to approved origins; no credentialed `*`.
    - Evidence: Turnstile server-side token validation test and CORS preflight tests.

11. **Safe error handling**
    - Users see neutral errors; server logs keep actionable diagnostics with redaction.
    - No SQL, stack traces, secrets, internal hostnames, or dependency versions in user-visible errors.
    - Evidence: negative-path API samples and log samples.

## AI Review Prompt

Use this only after collecting concrete artifacts:

```text
Audit this app as a security reviewer. Use the attached configs, test outputs,
API samples, and code pointers. Check privacy/data map, RLS/access control,
auth negative paths, headers, OWASP Top 10, server-side validation, sensitive
data exposure, API key boundaries, rate limiting/cost controls, bot/CORS
controls, and safe error handling. Return findings with severity, evidence,
fix, and verification command. Do not mark an item pass without evidence.
```

## Sources

- GDPR privacy notice guidance: https://gdpr.eu/privacy-notice/
- CCPA overview: https://oag.ca.gov/privacy/ccpa
- Supabase RLS docs: https://supabase.com/docs/guides/database/postgres/row-level-security
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP Secure Headers: https://owasp.org/www-project-secure-headers/
- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- OWASP Error Handling Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html
- MDN CORS guide: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS
- Cloudflare Turnstile: https://developers.cloudflare.com/turnstile/
