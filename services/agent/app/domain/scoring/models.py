"""Domain models for buyer scoring."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class BuyerScore(BaseModel):
    """V0 seven-dimension buyer score model.

    Total is out of 100 points:
    - icp_fit: 25
    - pain_intensity: 20
    - usage_frequency: 15
    - existing_spend: 15
    - customer_value: 10
    - buy_vs_build: 10
    - reachability: 5
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
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
