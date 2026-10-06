"""Explicit, version-bound acceptance; historical receipts stay in the audit chain."""
from fastapi import HTTPException

from app.core.config import settings
from app.services import accounts

ACKNOWLEDGEMENTS = {
    "advisory_only": "I understand AI outputs are advisory only and must be independently verified.",
    "no_equipment_control": "I understand the AI cannot control plant equipment.",
    "no_bypass": "I will not attempt to bypass safety, access or audit controls.",
    "audit_logging": "I understand my application activity is recorded in the tamper-evident audit log.",
}


def current(user):
    accepted = user.terms_version == settings.current_terms_version and user.terms_accepted_at is not None
    return {"version": settings.current_terms_version, "requires_acceptance": not accepted,
            "accepted_at": accounts.utc(user.terms_accepted_at) if accepted else None,
            "acknowledgements": [{"id": key, "text": text} for key, text in ACKNOWLEDGEMENTS.items()]}


def accept(db, user, payload, request_host):
    if payload.version != settings.current_terms_version:
        raise HTTPException(409, detail={"code": "terms_version_changed", "version": settings.current_terms_version})
    try:
        # Serialize duplicate clicks/retries for this account; never replace the first receipt.
        db.refresh(user, with_for_update=True)
        if not user.is_active or user.signup_pending:
            raise HTTPException(401, "Authentication required.")
        if current(user)["requires_acceptance"]:
            user.terms_version = payload.version
            user.terms_accepted_at = accounts.now()
            # Peer information only: never trust Host/X-Forwarded-For or perform reverse DNS.
            user.terms_request_host = request_host[:255] if request_host else None
            accounts.event(db, "TERMS_ACCEPTED", user, version=payload.version,
                accepted_at=user.terms_accepted_at, request_host=user.terms_request_host,
                acknowledgements=payload.acknowledgements.model_dump())
        db.commit()
        return {"version": user.terms_version, "accepted_at": accounts.utc(user.terms_accepted_at)}
    except Exception:
        db.rollback()
        raise
