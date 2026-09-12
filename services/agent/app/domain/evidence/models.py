"""Domain models for evidence."""

from __future__ import annotations

import enum
import uuid

from pydantic import BaseModel, Field


class EvidenceType(enum.StrEnum):
    """Type of evidence supporting a buyer score judgment."""

    ICP_FIT = "ICP_FIT"
    PAIN_SIGNAL = "PAIN_SIGNAL"
    USAGE_FREQUENCY = "USAGE_FREQUENCY"
    EXISTING_SPEND = "EXISTING_SPEND"
    CUSTOMER_VALUE = "CUSTOMER_VALUE"
    BUY_VS_BUILD = "BUY_VS_BUILD"
    REACHABILITY = "REACHABILITY"
    COMPETITOR = "COMPETITOR"
    BUSINESS_MODEL = "BUSINESS_MODEL"


class Evidence(BaseModel):
    """A piece of evidence supporting a buyer scoring decision."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    evidence_type: EvidenceType
    evidence_text: str
    source_url: str = ""
    confidence: float = 0.8
