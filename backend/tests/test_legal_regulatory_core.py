"""Part 2 deterministic G/H core: SYNTHETIC unvalidated fixtures only, no DB/settings/network/model."""
from datetime import date, datetime, timedelta, timezone
import unittest

from app.services.regulatory_versions import RegulatoryVersion, version_as_of, exact_diff, source_freshness
from app.services.compliance_assessment import (
    STATES, Check, Rule, Evidence, Component, Applicability, Requirement, assess, drift_reasons, impact,
)

UTC = timezone.utc
NOW = datetime(2026, 10, 6, 12, tzinfo=UTC)
V1 = RegulatoryVersion("syn-reg-v1", "a" * 64, date(2024, 1, 1), date(2026, 7, 1), published_at=date(2023, 11, 1))
V2 = RegulatoryVersion("syn-reg-v2", "b" * 64, date(2026, 7, 1), published_at=date(2026, 3, 1))
POLICY = Rule("syn-policy-approved", "1", (Check("policy_approved", "eq", True),))
TESTING = Rule("syn-control-tested", "1", (Check("tests_per_year", "ge", 1),))
APPLIES = Applicability("applicable", "syn-decision-1")


def ev(eid, facts, accepted=True, days_ago=10, valid_days=None, **kw):
    observed = NOW - timedelta(days=days_ago)
    until = observed + timedelta(days=valid_days) if valid_days is not None else None
    return Evidence(eid, observed, tuple(facts.items()), accepted, until, **kw)


def req(*components, applicability=APPLIES, **kw):
    return Requirement("syn-req-1", "ws-a", applicability, components, **kw)


class RegulatoryVersionTests(unittest.TestCase):
    def test_half_open_as_of_selection(self):
        self.assertEqual(version_as_of([V1, V2], date(2026, 6, 30)).version, V1)
        self.assertEqual(version_as_of([V1, V2], date(2026, 7, 1)).version, V2)  # until is exclusive
        self.assertEqual(version_as_of([V1, V2], date(2023, 12, 31)).status, "none_effective")

    def test_publication_does_not_imply_effectivity(self):
        self.assertEqual(version_as_of([V1, V2], date(2026, 4, 1)).version, V1)  # V2 published, not effective

    def test_unknown_and_overlapping_dates_need_verification(self):
        unknown = RegulatoryVersion("syn-reg-v3", "c" * 64, None)
        result = version_as_of([V1, V2, unknown], date(2026, 8, 1))
        self.assertEqual((result.status, result.version), ("needs_verification", None))
        self.assertIn("syn-reg-v3: effective_from unknown", result.reasons)
        overlap = RegulatoryVersion("syn-reg-amend", "d" * 64, date(2025, 1, 1))
        self.assertIn("overlapping", version_as_of([V1, overlap], date(2025, 6, 1)).reasons[0])

    def test_invalid_interval_and_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            RegulatoryVersion("bad", "e" * 64, date(2026, 1, 2), date(2026, 1, 1))
        with self.assertRaises(ValueError):
            version_as_of([V1, V1], date(2025, 1, 1))

    def test_exact_structural_diff(self):
        old = [("s1", "Keep records 5 years."), ("s2", "Report annually."), ("s3", "Old duty.")]
        new = [("s2", "Report annually."), ("s1", "Keep records 7 years."), ("s4", "New duty.")]
        kinds = {(c.section_ref, c.kind) for c in exact_diff(old, new)}
        self.assertTrue({("s1", "modified"), ("s3", "removed"), ("s4", "added"), ("s1", "reordered")} <= kinds)
        modified = next(c for c in exact_diff(old, new) if c.kind == "modified")
        self.assertIn("-Keep records 5 years.", modified.text_diff)
        self.assertIn("+Keep records 7 years.", modified.text_diff)
        self.assertEqual(exact_diff(old, old), [])
        with self.assertRaises(ValueError):
            exact_diff([("s1", "a"), ("s1", "b")], [])

    def test_failed_check_is_unavailable_not_no_change(self):
        day = timedelta(days=1)
        self.assertEqual(source_freshness(NOW, 7 * day, NOW - day)[0], "fresh")
        self.assertEqual(source_freshness(NOW, 7 * day, NOW - 8 * day)[0], "stale")
        self.assertEqual(source_freshness(NOW, 7 * day, NOW - 2 * day, NOW - day)[0], "unavailable")
        self.assertEqual(source_freshness(NOW, 7 * day, None)[0], "never_checked")
        with self.assertRaises(ValueError):
            source_freshness(NOW.replace(tzinfo=None), day, None)


