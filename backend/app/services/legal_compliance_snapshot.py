"""JSON snapshot adapter. Inputs must be assembled from authorized persisted records."""
from dataclasses import asdict
from datetime import datetime

from app.services.canonicalization import canonical_hash
from app.services.compliance_assessment import Applicability, Check, Component, Evidence, Requirement, Rule, assess


def instant(value):
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    if result is not None and result.tzinfo is None:
        raise ValueError("snapshot timestamps must be timezone-aware")
    return result


def evaluate_snapshot(inputs, now):
    components = []
    for item in inputs["components"]:
        evidence = []
        for record in item["evidence"]:
            observed, valid_from = instant(record["observed_at"]), instant(record["valid_from"])
            evidence.append(Evidence(record["evidence_id"], max(observed, valid_from),
                tuple(record["facts"].items()), record["accepted"], instant(record.get("expires_at")),
                record.get("superseded", False)))
        rule = Rule(item["rule_id"], item["rule_version"], tuple(Check(**check) for check in item["checks"]))
        components.append(Component(item["control_id"], rule, tuple(evidence)))
    result = assess(Requirement(inputs["requirement_id"], inputs["workspace_id"],
        Applicability(**inputs["applicability"]), tuple(components), inputs.get("pending_change_review", False)), now)
    data = asdict(result)
    data["evaluated_at"] = result.evaluated_at.isoformat()
    data["current_until"] = result.current_until.isoformat() if result.current_until else None
    data["inputs_digest"] = canonical_hash(inputs)
    return data


def projection(snapshot, current_inputs, now):
    reasons = []
    if snapshot["inputs_digest"] != canonical_hash(current_inputs):
        reasons.append("requirement, rule, applicability or evidence inputs changed")
    if snapshot["current_until"] and now >= instant(snapshot["current_until"]):
        reasons.append("evidence currency lapsed")
    current = evaluate_snapshot(current_inputs, now)
    if current["status"] != snapshot["status"] and not reasons:
        reasons.append("time-dependent evidence validity changed")
    return {"freshness": "stale" if reasons else "current", "reasons": reasons,
            "current_status": current["status"], "review_state": "not_approved"}
