from typing import Optional, Any

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


class JobStatusResponse(BaseModel):
    """Response schema for background task execution status."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(
        ...,
        description="Unique RQ job identifier",
        examples=["9c9418ad-e51a-47db-b6f3-e94523b349b1"],
    )
    status: str = Field(
        ...,
        description="Current state of the job: queued, started, finished, failed, deferred, not_found",
        examples=["finished"],
    )
    result: Optional[Any] = Field(
        default=None,
        description="Result payload returned by the completed job, if available",
    )
