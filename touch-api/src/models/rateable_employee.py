# TODO:ADD DOCSTRING
from typing import Literal

from pydantic import BaseModel, Field


class RateableEmployee(BaseModel):
    學號: str = Field(
        ...,
        example="000000",
        pattern=r"^\d{6}$",
        description="員工編號",
    )
    姓名: str = Field(
        ...,
        example="王小明",
        description="就...姓名",
    )
    主要部門: Literal[, , "", , ] = Field(
        ...,
        example="",
        description="部門",
    )
