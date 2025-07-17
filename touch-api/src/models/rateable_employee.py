"""可評分之員工.


"""
from typing import Literal

from pydantic import BaseModel, Field


class RateableEmployee(BaseModel):  # noqa: D101
    學號: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="員工編號",
    )
    姓名: str = Field(
        ...,
        description="就...姓名",
    )
    主要部門: Literal[, , "", , ] = Field(
        ...,
        description="部門",
    )
