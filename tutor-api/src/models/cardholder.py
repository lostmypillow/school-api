from pydantic import BaseModel, Field
from typing import Literal, Optional


class Cardholder(BaseModel):
    role: Optional[Literal["student", "teacher"]] = None
    card_id:  Optional[str] = Field(None, alias="學號")
    name: Optional[str] = Field(None, alias="姓名")
    school: Optional[str] = Field(None, alias="大學")
    device_id: Optional[int] = Field(None, alias='設備號碼')
