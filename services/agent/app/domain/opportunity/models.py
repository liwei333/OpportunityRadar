"""Domain models for candidates and opportunities."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from ..scoring.models import BuyerScore


class OpportunityLevel(enum.StrEnum):
    """Buyer score classification level."""

    S = "S"
    A = "A"
    B = "B"
    C = "C"


class AccountCandidate(BaseModel):
    """A candidate account identified during collection."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str
    account_name: str
    profile_url: str = ""
    bio: str = ""
    follower_count: int | None = None
    source_queries: list[str] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)


class ContentCandidate(BaseModel):
    """A piece of content identified during collection."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str
    account_id: str = ""
    account_name: str = ""
    content_url: str = ""
    title: str = ""
    description: str = ""
    published_at: datetime | None = None
    engagement: dict = Field(default_factory=dict)
    source_query: str = ""
    raw_data: dict = Field(default_factory=dict)


def classify_level(total_score: int) -> OpportunityLevel:
    """Classify a total buyer score into a level."""
    if total_score >= 90:
        return OpportunityLevel.S
    if total_score >= 80:
        return OpportunityLevel.A
    if total_score >= 65:
        return OpportunityLevel.B
    return OpportunityLevel.C


class Opportunity(BaseModel):
    """Final recommended prospect with scoring and evidence."""

    candidate: AccountCandidate
    buyer_score: BuyerScore
    level: OpportunityLevel
    evidence: list = Field(default_factory=list)
    value_hypothesis: str = ""
    recommended_action: str = ""

    @classmethod
    def from_score(
        cls,
        candidate: AccountCandidate,
        buyer_score: BuyerScore,
        evidence: list | None = None,
        value_hypothesis: str = "",
        recommended_action: str = "",
    ) -> Opportunity:
        """Create an Opportunity from a BuyerScore, auto-classifying level."""
        level = classify_level(buyer_score.total)
        return cls(
            candidate=candidate,
            buyer_score=buyer_score,
            level=level,
            evidence=evidence if evidence is not None else [],
            value_hypothesis=value_hypothesis,
            recommended_action=recommended_action,
        )
