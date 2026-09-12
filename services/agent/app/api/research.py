"""Research task API endpoints."""

from fastapi import APIRouter, HTTPException, status

from ..application.research_service import ResearchService
from ..core.exceptions import (
    ResearchTaskNotFoundError,
    ResearchTaskStateError,
)
from ..schemas.requests import CreateTaskRequest
from ..schemas.responses import (
    BuyerScoreSchema,
    CreateTaskResponse,
    EvidenceSchema,
    OpportunitiesListResponse,
    OpportunityResponse,
    TaskResponse,
    TaskRunResponse,
)

router = APIRouter(prefix="/research", tags=["research"])

# Singleton service instance
_service = ResearchService()


@router.post(
    "/tasks",
    response_model=CreateTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(request: CreateTaskRequest) -> CreateTaskResponse:
    """Create a new research task.

    Accepts a natural language goal and creates a task for processing.
    """
    task = await _service.create_task(goal=request.goal)
    return CreateTaskResponse(task_id=task.id, status=task.status.value)


@router.post(
    "/tasks/{task_id}/run",
    response_model=TaskRunResponse,
)
async def run_task(task_id: str) -> TaskRunResponse:
    """Execute the full research pipeline for a task.

    Runs: Planner → Collector → Normalizer → Deduplicator →
          Buyer Scoring → Ranking → Database
    """
    try:
        result = await _service.run_task(task_id)
        return TaskRunResponse(**result)
    except ResearchTaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        ) from None
    except ResearchTaskStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}",
        ) from e


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
async def get_task(task_id: str) -> TaskResponse:
    """Get research task details and status."""
    try:
        task = await _service.get_task(task_id)
        return TaskResponse(
            id=task.id,
            goal=task.goal,
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            error_message=task.error_message,
        )
    except ResearchTaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        ) from None


@router.get(
    "/tasks/{task_id}/opportunities",
    response_model=OpportunitiesListResponse,
)
async def get_opportunities(task_id: str) -> OpportunitiesListResponse:
    """Get ranked opportunities for a task, sorted by buyer score descending."""
    try:
        # Verify task exists
        await _service.get_task(task_id)
    except ResearchTaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        ) from None

    raw_opportunities = await _service.get_opportunities(task_id)

    opportunities: list[OpportunityResponse] = []
    for raw in raw_opportunities:
        buyer_score = raw["buyer_score"]
        opportunities.append(
            OpportunityResponse(
                id=raw["id"],
                candidate_id=raw["candidate_id"],
                account_name=raw["account_name"],
                profile_url=raw.get("profile_url", ""),
                level=raw["level"],
                total_score=buyer_score["total"],
                buyer_score=BuyerScoreSchema(**buyer_score),
                value_hypothesis=raw.get("value_hypothesis", ""),
                recommended_action=raw.get("recommended_action", ""),
                evidence=[
                    EvidenceSchema(**ev) for ev in raw.get("evidence", [])
                ],
            )
        )

    return OpportunitiesListResponse(
        task_id=task_id,
        total=len(opportunities),
        opportunities=opportunities,
    )
