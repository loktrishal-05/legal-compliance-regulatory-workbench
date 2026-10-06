"""Bounded legal metadata responses; storage paths and source bodies are private."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkspaceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    organization_id: UUID
    name: str
    role: Literal["analyst", "legal_reviewer", "compliance_reviewer", "business_owner",
                  "auditor", "workspace_admin", "viewer"]


class LegalDocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    workspace_id: UUID
    matter_id: UUID | None
    filename: str
    document_type: str
    classification: Literal["public", "internal", "confidential", "restricted"]
    ingestion_status: str
    legal_hold: bool
