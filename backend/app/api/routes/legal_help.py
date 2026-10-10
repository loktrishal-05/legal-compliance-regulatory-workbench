"""Session/terms-protected public-guide help only; never accepts tenant or model routing fields."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.api.deps import get_current_user
from app.services.legal_help import HelpRateLimited, default_help_service

router = APIRouter(prefix="/v1/help", tags=["application help"])


class HelpQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=1200)

    @field_validator("question")
    @classmethod
    def nonempty(cls, value):
        if not value.strip() or "\0" in value:
            raise ValueError("invalid_help_question")
        return value


@router.post("/chat")
def chat(payload: HelpQuestion, request: Request, user=Depends(get_current_user)):
    service = getattr(request.app.state, "legal_help_service", None)
    if service is None:
        service = request.app.state.legal_help_service = default_help_service()
    try:
        return service.answer(payload.question, user_id=user.id)
    except HelpRateLimited:
        raise HTTPException(429, detail={"code": "help_rate_limited"}, headers={"Retry-After": "60"}) from None
