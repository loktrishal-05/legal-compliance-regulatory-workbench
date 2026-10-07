"""Bounded native parser IPC and public provenance; no client-owned authority fields."""
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LineLocator(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["line"]
    line: int = Field(gt=0)
    offset_unit: Literal["unicode_codepoint"]


class ParagraphLocator(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["paragraph"]
    part: str = Field(max_length=200, pattern=r"^word/[a-zA-Z0-9_.-]+\.xml$")
    paragraph: int = Field(gt=0)
    offset_unit: Literal["unicode_codepoint"]


class PageLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    kind: Literal["page_region"]
    page: int = Field(gt=0, le=100)
    bbox: list[float] = Field(min_length=4, max_length=4)
    origin: Literal["TOPLEFT"]
    offset_unit: Literal["unicode_codepoint"]


Locator = Annotated[LineLocator | ParagraphLocator | PageLocator, Field(discriminator="kind")]


class NativeSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    locator: Locator


class NativeArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=2 * 1024 * 1024)
    spans: list[NativeSpan] = Field(max_length=2000)
    warnings: list[str] = Field(max_length=20)
    status: Literal["ready", "needs_verification"]
    extractor: str = Field(max_length=100)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    extraction_id: UUID
    status: Literal["ready", "needs_verification"]
    span_ids: list[UUID]
    warnings: list[str]


class SourceSpanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    span_id: UUID
    extraction_id: UUID
    document_id: UUID
    version_id: UUID
    source_sha256: str
    artifact_sha256: str
    quote: str
    start: int
    end: int
    locator: Locator
    status: Literal["ready", "needs_verification"]
    warnings: list[str]
