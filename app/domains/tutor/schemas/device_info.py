"""設備資訊. 這個或 `src.schemas.device`是多餘的."""
from pydantic import AliasChoices, BaseModel, Field


class DeviceInfo(BaseModel):
    device_id: int = Field(..., validation_alias=AliasChoices("device_id", "id", "設備號碼"))
    teacher_id: str | None = Field(None, validation_alias=AliasChoices("teacher_id", "老師編號"))
