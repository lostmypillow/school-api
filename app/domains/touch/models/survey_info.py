"""前端傳的評分資訊.


"""
from pydantic import BaseModel, Field


class SurveyInfo(BaseModel):  # noqa: D101
    employee_id: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="員工編號",
    )
    employee_dep: str
    student_id: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="學生student_id",
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="1–5 integer rating",
    )
