from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field


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
