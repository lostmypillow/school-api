"""補位學生登入資訊.


"""
from typing import Literal

from pydantic import BaseModel, Field


class AuthRequest(BaseModel):  # noqa: D101
    student_id: str = Field(
        ...,
        description="學生student_id",
    )
    type: Literal[
        "seat",
        "survey",
        "award",
    ] = Field(
        ...,
        description="驗證種類: 補位、評分或獎學金",
    )
