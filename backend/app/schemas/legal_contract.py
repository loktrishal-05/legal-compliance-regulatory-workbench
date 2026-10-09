"""Strict bounded Agent B commands. Identity/review status/profile are server-owned."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="after")
    @classmethod
    def safe_text(cls, value):
        if isinstance(value, str) and (not value.strip() or "\0" in value):
            raise ValueError("nonempty_text_required")
        return value


class ContractRequest(Command):
    document_id: UUID
    version_id: UUID
    title: str = Field(min_length=1, max_length=200)


class ContractVersionRequest(Command):
    document_id: UUID
    version_id: UUID


class AnalysisRequest(Command):
    playbook_id: UUID | None = None


class CollisionRequest(Command):
    left_contract_id: UUID
    left_version_id: UUID
    right_contract_id: UUID
    right_version_id: UUID


class PlaybookRuleRequest(Command):
    clause_type: str = Field(min_length=1, max_length=40)
    kind: Literal["required_clause", "forbidden_text"]
    label: str = Field(min_length=1, max_length=300)
    pattern: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def required_pattern(self):
        if self.kind == "forbidden_text" and not self.pattern:
            raise ValueError("forbidden_text_requires_pattern")
        from app.services.legal_contract_analysis import LABELS
        if self.clause_type not in set(LABELS.values()) | {"other"}:
            raise ValueError("unsupported_clause_type")
        return self


class PlaybookRequest(Command):
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=60)
    legal_basis: str = Field(min_length=1, max_length=2000)
    jurisdiction: str = Field(min_length=1, max_length=200)
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    rules: list[PlaybookRuleRequest] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def interval(self):
        if any(v and v.tzinfo is None for v in (self.effective_from, self.effective_until)):
            raise ValueError("timezone_required")
        if self.effective_until and (not self.effective_from or self.effective_until <= self.effective_from):
            raise ValueError("invalid_effective_interval")
        return self


class SourceRequest(Command):
    document_id: UUID
    version_id: UUID


class SummaryRequest(Command):
    sources: list[SourceRequest] = Field(min_length=1, max_length=20)
    profile: Literal["executive", "detailed", "clause", "risk", "obligation", "action", "change"] = "executive"
    audience: Literal["legal", "compliance", "business", "executive", "auditor"] = "legal"


class QuestionRequest(Command):
    question: str = Field(min_length=1, max_length=2000)
    matter_id: UUID | None = None
    conversation_id: UUID | None = None


class ConversationRequest(Command):
    matter_id: UUID | None = None


class GatewayCitation(Command):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    span_id: UUID
    quote: str = Field(min_length=1, max_length=64000)


class GatewayStatement(Command):
    text: str = Field(min_length=1, max_length=64000)
    category: Literal["source_fact", "observation", "interpretation", "recommendation"]
    citations: list[GatewayCitation] = Field(min_length=1, max_length=20)


class GatewayOutput(Command):
    statements: list[GatewayStatement] = Field(min_length=1, max_length=100)
