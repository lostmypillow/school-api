"""設備資訊. 這個或 `src.schemas.device_info`是多餘的."""
from pydantic import AliasChoices, BaseModel, Field


class Device(BaseModel):
    device_id: int | None = Field(None, validation_alias=AliasChoices("device_id", "id"))
    teacher_id: str | None = Field(None, validation_alias=AliasChoices("teacher_id"))
