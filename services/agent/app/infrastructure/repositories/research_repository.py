"""Research repository — handles all database operations for research tasks."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.opportunity.models import AccountCandidate, Opportunity
from ...domain.research.models import ResearchTask, ResearchTaskStatus
from ..database.models import (
    AccountCandidateORM,
    BuyerScoreORM,
    EvidenceORM,
    ResearchTaskORM,
    SearchQueryORM,
)


class ResearchRepository:
    """Repository for research task persistence.

    Handles conversion between domain models and ORM models.
    All database access goes through this class.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── ResearchTask ─────────────────────────────────────────────────────
    async def create_task(self, task: ResearchTask) -> ResearchTask:
        """Persist a new research task."""
        orm = ResearchTaskORM(
            id=task.id,
            goal=task.goal,
            status=task.status.value,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        self._session.add(orm)
        await self._session.flush()
        return task

    async def get_task(self, task_id: str) -> ResearchTask | None:
        """Retrieve a research task by ID."""
        result = await self._session.execute(
            select(ResearchTaskORM).where(ResearchTaskORM.id == task_id)
        )
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return ResearchTask(
            id=orm.id,
            goal=orm.goal,
            status=ResearchTaskStatus(orm.status),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            error_message=orm.error_message,
        )

    async def update_task_status(
        self,
        task_id: str,
        status: ResearchTaskStatus,
        error_message: str | None = None,
    ) -> None:
        """Update task status and timestamp."""
        result = await self._session.execute(
            select(ResearchTaskORM).where(ResearchTaskORM.id == task_id)
        )
        orm = result.scalar_one_or_none()
        if orm:
            orm.status = status.value
            orm.updated_at = datetime.utcnow()
            if error_message:
                orm.error_message = error_message
            await self._session.flush()

    # ── SearchQuery ──────────────────────────────────────────────────────
    async def save_queries(self, queries: list) -> None:
        """Persist search queries."""
        for query in queries:
            orm = SearchQueryORM(
                id=query.id,
                research_task_id=query.research_task_id,
                query=query.query,
                query_type=query.query_type.value,
                reason=query.reason,
                status=query.status,
            )
            self._session.add(orm)
        await self._session.flush()

    # ── AccountCandidate ─────────────────────────────────────────────────
    async def save_candidates(
        self,
        task_id: str,
        candidates: list[AccountCandidate],
    ) -> None:
        """Persist account candidates."""
        for candidate in candidates:
            orm = AccountCandidateORM(
                id=candidate.id,
                research_task_id=task_id,
                platform=candidate.platform,
                account_name=candidate.account_name,
                profile_url=candidate.profile_url,
                bio=candidate.bio,
                follower_count=candidate.follower_count,
                source_queries=candidate.source_queries,
                raw_data=candidate.raw_data,
            )
            self._session.add(orm)
        await self._session.flush()

    # ── BuyerScore & Evidence ────────────────────────────────────────────
    async def save_scores_and_evidence(
        self,
        task_id: str,
        opportunities: list[Opportunity],
    ) -> None:
        """Persist buyer scores and evidence."""
        for opp in opportunities:
            score = opp.buyer_score
            candidate = opp.candidate

            score_orm = BuyerScoreORM(
                id=score.id,
                research_task_id=task_id,
                candidate_id=candidate.id,
                account_name=candidate.account_name,
                profile_url=candidate.profile_url,
                icp_fit=score.icp_fit,
                pain_intensity=score.pain_intensity,
                usage_frequency=score.usage_frequency,
                existing_spend=score.existing_spend,
                customer_value=score.customer_value,
                buy_vs_build=score.buy_vs_build,
                reachability=score.reachability,
                total=score.total,
                level=opp.level.value,
                score_reason=score.score_reason,
                risk=score.risk,
                confidence=score.confidence,
                value_hypothesis=opp.value_hypothesis,
                recommended_action=opp.recommended_action,
            )
            self._session.add(score_orm)

            for evidence in opp.evidence:
                evidence_orm = EvidenceORM(
                    id=evidence.id,
                    research_task_id=task_id,
                    candidate_id=candidate.id,
                    evidence_type=evidence.evidence_type.value,
                    evidence_text=evidence.evidence_text,
                    source_url=evidence.source_url,
                    confidence=evidence.confidence,
                )
                self._session.add(evidence_orm)

        await self._session.flush()

    # ── Query Results ────────────────────────────────────────────────────
    async def get_opportunities(
        self,
        task_id: str,
    ) -> list[dict]:
        """Get opportunities for a task, sorted by total score descending."""
        result = await self._session.execute(
            select(BuyerScoreORM)
            .where(BuyerScoreORM.research_task_id == task_id)
            .order_by(BuyerScoreORM.total.desc())
        )
        rows = result.scalars().all()

        results: list[dict] = []
        for row in rows:
            # Get evidence for this candidate
            ev_result = await self._session.execute(
                select(EvidenceORM).where(
                    EvidenceORM.candidate_id == row.candidate_id
                )
            )
            evidence_rows = ev_result.scalars().all()

            results.append(
                {
                    "id": row.id,
                    "candidate_id": row.candidate_id,
                    "account_name": row.account_name,
                    "profile_url": row.profile_url,
                    "buyer_score": {
                        "icp_fit": row.icp_fit,
                        "pain_intensity": row.pain_intensity,
                        "usage_frequency": row.usage_frequency,
                        "existing_spend": row.existing_spend,
                        "customer_value": row.customer_value,
                        "buy_vs_build": row.buy_vs_build,
                        "reachability": row.reachability,
                        "total": row.total,
                        "score_reason": row.score_reason,
                        "risk": row.risk,
                        "confidence": row.confidence,
                    },
                    "level": row.level,
                    "value_hypothesis": row.value_hypothesis,
                    "recommended_action": row.recommended_action,
                    "evidence": [
                        {
                            "evidence_type": ev.evidence_type,
                            "evidence_text": ev.evidence_text,
                            "source_url": ev.source_url,
                            "confidence": ev.confidence,
                        }
                        for ev in evidence_rows
                    ],
                }
            )

        return results

    async def get_task_stats(self, task_id: str) -> dict:
        """Get pipeline statistics for a task."""
        # Count candidates
        cand_result = await self._session.execute(
            select(AccountCandidateORM).where(
                AccountCandidateORM.research_task_id == task_id
            )
        )
        candidate_count = len(cand_result.scalars().all())

        # Count scores
        score_result = await self._session.execute(
            select(BuyerScoreORM).where(
                BuyerScoreORM.research_task_id == task_id
            )
        )
        score_count = len(score_result.scalars().all())

        # Count queries
        query_result = await self._session.execute(
            select(SearchQueryORM).where(
                SearchQueryORM.research_task_id == task_id
            )
        )
        queries = query_result.scalars().all()
        query_count = len(queries)

        return {
            "query_count": query_count,
            "candidate_count": candidate_count,
            "scored_count": score_count,
            "top_score": max(
                (s.total for s in score_result.scalars().all()),
                default=0,
            ),
        }
