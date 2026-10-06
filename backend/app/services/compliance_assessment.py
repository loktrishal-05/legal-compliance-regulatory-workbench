"""Deterministic compliance assessment (Phase H): six explainable states, evidence currency, drift, impact.

Pure functions; no DB, model calls or numeric scores (no approved weights exist). Rules are versioned
declarative checks over JSON-primitive facts carried by accepted evidence, so outcomes repeat exactly.
Results are proposals for review/persistence; they never accept risk or replace an authorized human
decision. Missing evidence is insufficiency, never proof of violation. Assessments are frozen: drift
produces re-evaluation reasons and a new assessment, history is never rewritten.
"""
from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import hashlib
import json

STATES = ("satisfied", "partially_satisfied", "unsatisfied", "insufficient_evidence", "not_applicable", "needs_review")
_OPS = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b, "ge": lambda a, b: a >= b,
        "le": lambda a, b: a <= b, "in": lambda a, b: a in b}


@dataclass(frozen=True)
class Check:
    fact: str
    op: str
    value: object

    def __post_init__(self):
        if self.op not in _OPS:
            raise ValueError(f"unsupported op {self.op}")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    version: str
    checks: tuple[Check, ...]


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    observed_at: datetime
    facts: tuple[tuple[str, object], ...]
    accepted: bool = False  # accepted by an authorized reviewer (Part 3 review ledger)
    valid_until: datetime | None = None  # exclusive
    superseded: bool = False


@dataclass(frozen=True)
class Component:
    component_id: str
    rule: Rule
    evidence: tuple[Evidence, ...] = ()
    max_evidence_age: timedelta | None = None


@dataclass(frozen=True)
class Applicability:
    state: str  # applicable | not_applicable | pending
    decision_id: str | None = None  # authorized human decision with source/version context


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    workspace_id: str
    applicability: Applicability
    components: tuple[Component, ...]
    pending_change_review: bool = False  # accepted source/control change awaiting impact review


@dataclass(frozen=True)
class ComponentResult:
    component_id: str
    outcome: str  # supported | failed | missing | ambiguous
    reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Assessment:
    requirement_id: str
    status: str
    reasons: tuple[str, ...]
    components: tuple[ComponentResult, ...]
    component_summary: tuple[tuple[str, int], ...]  # visible counts instead of an opaque score
    rule_versions: tuple[str, ...]
    evaluated_at: datetime
    inputs_digest: str
    current_until: datetime | None = None  # next evidence expiry/staleness that changes currency


def _aware(value, name):
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")


def _usable(ev: Evidence, comp: Component, now: datetime):
    if not ev.accepted:
        return f"{ev.evidence_id}: not accepted"
    if ev.superseded:
        return f"{ev.evidence_id}: superseded"
    if ev.observed_at > now:
        return f"{ev.evidence_id}: observed after evaluation time"
    if ev.valid_until is not None and now >= ev.valid_until:
        return f"{ev.evidence_id}: expired {ev.valid_until.isoformat()}"
    if comp.max_evidence_age is not None and now - ev.observed_at > comp.max_evidence_age:
        return f"{ev.evidence_id}: stale, observed {ev.observed_at.isoformat()}"
    return None


def evaluate_component(comp: Component, now: datetime) -> ComponentResult:
    reasons, current = [], []
    for ev in comp.evidence:
        _aware(ev.observed_at, "observed_at")
        _aware(ev.valid_until, "valid_until")
        problem = _usable(ev, comp, now)
        if problem:
            reasons.append(problem)
        else:
            current.append(ev)
    ids = tuple(ev.evidence_id for ev in current)
    if not current:
        return ComponentResult(comp.component_id, "missing", tuple(reasons) + ("no current accepted evidence",), ids)
    if not comp.rule.checks:
        return ComponentResult(comp.component_id, "ambiguous", tuple(reasons) + ("rule has no checks",), ids)
    values = {}
    for ev in current:
        for key, value in ev.facts:
            values.setdefault(key, set()).add(json.dumps(value, sort_keys=True))
    outcome = "supported"
    for check in comp.rule.checks:
        seen = values.get(check.fact)
        if not seen:
            reasons.append(f"fact '{check.fact}' not evidenced")
            outcome = "missing" if outcome == "supported" else outcome
            continue
        if len(seen) > 1:
            reasons.append(f"conflicting evidence for '{check.fact}'")
            outcome = "ambiguous" if outcome != "failed" else outcome
            continue
        try:
            passed = _OPS[check.op](json.loads(next(iter(seen))), check.value)
        except TypeError:
            reasons.append(f"'{check.fact}' type incompatible with {check.op} {check.value!r}")
            outcome = "ambiguous" if outcome != "failed" else outcome
            continue
        if not passed:
            reasons.append(f"'{check.fact}' fails {check.op} {check.value!r}")
            outcome = "failed"
    return ComponentResult(comp.component_id, outcome, tuple(reasons), ids)


