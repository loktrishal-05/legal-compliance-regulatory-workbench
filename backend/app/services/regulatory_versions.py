"""Deterministic regulatory version logic (Phase G): as-of selection, exact diff, source freshness.

Pure functions over labelled inputs; no DB, settings, network or model calls. Persistence,
registry approval and human applicability decisions land with migration 0022 after Part 1's 0021.
Effective intervals are half-open [effective_from, effective_until). Unknown dates stay unknown.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import difflib


@dataclass(frozen=True)
class RegulatoryVersion:
    version_id: str
    source_sha256: str
    effective_from: date | None  # None = unknown, needs verification
    effective_until: date | None = None  # exclusive; None = no recorded end
    published_at: date | None = None  # publication never implies effectivity

    def __post_init__(self):
        if self.effective_from and self.effective_until and self.effective_until <= self.effective_from:
            raise ValueError(f"{self.version_id}: effective_until must be after effective_from")


@dataclass(frozen=True)
class AsOfResult:
    status: str  # effective | none_effective | needs_verification
    version: RegulatoryVersion | None
    reasons: tuple[str, ...] = field(default_factory=tuple)


def version_as_of(versions, as_of: date) -> AsOfResult:
    """Select the single version in force on `as_of`; ambiguity is never resolved by recency."""
    ids = [v.version_id for v in versions]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate version_id")
    matches = [v for v in versions if v.effective_from is not None and v.effective_from <= as_of
               and (v.effective_until is None or as_of < v.effective_until)]
    unknown = sorted(v.version_id for v in versions if v.effective_from is None)
    reasons = [f"{vid}: effective_from unknown" for vid in unknown]
    if len(matches) > 1:
        reasons.insert(0, "overlapping effective intervals: " + ", ".join(sorted(v.version_id for v in matches)))
        return AsOfResult("needs_verification", None, tuple(reasons))
    if unknown:
        return AsOfResult("needs_verification", None, tuple(reasons))
    if matches:
        return AsOfResult("effective", matches[0])
    return AsOfResult("none_effective", None, (f"no version effective on {as_of.isoformat()}",))


@dataclass(frozen=True)
class SectionChange:
    section_ref: str
    kind: str  # added | removed | modified | reordered
    text_diff: tuple[str, ...] = ()


def exact_diff(old_sections, new_sections) -> list[SectionChange]:
    """Structural + exact text differences between ordered (section_ref, text) pairs.

    Semantic change explanations are separate AI proposals; this exact record is kept beside them.
    """
    old, new = dict(old_sections), dict(new_sections)
    if len(old) != len(old_sections) or len(new) != len(new_sections):
        raise ValueError("duplicate section_ref")
    changes = []
    for ref, text in new_sections:
        if ref not in old:
            changes.append(SectionChange(ref, "added", tuple(text.splitlines())))
        elif old[ref] != text:
            diff = difflib.unified_diff(old[ref].splitlines(), text.splitlines(), "old", "new", lineterm="")
            changes.append(SectionChange(ref, "modified", tuple(diff)))
    changes += [SectionChange(ref, "removed", tuple(text.splitlines())) for ref, text in old_sections if ref not in new]
    common_old = [r for r, _ in old_sections if r in new]
    common_new = [r for r, _ in new_sections if r in old]
    changes += [SectionChange(r, "reordered") for r, o in zip(common_new, common_old) if r != o]
    return changes


def _aware(value, name):
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def source_freshness(now: datetime, max_age: timedelta, last_success_at: datetime | None,
                     last_failure_at: datetime | None = None) -> tuple[str, str]:
    """(fresh | stale | unavailable | never_checked, reason). A failed check is never 'no change'."""
    for value, name in ((now, "now"), (last_success_at, "last_success_at"), (last_failure_at, "last_failure_at")):
        _aware(value, name)
    if last_failure_at and (last_success_at is None or last_failure_at > last_success_at):
        return "unavailable", f"last check failed at {last_failure_at.isoformat()}"
    if last_success_at is None:
        return "never_checked", "no successful import or check recorded"
    if now - last_success_at > max_age:
        return "stale", f"last successful check {last_success_at.isoformat()} older than {max_age}"
    return "fresh", f"checked {last_success_at.isoformat()}"
