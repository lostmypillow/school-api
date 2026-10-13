"""補位學生登入回傳值.


"""
from typing import Literal

from pydantic import BaseModel, Field

from .rateable_employee import RateableEmployee


class AuthResponse(BaseModel):  # noqa: D101
    student_id: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="學生student_id",
    )
    name: str = Field(
        ...,
        description="就...name",
    )
    gender: Literal["male", "female"] = Field(
        ...,
        description="就...gender",
    )
    rateable_employees: list[RateableEmployee] = Field(
        default_factory=list,
        description="可評分員工",
    )