def _digest(req: Requirement) -> str:
    return hashlib.sha256(json.dumps(asdict(req), sort_keys=True, default=str).encode()).hexdigest()


def assess(req: Requirement, now: datetime) -> Assessment:
    """Six-state proposal with reasons, using the fixed precedence below."""
    _aware(now, "now")
    results = tuple(evaluate_component(c, now) for c in req.components)
    outcomes = Counter(r.outcome for r in results)
    app = req.applicability
    if app.state == "not_applicable" and app.decision_id:
        status, reasons = "not_applicable", [f"applicability decision {app.decision_id}"]
    elif app.state != "applicable" or not app.decision_id:
        status, reasons = "needs_review", ["applicability not decided by an authorized reviewer"]
    elif req.pending_change_review:
        status, reasons = "needs_review", ["source or control change awaiting impact review"]
    elif not results:
        status, reasons = "needs_review", ["no approved rule components defined"]
    elif outcomes["failed"]:
        status, reasons = "unsatisfied", ["evidenced failure of an approved rule"]
    elif outcomes["ambiguous"]:
        status, reasons = "needs_review", ["ambiguous or conflicting evidence"]
    elif outcomes["missing"] and outcomes["supported"]:
        status, reasons = "partially_satisfied", ["some components lack current sufficient evidence"]
    elif outcomes["missing"]:
        status, reasons = "insufficient_evidence", ["no component has current sufficient evidence"]
    else:
        status, reasons = "satisfied", ["all components supported by current accepted evidence"]
    for r in results:
        reasons += [f"{r.component_id}: {r.outcome}: {x}" for x in r.reasons]
    lapses = [ev.valid_until for c in req.components for ev in c.evidence
              if ev.valid_until is not None and ev.valid_until > now]
    lapses += [ev.observed_at + c.max_evidence_age for c in req.components for ev in c.evidence
               if c.max_evidence_age is not None and ev.observed_at + c.max_evidence_age > now]
    return Assessment(req.requirement_id, status, tuple(reasons), results, tuple(sorted(outcomes.items())),
                      tuple(sorted({f"{c.rule.rule_id}@{c.rule.version}" for c in req.components})),
                      now, _digest(req), min(lapses, default=None))


def drift_reasons(previous: Assessment, req: Requirement, now: datetime) -> list[str]:
    """Why `previous` is no longer the current conclusion; empty list means still current."""
    _aware(now, "now")
    if previous.requirement_id != req.requirement_id:
        raise ValueError("assessment belongs to another requirement")
    reasons = []
    if previous.inputs_digest != _digest(req):
        reasons.append("requirement, rule, applicability or evidence inputs changed")
    if previous.current_until is not None and now >= previous.current_until:
        reasons.append(f"evidence currency lapsed at {previous.current_until.isoformat()}")
    return reasons


def impact(nodes: dict, links, changed) -> dict:
    """Blast radius: {impacted_id: path} following upstream->downstream dependency links.

    `nodes` maps id -> workspace_id; every link must stay inside one workspace.
    """
    graph = {}
    for up, down in links:
        if up not in nodes or down not in nodes:
            raise ValueError(f"link references unknown node {up}->{down}")
        if nodes[up] != nodes[down]:
            raise ValueError(f"cross-workspace link {up}->{down}")
        graph.setdefault(up, []).append(down)
    changed = set(changed)
    paths, queue = {}, deque((c, (c,)) for c in changed)
    while queue:
        node, path = queue.popleft()
        for nxt in graph.get(node, ()):
            if nxt not in paths and nxt not in changed:
                paths[nxt] = path + (nxt,)
                queue.append((nxt, paths[nxt]))
    return paths
