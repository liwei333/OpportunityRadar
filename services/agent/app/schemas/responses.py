"""API response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    service: str = "opportunity-radar-agent"
    version: str = "0.1.0"


class CreateTaskResponse(BaseModel):
    """Response after creating a research task."""

    task_id: str
    status: str


class TaskResponse(BaseModel):
    """Full research task response."""

    id: str
    goal: str
    status: str
    created_at: str
    updated_at: str
    error_message: str | None = None
    stats: dict | None = None


class TaskRunResponse(BaseModel):
    """Response after running a research task."""

    task_id: str
    status: str
    queries_generated: int = 0
    candidates_collected: int = 0
    candidates_after_dedup: int = 0
    opportunities_found: int = 0
    top_score: int = 0


class EvidenceSchema(BaseModel):
    """Evidence item in an opportunity."""

    evidence_type: str
    evidence_text: str
    source_url: str = ""
    confidence: float = 0.8


class BuyerScoreSchema(BaseModel):
    """Buyer score details."""

    icp_fit: int = 0
    pain_intensity: int = 0
    usage_frequency: int = 0
    existing_spend: int = 0
    customer_value: int = 0
    buy_vs_build: int = 0
    reachability: int = 0
    total: int = 0
    score_reason: str = ""
    risk: str = ""
    confidence: float = 0.8


class OpportunityResponse(BaseModel):
    """A single opportunity in the results."""

    id: str
    candidate_id: str
    account_name: str
    profile_url: str = ""
    level: str
    total_score: int
    buyer_score: BuyerScoreSchema
    value_hypothesis: str = ""
    recommended_action: str = ""
    evidence: list[EvidenceSchema] = Field(default_factory=list)


class OpportunitiesListResponse(BaseModel):
    """List of opportunities for a task."""

    task_id: str
    total: int
    opportunities: list[OpportunityResponse]


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
