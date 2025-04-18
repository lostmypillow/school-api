from pydantic import BaseModel, Field
from typing import Literal
from .rateable_employee import RateableEmployee

class AuthResponse(BaseModel):
    學號: str = Field(
        ...,
        pattern=r"^\d{6}$",
        example="",
        description="學生學號"
    )
    姓名: str = Field(
        ...,
        example="王小明",
        description="就...姓名"
    )
    性別: Literal["男", "女"] = Field(
        ...,
        example="女",
        description="就...性別"
    )
    rateable_employees: list[RateableEmployee] = Field(
        default_factory=list,
        example=[],
        description="可評分員工"
    )
