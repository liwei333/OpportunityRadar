"""API request schemas."""

from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    """Request to create a new research task."""

    goal: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Natural language research goal",
        examples=["帮我寻找最可能购买 OpportunityRadar 的客户"],
    )
