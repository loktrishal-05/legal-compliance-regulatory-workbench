"""Job, region transcription and projection shapes; actor and scope always come from the session."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Literal["extract", "ocr"] = "extract"
    idempotency_key: str = Field(min_length=1, max_length=200)


class JobResponse(BaseModel):
    job_id: UUID
    document_id: UUID
    version_id: UUID
    operation: str
    profile: str
    state: str
    attempts: int
    max_attempts: int
    failure_code: str | None
    extraction_id: UUID | None
    next_retry_at: datetime | None
    created_at: datetime | None
    finished_at: datetime | None


class RegionTranscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    extraction_id: UUID
    page: int = Field(ge=1, le=10000)
    bbox: list[float] = Field(min_length=4, max_length=4)
    text: str = Field(min_length=1, max_length=64000)
    rationale: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @field_validator("text", "rationale")
    @classmethod
    def substantive(cls, value):
        if not value.strip() or "\0" in value:
            raise ValueError("Nonblank text without NUL is required")
        return value


class RegionTranscriptionResponse(BaseModel):
    transcription_id: UUID
    extraction_id: UUID
    page: int
    bbox: list[float]
    text: str
    transcription_sha256: str
    review_target_type: str = "region_transcription"
