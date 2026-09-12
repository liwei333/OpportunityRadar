"""SQLAlchemy ORM models.

These are persistence models separate from domain models.
Domain models (Pydantic) are used in business logic;
ORM models are used for database storage.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ResearchTaskORM(Base):
    """ORM model for research_tasks table."""

    __tablename__ = "research_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class SearchQueryORM(Base):
    """ORM model for search_queries table."""

    __tablename__ = "search_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    research_task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    query_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="PENDING")


class AccountCandidateORM(Base):
    """ORM model for account_candidates table."""

    __tablename__ = "account_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    research_task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(500), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    follower_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_queries: Mapped[list] = mapped_column(JSON, default=list)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)


class BuyerScoreORM(Base):
    """ORM model for buyer_scores table."""

    __tablename__ = "buyer_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    research_task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    candidate_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(500), default="")
    icp_fit: Mapped[int] = mapped_column(Integer, default=0)
    pain_intensity: Mapped[int] = mapped_column(Integer, default=0)
    usage_frequency: Mapped[int] = mapped_column(Integer, default=0)
    existing_spend: Mapped[int] = mapped_column(Integer, default=0)
    customer_value: Mapped[int] = mapped_column(Integer, default=0)
    buy_vs_build: Mapped[int] = mapped_column(Integer, default=0)
    reachability: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(1), nullable=False, default="C")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    risk: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    value_hypothesis: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(Text, default="")


class EvidenceORM(Base):
    """ORM model for evidence table."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    research_task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    candidate_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
