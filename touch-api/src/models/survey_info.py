from pydantic import BaseModel, Field


class SurveyInfo(BaseModel):
    employee_id: str = Field(
        ...,
        pattern=r"^\d{6}$",
        example="",
        description="員工編號"
    )
    employee_dep: str = Field(
        ...,
        example=""
    )
    student_id: str = Field(
        ...,
        pattern=r"^\d{6}$",
        example="",
        description="學生學號"
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        example=4,
        description="1–5 integer rating"
    )
