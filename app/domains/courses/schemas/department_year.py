from datetime import datetime

from pydantic import ConfigDict, BaseModel, Field


class DepartmentYearModel(BaseModel):
    """Core academic department-year (class cohort) model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: str = Field(default=..., description="Unique department-year identifier, e.g. 113_1_001_0482")
    department_id: str = Field(default=..., description="Parent department ID, e.g. 113_1_001")
    year: str = Field(default=..., description="ROC school year, e.g. 113")
    sem: str = Field(default=..., description="Semester number, e.g. 1 or 2")
    code: str = Field(default=..., description="Department-year 4-digit code, e.g. 0482")
    name: str = Field(default=..., description="Department-year class name")
    link: str = Field(default=..., description="Relative URL to courses page")


class DepartmentYearResponseSchema(DepartmentYearModel):
    """Response schema for /courses/department_years."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    created_at: datetime
    updated_at: datetime
