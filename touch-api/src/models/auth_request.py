from typing import Literal

from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    student_id: str = Field(
        ...,
        example="",
        description="學生學號",
    )
    type: Literal[
        "seat",
        "survey",
        "award",
    ] = Field(
        ...,
        example="seats",
        description="驗證種類: 補位、評分或獎學金",
    )
