from pydantic import BaseModel, Field


class ServerErrorDetail(BaseModel):
    """Schema for public HTTP response errors."""
    reference_id: str
    message: str = "Error while contacting API"


class ServerErrorLog(ServerErrorDetail):
    """Schema for internal logger payload."""
    detail: str = Field(description="Exception message or string representation")
