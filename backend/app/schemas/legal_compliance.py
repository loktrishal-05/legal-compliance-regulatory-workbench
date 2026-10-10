"""Human proposals only; the server assembles assessment inputs and approval state."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, model_validator


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RequirementRequest(Proposal):
    regulatory_version_id: UUID
    title: str = Field(min_length=1, max_length=250)


class InterpretationRequest(Proposal):
    requirement_id: UUID
    text: str = Field(min_length=1, max_length=12000)
    span_ids: list[UUID] = Field(min_length=1, max_length=100)


class PolicyRequest(Proposal):
    title: str = Field(min_length=1, max_length=250)


class PolicyVersionRequest(Proposal):
    policy_id: UUID
    document_id: UUID
    version_id: UUID


class ControlRequest(Proposal):
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=4000)
    owner_id: UUID


class EvidenceRequest(Proposal):
    title: str = Field(min_length=1, max_length=250)


class EvidenceVersionRequest(Proposal):
    evidence_id: UUID
    document_id: UUID
    version_id: UUID
    observed_at: AwareDatetime
    valid_from: AwareDatetime
    expires_at: AwareDatetime | None = None
    replaces_id: UUID | None = None
    facts: dict[str, JsonValue] = Field(min_length=1, max_length=100)
    span_ids: list[UUID] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def interval(self):
        if self.expires_at and self.expires_at <= self.valid_from:
            raise ValueError("expires_at must be after valid_from")
        return self


class MappingRequest(Proposal):
    requirement_id: UUID
    control_id: UUID
    policy_version_id: UUID | None = None
    evidence_version_id: UUID | None = None


class CheckRequest(Proposal):
    fact: str = Field(min_length=1, max_length=100)
    op: Literal["eq", "ne", "ge", "le", "in"]
    value: JsonValue


class RuleRequest(Proposal):
    control_id: UUID
    interpretation_id: UUID
    checks: list[CheckRequest] = Field(min_length=1, max_length=100)


class AssessmentRequest(Proposal):
    requirement_id: UUID
    applicability_id: UUID


class FindingRequest(Proposal):
    assessment_id: UUID
    text: str = Field(min_length=1, max_length=4000)
