"""Bounded deterministic proposals over stored sources; never grants legal authority."""
import re
from uuid import UUID

PROFILE = "legal-contract-deterministic-v1"
SCHEMA = "legal-contract-output-v1"
PROMPT = "no-model-deterministic-v1"
RULES = "synthetic-keyword-rules-v1"
LABELS = {
    "parties": "parties", "definitions": "definition", "definition": "definition",
    "confidentiality": "confidentiality", "term": "term", "notice": "notice",
    "governing law": "governing_law", "services": "services", "payment": "payment",
    "liability": "liability", "termination": "termination", "renewal": "renewal",
    "data protection": "data_protection", "maintenance": "maintenance",
}
HEADING = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?|[A-Z][.)])\s+([A-Za-z][^\n]{0,120})\s*$")
INJECTION = re.compile(r"ignore\s+(?:all\s+)?(?:previous|system)\s+instructions|reveal\s+secrets|mark\s+accepted|system\s*prompt", re.I)
MODAL = re.compile(r"\b([A-Z][\w -]{0,60}?)\s+(shall not|must not|shall|must|may)\s+([^\n]+)")
DEADLINE = re.compile(r"\b(?:within\s+\d+\s+days(?:\s+(?:of|after)\s+[^,.;]+)?|on\s+the\s+first\s+day\s+of\s+each\s+month)", re.I)


def analyze_sources(sources, *, playbook_rules=(), quality="ready"):
    if quality not in {"ready", "needs_verification"} or not 1 <= len(sources) <= 2000:
        raise ValueError("invalid_contract_sources")
    ids = [str(UUID(str(s["span_id"]))) for s in sources]
    if len(set(ids)) != len(ids) or sum(len(s["quote"]) for s in sources) > 2_000_000:
        raise ValueError("invalid_contract_sources")
    clauses, facts, parties, obligations, findings, uncertainties = [], [], [], [], [], []
    if quality != "ready":
        uncertainties.append("extraction_requires_verification")
    current = None
    for item in sources:
        if not isinstance(item["quote"], str) or not item["quote"].strip():
            raise ValueError("empty_contract_span")
        citation = {"span_id": str(item["span_id"]), "quote": item["quote"], "locator": item.get("locator", {})}
        # One stored block can contain several headings; each remains tied to its exact original span.
        for line in item["quote"].splitlines():
            if not line.strip():
                continue
            match = HEADING.match(line)
            if match or current is None:
                title = match.group(1).strip().rstrip(".") if match else "Unclassified text"
                kind = LABELS.get(title.lower(), "other")
                current = {"ordinal": len(clauses)+1, "title": title, "clause_type": kind,
                           "text": "", "citations": []}
                clauses.append(current)
                if kind == "other":
                    uncertainties.append("unclassified_clause")
            current["text"] += ("\n" if current["text"] else "") + line
            if citation not in current["citations"]:
                current["citations"].append(citation)
            if INJECTION.search(line):
                uncertainties.append("untrusted_document_instructions")
                continue
            party = re.search(r"\bbetween\s+(.+?)\s+and\s+(.+?)[.]?$", line, re.I)
            if party and current["clause_type"] == "parties":
                for name in party.groups():
                    parties.append({"name": name.strip().rstrip("."), "citations": [citation]})
            definition = re.search(r'["“]([^"”]+)["”]\s+means\s+(.+)', line)
            if definition:
                facts.append({"kind": "definition", "name": definition.group(1),
                              "value": definition.group(2), "citations": [citation]})
            for date in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", line):
                facts.append({"kind": "date", "name": "source_date", "value": date, "citations": [citation]})
            kind = current["clause_type"]
            if not match and kind in {"term", "renewal", "notice", "governing_law"}:
                facts.append({"kind": kind, "name": kind, "value": line, "citations": [citation]})
            for modal in MODAL.finditer(line):
                actor, verb, action = modal.groups()
                deadline = DEADLINE.search(action)
                conditions = re.findall(r"\b(?:provided|subject to|if|unless|while|except with)\b[^.;]+", action, re.I)
                trigger = re.search(r"\b(?:upon|after)\s+[^,.;]+", action, re.I)
                obligations.append({"obligation_type": "prohibition" if "not" in verb else "right" if verb == "may" else "duty",
                    "actor": actor.strip(), "action": action.rstrip("."), "trigger": trigger.group() if trigger else None,
                    "conditions": conditions, "original_deadline_phrase": deadline.group() if deadline else None,
                    "normalized_deadline": None, "uncertainties": ["actor_identity_requires_review"] +
                        (["deadline_calendar_and_trigger_require_confirmation"] if deadline else ["deadline_not_identified"]),
                    "citations": [citation], "review_required": True})
    covered = set(c["span_id"] for clause in clauses for c in clause["citations"])
    coverage = {"total_spans": len(sources), "covered_spans": len(covered), "quality": quality,
                "inspected_span_ids": ids}
    for rule in playbook_rules:
        present = [c for c in clauses if c["clause_type"] == rule["clause_type"]]
        if rule["kind"] == "required_clause" and not present:
            established = quality == "ready" and len(covered) == len(sources) and not uncertainties
            findings.append({"kind": "missing_clause", "rule_id": rule["rule_id"],
                "rationale": "Expected clause absent from inspected extraction" if established else "absence not established: extraction/coverage requires verification",
                "absence_established": established, "coverage": coverage,
                "citations": [{"span_id": str(s["span_id"]), "quote": s["quote"], "locator": s.get("locator", {})} for s in sources]})
        elif rule["kind"] == "forbidden_text":
            needle = rule.get("pattern", "").casefold()
            if not needle:
                raise ValueError("empty_playbook_pattern")
            for clause in present:
                if needle in clause["text"].casefold():
                    findings.append({"kind": "deviation", "rule_id": rule["rule_id"],
                        "rationale": "Source matches a synthetic playbook deviation rule", "citations": clause["citations"]})
    # ponytail: literal opposite-duty heuristic only; evaluated semantic conflict profiles are a later upgrade.
    for n, left in enumerate(obligations):
        for right in obligations[n+1:]:
            if left["actor"] == right["actor"] and left["action"].casefold() == right["action"].casefold() and (
                    {left["obligation_type"], right["obligation_type"]} == {"duty", "prohibition"}):
                findings.append({"kind": "internal_conflict", "rule_id": None,
                    "rationale": "Literal opposing duties require legal interpretation", "citations": left["citations"] + right["citations"]})
    return {"profile_version": PROFILE, "schema_version": SCHEMA, "prompt_version": PROMPT,
        "rule_version": RULES, "status": "needs_review", "clauses": clauses, "facts": facts,
        "parties": parties, "obligations": obligations, "findings": findings,
        "coverage": coverage, "uncertainties": sorted(set(uncertainties)), "review_required": True}
