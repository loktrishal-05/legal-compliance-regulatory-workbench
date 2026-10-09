"""Synthetic source-time projection; never infer a configured feed or effectivity."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from app.services.legal_regulatory_projection import historical_version, monitoring_status, structural_changes

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


class RegulatoryProjectionTests(unittest.TestCase):
    def test_unconfigured_manual_feed_never_claims_monitoring(self):
        self.assertEqual(monitoring_status(NOW, 7, None, None)["monitoring"], "not_monitored")
        failed = monitoring_status(NOW, 7, NOW - timedelta(days=2), NOW - timedelta(days=1))
        self.assertEqual(failed["freshness"], "unavailable")
        self.assertNotIn("no change", failed["reason"])

    def test_historical_import_cutoff_and_unknown_effectivity(self):
        first = SimpleNamespace(id="v1", source_sha256="a" * 64, effective_from=date(2025, 2, 1),
            effective_until=None, published_at=date(2025, 1, 1), imported_at=NOW - timedelta(days=30))
        second = SimpleNamespace(id="v2", source_sha256="b" * 64, effective_from=None,
            effective_until=None, published_at=date(2026, 9, 1), imported_at=NOW)
        self.assertEqual(historical_version([first, second], date(2026, 9, 20), NOW - timedelta(days=1))["version_id"], "v1")
        self.assertEqual(historical_version([first, second], NOW.date(), NOW)["status"], "needs_verification")

    def test_fixture_diff_preserves_exact_text_and_structure(self):
        root = Path(__file__).parent / "fixtures" / "legal_regulatory"
        old, new = [json.loads((root / f"retention-v{i}.json").read_text()) for i in (1, 2)]
        changes = structural_changes(old["sections"], new["sections"])
        self.assertEqual({x["kind"] for x in changes}, {"added", "removed", "modified", "reordered"})
        self.assertIn("-Keep records for five years.", next(x for x in changes if x["kind"] == "modified")["text_diff"])

    def test_naive_clock_and_invalid_age_rejected(self):
        for days in (0, -1):
            with self.assertRaises(ValueError):
                monitoring_status(NOW, days, None, None)
        with self.assertRaises(ValueError):
            historical_version([], NOW.date(), NOW.replace(tzinfo=None))
