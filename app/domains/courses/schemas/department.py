from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentModel(BaseModel):
    """Core academic department model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Unique department identifier, e.g. 113_1_001")
    semester_id: str = Field(..., description="Parent semester ID, e.g. 113_1")
    year: str = Field(..., description="ROC school year, e.g. 113")
    sem: str = Field(..., description="Semester number, e.g. 1 or 2")
    code: str = Field(..., description="Department 3-digit code, e.g. 001")
    name: str = Field(..., description="Department name")
    link: str = Field(..., description="Relative URL to department-year page")


class DepartmentResponseSchema(DepartmentModel):
    """Response schema for /courses/departments."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    created_at: datetime
    updated_at: datetime
