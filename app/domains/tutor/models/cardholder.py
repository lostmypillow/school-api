"""持卡人資訊."""
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


class Cardholder(BaseModel):
    role: Literal["student", "teacher"] | None = None
    card_id: str | None = Field(None, validation_alias=AliasChoices("student_id", "id", "student_id", "card_id"))
    name: str | None = Field(None, validation_alias=AliasChoices("name", "name"))
    school: str | None = Field(None, validation_alias=AliasChoices("college", "大學", "school"))
    device_id: int | None = Field(None, validation_alias=AliasChoices("device_id", "設備號碼"))
    new_school: str | None = Field(None, validation_alias=AliasChoices("new_college", "新大學", "new_school"))
