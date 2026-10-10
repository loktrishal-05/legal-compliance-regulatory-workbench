"""Persisted-row projections using the existing deterministic regulatory core."""
from datetime import timedelta

from app.services.regulatory_versions import RegulatoryVersion, exact_diff, source_freshness, version_as_of


def historical_version(rows, effective_on, known_at):
    if known_at.tzinfo is None:
        raise ValueError("known_at must be timezone-aware")
    versions = [RegulatoryVersion(str(row.id), row.source_sha256, row.effective_from,
                row.effective_until, row.published_at) for row in rows if row.imported_at <= known_at]
    result = version_as_of(versions, effective_on)
    return {"status": result.status, "version_id": result.version.version_id if result.version else None,
            "reasons": list(result.reasons), "effective_on": effective_on.isoformat(), "known_at": known_at.isoformat()}


def monitoring_status(now, max_age_days, last_success_at, last_failure_at):
    if max_age_days <= 0:
        raise ValueError("max_age_days must be positive")
    freshness, reason = source_freshness(now, timedelta(days=max_age_days), last_success_at, last_failure_at)
    return {"monitoring": "not_monitored", "import_policy": "manual", "freshness": freshness, "reason": reason}


def structural_changes(old_sections, new_sections):
    return [{"section_ref": change.section_ref, "kind": change.kind, "text_diff": list(change.text_diff)}
            for change in exact_diff(old_sections, new_sections)]
