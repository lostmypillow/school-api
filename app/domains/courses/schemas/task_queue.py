from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskQueueResponse(BaseModel):
    """Response schema returned when a background task is successfully enqueued."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        ...,
        description="Status of the task submission",
        examples=["Queued"],
    )
    job_id: Optional[str] = Field(
        default=None,
        description="Unique RQ job identifier for polling status",
        examples=["9c9418ad-e51a-47db-b6f3-e94523b349b1"],
    )
