"""Research service — orchestrates the full research pipeline.

Pipeline:
    Planner → Collector → Normalizer → Deduplicator →
    Buyer Scoring → Ranking → Database
"""

import logging

from ..core.exceptions import (
    ResearchTaskNotFoundError,
    ResearchTaskStateError,
)
from ..domain.opportunity.models import AccountCandidate
from ..domain.research.models import ResearchTask, ResearchTaskStatus
from ..domain.scoring.models import BuyerScore
from ..infrastructure.database import AsyncSessionLocal, init_db
from ..infrastructure.repositories.research_repository import ResearchRepository
from .collector.mock_collector import MockCollector
from .intelligence.buyer_scoring import BuyerScoringService
from .normalizer import AccountDeduplicator, DataCleaner, URLNormalizer
from .planner.mock_planner import MockPlanner
from .ranking.ranker import OpportunityRanker

logger = logging.getLogger(__name__)


class ResearchService:
    """Orchestrates research task execution.

    Coordinates all pipeline stages from planning to ranking.
    Maintains clean separation between facts (collection) and
    intelligence (scoring).
    """

    def __init__(self) -> None:
        self._planner = MockPlanner()
        self._collector = MockCollector()
        self._scoring = BuyerScoringService()
        self._ranker = OpportunityRanker()
        self._url_normalizer = URLNormalizer()
        self._cleaner = DataCleaner()
        self._account_dedup = AccountDeduplicator()

    async def create_task(self, goal: str) -> ResearchTask:
        """Create a new research task.

        Args:
            goal: Natural language research goal.

        Returns:
            The created ResearchTask.
        """
        await init_db()
        task = ResearchTask(goal=goal)

        async with AsyncSessionLocal() as session:
            repo = ResearchRepository(session)
            await repo.create_task(task)
            await session.commit()

        logger.info("Created research task: %s", task.id)
        return task

    async def run_task(self, task_id: str) -> dict:
        """Execute the full research pipeline for a task.

        Args:
            task_id: The task to execute.

        Returns:
            Pipeline results summary.
        """
        await init_db()

        async with AsyncSessionLocal() as session:
            repo = ResearchRepository(session)

            # Load task
            task = await repo.get_task(task_id)
            if not task:
                raise ResearchTaskNotFoundError(f"Task not found: {task_id}")

            if task.status not in (ResearchTaskStatus.PENDING, ResearchTaskStatus.FAILED):
                raise ResearchTaskStateError(
                    f"Task {task_id} is in state {task.status.value}, cannot run"
                )

            try:
                # Step 1: Planning
                task.mark_status(ResearchTaskStatus.PLANNING)
                await repo.update_task_status(task_id, ResearchTaskStatus.PLANNING)
                await session.commit()

                queries = self._planner.plan(task)
                await repo.save_queries(queries)
                logger.info("Planning complete: %d queries", len(queries))

                # Step 2: Collecting
                task.mark_status(ResearchTaskStatus.COLLECTING)
                await repo.update_task_status(task_id, ResearchTaskStatus.COLLECTING)
                await session.commit()

                accounts, content = await self._collector.collect(task, queries)
                logger.info(
                    "Collection complete: %d accounts, %d content",
                    len(accounts),
                    len(content),
                )

                # Step 3: Normalizing & Deduplicating
                task.mark_status(ResearchTaskStatus.FILTERING)
                await repo.update_task_status(task_id, ResearchTaskStatus.FILTERING)
                await session.commit()

                accounts = self._normalize_and_clean(accounts)
                deduped_accounts = self._account_dedup.deduplicate(accounts)
                logger.info(
                    "After dedup: %d accounts (from %d)",
                    len(deduped_accounts),
                    len(accounts),
                )

                # Save candidates
                await repo.save_candidates(task_id, deduped_accounts)
                await session.commit()

                # Step 4: Scoring
                task.mark_status(ResearchTaskStatus.SCORING)
                await repo.update_task_status(task_id, ResearchTaskStatus.SCORING)
                await session.commit()

                scored: list[tuple[AccountCandidate, BuyerScore]] = []
                for candidate in deduped_accounts:
                    score = self._scoring.score(candidate)
                    scored.append((candidate, score))

                # Step 5: Ranking
                opportunities = self._ranker.rank(scored, top_n=20)

                # Generate evidence for each opportunity
                for opp in opportunities:
                    opp.evidence = self._scoring.generate_evidence(opp.candidate)

                # Save scores and evidence
                await repo.save_scores_and_evidence(task_id, opportunities)
                await session.commit()

                # Complete
                task.mark_status(ResearchTaskStatus.COMPLETED)
                await repo.update_task_status(task_id, ResearchTaskStatus.COMPLETED)
                await session.commit()

                return {
                    "task_id": task_id,
                    "status": "COMPLETED",
                    "queries_generated": len(queries),
                    "candidates_collected": len(accounts),
                    "candidates_after_dedup": len(deduped_accounts),
                    "opportunities_found": len(opportunities),
                    "top_score": opportunities[0].buyer_score.total if opportunities else 0,
                }

            except Exception as e:
                logger.exception("Task execution failed")
                task.mark_failed(str(e))
                await repo.update_task_status(
                    task_id, ResearchTaskStatus.FAILED, error_message=str(e)
                )
                await session.commit()
                raise

    async def get_task(self, task_id: str) -> ResearchTask:
        """Get a research task by ID."""
        async with AsyncSessionLocal() as session:
            repo = ResearchRepository(session)
            task = await repo.get_task(task_id)
            if not task:
                raise ResearchTaskNotFoundError(f"Task not found: {task_id}")
            return task

    async def get_opportunities(self, task_id: str) -> list[dict]:
        """Get ranked opportunities for a task."""
        async with AsyncSessionLocal() as session:
            repo = ResearchRepository(session)
            return await repo.get_opportunities(task_id)

    def _normalize_and_clean(
        self,
        candidates: list[AccountCandidate],
    ) -> list[AccountCandidate]:
        """Normalize and clean candidate data."""
        cleaned: list[AccountCandidate] = []
        for candidate in candidates:
            candidate.account_name = self._cleaner.clean_account_name(
                candidate.account_name
            )
            candidate.bio = self._cleaner.clean_bio(candidate.bio)
            candidate.profile_url = self._url_normalizer.normalize(
                candidate.profile_url
            )
            cleaned.append(candidate)
        return cleaned
