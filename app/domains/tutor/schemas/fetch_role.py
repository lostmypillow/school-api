"""用來判斷卡號是學生或老師."""
from pydantic import BaseModel, Field


class FetchRoleResponse(BaseModel):
    name: str | None = Field(None, alias="name")
    card_id: str | None = Field(None, alias="student_id")
