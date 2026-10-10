"""Frozen deterministic compliance inputs; synthetic facts only."""
from datetime import datetime, timedelta, timezone
import unittest

from app.services.legal_compliance_snapshot import evaluate_snapshot, projection

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


class ComplianceSnapshotTests(unittest.TestCase):
    def inputs(self, facts=None, **overrides):
        data = {"requirement_id": "r1", "workspace_id": "ws1",
            "applicability": {"state": "applicable", "decision_id": "approved-decision"},
            "components": [{"control_id": "c1", "rule_id": "rule1", "rule_version": "1",
                "checks": [{"fact": "retention_years", "op": "ge", "value": 7}],
                "evidence": [] if facts is None else [{"evidence_id": "e1", "accepted": True,
                    "observed_at": NOW.isoformat(), "valid_from": NOW.isoformat(),
                    "expires_at": (NOW + timedelta(days=1)).isoformat(), "facts": facts}]}]}
        data.update(overrides)
        return data

    def test_all_six_states(self):
        good = self.inputs({"retention_years": 7})
        partial = self.inputs({"retention_years": 7})
        partial["components"].append({**partial["components"][0], "control_id": "c2", "evidence": []})
        cases = {"satisfied": good, "partially_satisfied": partial,
            "unsatisfied": self.inputs({"retention_years": 2}), "insufficient_evidence": self.inputs(),
            "not_applicable": self.inputs(applicability={"state": "not_applicable", "decision_id": "approved-decision"}),
            "needs_review": self.inputs(applicability={"state": "not_applicable", "decision_id": None})}
        for state, inputs in cases.items():
            with self.subTest(state=state):
                result = evaluate_snapshot(inputs, NOW)
                self.assertEqual(result["status"], state)
                self.assertTrue(result["reasons"])

    def test_future_validity_and_expiry_are_insufficient(self):
        inputs = self.inputs({"retention_years": 7})
        inputs["components"][0]["evidence"][0]["valid_from"] = (NOW + timedelta(hours=1)).isoformat()
        self.assertEqual(evaluate_snapshot(inputs, NOW)["status"], "insufficient_evidence")
        self.assertEqual(evaluate_snapshot(inputs, NOW + timedelta(days=1))["status"], "insufficient_evidence")

    def test_history_retained_when_current_projection_stales(self):
        inputs = self.inputs({"retention_years": 7})
        historical = evaluate_snapshot(inputs, NOW)
        current = projection(historical, inputs, NOW + timedelta(days=1))
        self.assertEqual(historical["status"], "satisfied")
        self.assertEqual(current["freshness"], "stale")
        self.assertEqual(current["current_status"], "insufficient_evidence")
        self.assertTrue(current["reasons"])

    def test_conflict_and_client_approval_cannot_be_silently_resolved(self):
        inputs = self.inputs({"retention_years": 7})
        inputs["components"][0]["evidence"].append({**inputs["components"][0]["evidence"][0],
            "evidence_id": "e2", "facts": {"retention_years": 2}})
        self.assertEqual(evaluate_snapshot(inputs, NOW)["status"], "needs_review")
