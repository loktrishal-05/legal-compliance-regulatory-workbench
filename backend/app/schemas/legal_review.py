"""Bounded review inputs; the requester/reviewer always come from the verified session."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _substantive(value):
    if not value.strip() or "\0" in value:
        raise ValueError("Nonblank text without NUL is required")
    return value


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_type: str = Field(min_length=1, max_length=60, pattern=r"^[a-z_]+$")
    target_id: UUID
    target_revision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=200)


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject", "request_changes", "escalate"]
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def substantive(cls, value):
        return _substantive(value)


class ReviewDecisionResponse(BaseModel):
    decision_id: UUID
    reviewer_id: UUID
    decision: str
    rationale: str
    created_at: datetime | None


class ReviewResponse(BaseModel):
    review_id: UUID
    target_type: str
    target_id: UUID
    target_revision_sha256: str
    requester_id: UUID
    status: str
    created_at: datetime | None
    decisions: list[ReviewDecisionResponse]
