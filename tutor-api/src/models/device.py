
from pydantic import BaseModel, Field


class Device(BaseModel):
    device_id: int | None = Field(None)
    teacher_id: int | None = Field(None)
