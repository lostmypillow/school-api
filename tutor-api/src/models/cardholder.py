"""持卡人資訊."""
from typing import Literal

from pydantic import BaseModel, Field


class Cardholder(BaseModel):
    role: Literal["student", "teacher"] | None = None
    card_id: str | None = Field(None, alias="學號")
    name: str | None = Field(None, alias="姓名")
    school: str | None = Field(None, alias="大學")
    device_id: int | None = Field(None, alias="設備號碼")
    new_school: str | None = Field(None, alias="新大學")
