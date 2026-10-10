"""Bounded client proposals; acceptance and source hashes are server-owned."""
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    jurisdiction: str = Field(min_length=1, max_length=100)
    authority_tier: Literal["unverified", "primary", "secondary"] = "unverified"
    owner_id: UUID


class DocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_id: UUID
    title: str = Field(min_length=1, max_length=250)


class VersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    regulatory_document_id: UUID
    document_id: UUID
    version_id: UUID
    extraction_id: UUID
    published_at: date | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    amends_id: UUID | None = None
    supersedes_id: UUID | None = None

    @model_validator(mode="after")
    def interval(self):
        if self.effective_from and self.effective_until and self.effective_until <= self.effective_from:
            raise ValueError("effective_until must be after effective_from")
        return self


class ChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_version_id: UUID
    to_version_id: UUID


class ApplicabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    regulatory_version_id: UUID
    state: Literal["applicable", "not_applicable"]
    jurisdiction: str = Field(min_length=1, max_length=100)
    entity: str = Field(min_length=1, max_length=200)
    product: str = Field(min_length=1, max_length=200)
    business_unit: str = Field(min_length=1, max_length=200)
    effective_on: date
    rationale: str = Field(min_length=1, max_length=2000)


class WatchlistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: UUID
    max_age_days: int = Field(ge=1, le=3650)
