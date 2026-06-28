#!/usr/bin/env python3
"""Tests for the app pre-launch security checklist."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "rules" / "app-prelaunch-security-checklist.md"
MOA = ROOT / "rules" / "moa-gemini-delegation-eval.md"

REQUIRED_SECURITY_TERMS = (
    "Privacy and data map",
    "Database access control / RLS",
    "Auth negative-path tests",
    "Security headers",
    "OWASP Top 10",
    "Server-side validation",
    "Sensitive data exposure audit",
    "API key boundary",
    "Rate limiting",
    "Bot and CORS controls",
    "Safe error handling",
)

REQUIRED_SOURCES = (
    "gdpr.eu/privacy-notice",
    "oag.ca.gov/privacy/ccpa",
    "supabase.com/docs/guides/database/postgres/row-level-security",
    "owasp.org/www-project-top-ten",
    "developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS",
    "developers.cloudflare.com/turnstile",
)


class AppSecurityChecklistTests(unittest.TestCase):
    def test_security_checklist_has_all_required_gates_and_sources(self) -> None:
        text = CHECKLIST.read_text(encoding="utf-8")
        for term in REQUIRED_SECURITY_TERMS:
            self.assertIn(term, text)
        for source in REQUIRED_SOURCES:
            self.assertIn(source, text)

    def test_moa_gate_requires_eval_before_adoption(self) -> None:
        text = MOA.read_text(encoding="utf-8")
        self.assertIn("Do not adopt MoA globally", text)
        self.assertIn("Approval Criteria", text)
        self.assertIn("cost/quota burn", text)
        self.assertIn("gemini-delegate", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
