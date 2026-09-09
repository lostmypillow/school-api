"""設備資訊. 這個或 `src.models.device_info`是多餘的."""
from pydantic import BaseModel, Field


class Device(BaseModel):
    device_id: int | None = Field(None)
    teacher_id: int | None = Field(None)
