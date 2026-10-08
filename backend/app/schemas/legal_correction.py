"""Bounded transcription inputs; no client-owned review/source authority."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.legal_extraction import Locator


class CorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: UUID
    expected_quote_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    corrected_text: str = Field(min_length=1, max_length=64000)
    rationale: str = Field(min_length=1, max_length=2000)
    parent_correction_id: UUID | None = None

    @field_validator("corrected_text", "rationale")
    @classmethod
    def substantive(cls, value):
        if not value.strip() or "\0" in value:
            raise ValueError("Nonblank text without NUL is required")
        return value


class CorrectionDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["approved", "rejected"]
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def substantive(cls, value):
        return CorrectionRequest.substantive(value)


class CorrectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    correction_id: UUID
    correction_sha256: str
    parent_correction_id: UUID | None
    span_id: UUID
    extraction_id: UUID
    document_id: UUID
    version_id: UUID
    source_sha256: str
    original_quote: str
    corrected_text: str
    rationale: str
    locator: Locator
    actor_id: UUID
    outcome: Literal["proposed", "approved", "rejected"]
    reviewer_id: UUID | None
    review_rationale: str | None