class ComplianceAssessmentTests(unittest.TestCase):
    def test_six_states_with_reasons(self):
        good_policy = Component("c-policy", POLICY, (ev("e1", {"policy_approved": True}),))
        good_test = Component("c-test", TESTING, (ev("e2", {"tests_per_year": 2}),))
        no_test = Component("c-test", TESTING, ())
        cases = {
            "satisfied": req(good_policy, good_test),
            "partially_satisfied": req(good_policy, no_test),
            "unsatisfied": req(good_policy, Component("c-test", TESTING, (ev("e3", {"tests_per_year": 0}),))),
            "insufficient_evidence": req(Component("c-policy", POLICY, ()), no_test),
            "not_applicable": req(good_policy, applicability=Applicability("not_applicable", "syn-decision-2")),
            "needs_review": req(good_policy, applicability=Applicability("applicable")),
        }
        for state, requirement in cases.items():
            result = assess(requirement, NOW)
            self.assertEqual(result.status, state)
            self.assertTrue(result.reasons)
        self.assertEqual(set(cases), set(STATES))

    def test_missing_evidence_is_never_violation(self):
        unaccepted = Component("c-policy", POLICY, (ev("e1", {"policy_approved": False}, accepted=False),))
        lacks_fact = Component("c-test", TESTING, (ev("e2", {"unrelated": 1}),))
        self.assertEqual(assess(req(unaccepted), NOW).status, "insufficient_evidence")
        self.assertEqual(assess(req(lacks_fact), NOW).status, "insufficient_evidence")

    def test_expired_stale_superseded_and_conflicting_evidence(self):
        expired = Component("c", POLICY, (ev("e1", {"policy_approved": True}, valid_days=5),))
        stale = Component("c", POLICY, (ev("e1", {"policy_approved": True}, days_ago=400),), timedelta(days=365))
        superseded = Component("c", POLICY, (ev("e1", {"policy_approved": True}, superseded=True),))
        conflict = Component("c", POLICY, (ev("e1", {"policy_approved": True}), ev("e2", {"policy_approved": False})))
        for comp, words in ((expired, "expired"), (stale, "stale"), (superseded, "superseded")):
            result = assess(req(comp), NOW)
            self.assertEqual(result.status, "insufficient_evidence")
            self.assertTrue(any(words in r for r in result.reasons))
        self.assertEqual(assess(req(conflict), NOW).status, "needs_review")

    def test_applicability_and_pending_change_need_review(self):
        comp = Component("c", POLICY, (ev("e1", {"policy_approved": True}),))
        self.assertEqual(assess(req(comp, applicability=Applicability("not_applicable")), NOW).status, "needs_review")
        self.assertEqual(assess(req(comp, pending_change_review=True), NOW).status, "needs_review")
        self.assertEqual(assess(req(), NOW).status, "needs_review")

    def test_deterministic_and_type_safe(self):
        comp = Component("c", TESTING, (ev("e1", {"tests_per_year": "often"}),))
        first, second = assess(req(comp), NOW), assess(req(comp), NOW)
        self.assertEqual(first, second)
        self.assertEqual(first.status, "needs_review")
        self.assertEqual(first.rule_versions, ("syn-control-tested@1",))
        with self.assertRaises(ValueError):
            Check("x", "regex", ".*")

    def test_drift_invalidates_current_without_rewriting_history(self):
        comp = Component("c", POLICY, (ev("e1", {"policy_approved": True}, valid_days=15),))
        original = assess(req(comp), NOW)
        self.assertEqual((original.status, drift_reasons(original, req(comp), NOW)), ("satisfied", []))
        later = NOW + timedelta(days=6)
        self.assertIn("lapsed", drift_reasons(original, req(comp), later)[0])
        self.assertEqual(assess(req(comp), later).status, "insufficient_evidence")
        self.assertEqual(original.status, "satisfied")  # historical assessment unchanged
        changed = req(comp, pending_change_review=True)
        self.assertIn("inputs changed", drift_reasons(original, changed, NOW)[0])

    def test_blast_radius_and_cross_workspace_denial(self):
        nodes = {"reg-v2": "ws-a", "req-1": "ws-a", "ctl-1": "ws-a", "ev-1": "ws-a", "req-2": "ws-a", "other": "ws-b"}
        links = [("reg-v2", "req-1"), ("ev-1", "ctl-1"), ("ctl-1", "req-1"), ("ctl-1", "req-2")]
        self.assertEqual(impact(nodes, links, {"ev-1"}),
                         {"ctl-1": ("ev-1", "ctl-1"), "req-1": ("ev-1", "ctl-1", "req-1"),
                          "req-2": ("ev-1", "ctl-1", "req-2")})
        self.assertEqual(impact(nodes, links, {"reg-v2"}), {"req-1": ("reg-v2", "req-1")})
        with self.assertRaises(ValueError):
            impact(nodes, links + [("ctl-1", "other")], {"ev-1"})
        with self.assertRaises(ValueError):
            impact(nodes, [("ghost", "req-1")], {"ghost"})

    def test_demo_version_change_and_expiry_yield_explainable_reevaluation(self):
        """Regulation v1->v2 changes + evidence expiry -> pending review, impacted requirement, reasons."""
        diff = exact_diff([("s1", "Test controls annually.")], [("s1", "Test controls twice a year.")])
        self.assertEqual(diff[0].kind, "modified")
        self.assertEqual(version_as_of([V1, V2], NOW.date()).version, V2)
        comp = Component("c", TESTING, (ev("e1", {"tests_per_year": 1}, valid_days=20),))
        before = assess(req(comp), NOW)
        self.assertEqual(before.status, "satisfied")
        after = assess(req(comp, pending_change_review=True), NOW + timedelta(days=11))
        self.assertEqual(after.status, "needs_review")
        self.assertTrue(any("expired" in r for r in after.reasons))
        self.assertEqual(len(drift_reasons(before, req(comp, pending_change_review=True), NOW + timedelta(days=11))), 2)
        self.assertIn("req-1", impact({"reg": "ws-a", "req-1": "ws-a"}, [("reg", "req-1")], {"reg"}))


if __name__ == "__main__":
    unittest.main()
