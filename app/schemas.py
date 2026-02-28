"""
schemas.py — Pydantic request/response models for FastAPI endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for POST /chat"""
    session_id: str = Field(
        ...,
        description="Unique session identifier. Use any consistent string (UUID recommended).",
        example="user-abc-123"
    )
    message: str = Field(
        ...,
        description="The user's message.",
        min_length=1,
        max_length=2000,
        example="I've been really stressed about work lately and can't sleep."
    )
    country: Optional[str] = Field(
        default="US",
        description="Country code for crisis resource localization (US, UK, IN, AU, CA, GLOBAL).",
        example="US"
    )
    consent: Optional[bool] = Field(
        default=False,
        description="Whether the user has consented to their emotional history being stored for trend analysis.",
        example=True
    )

    @field_validator("country")
    @classmethod
    def validate_country(cls, v):
        valid = {"US", "UK", "IN", "AU", "CA", "GLOBAL"}
        if v and v.upper() not in valid:
            return "GLOBAL"  # Graceful fallback
        return v.upper() if v else "US"

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty.")
        return v.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class DistressAnalysis(BaseModel):
    """Distress analysis output from the distress_analysis_agent."""
    emotion: str
    risk_level: str
    confidence: float
    routing_path: str


class ChatResponse(BaseModel):
    """Response body for POST /chat"""
    session_id: str
    response: str = Field(description="The agent's final formatted response.")
    analysis: DistressAnalysis = Field(description="Distress analysis metadata.")
    selected_tools: List[str] = Field(default=[], description="Coping tool IDs used (empty for crisis path).")
    trend_warning: Optional[str] = Field(default=None, description="Warning if worsening trend detected.")
    disclaimer: str = Field(
        default="This tool provides emotional support and is not a substitute for professional medical care.",
        description="Standard disclaimer."
    )


class EmotionRecord(BaseModel):
    """A single historical emotion snapshot."""
    timestamp: str
    emotion: str
    risk_level: str
    confidence: float


class EmotionHistoryResponse(BaseModel):
    """Response body for GET /session/{session_id}/history"""
    session_id: str
    emotion_history: List[EmotionRecord]
    trend_warning: Optional[str] = None
    total_records: int


class HealthResponse(BaseModel):
    """Response body for GET /health"""
    status: str
    version: str = "1.0.0"
    llm_provider: str


class SessionDeleteResponse(BaseModel):
    """Response body for DELETE /session/{session_id}"""
    session_id: str
    deleted: bool
    message: str
