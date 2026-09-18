"""補位學生登入回傳值.


"""
from typing import Literal

from pydantic import BaseModel, Field

from .rateable_employee import RateableEmployee


class AuthResponse(BaseModel):  # noqa: D101
    學號: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="學生學號",
    )
    姓名: str = Field(
        ...,
        description="就...姓名",
    )
    性別: Literal["男", "女"] = Field(
        ...,
        description="就...性別",
    )
    rateable_employees: list[RateableEmployee] = Field(
        default_factory=list,
        description="可評分員工",
    )
