from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SemesterBase(BaseModel):
    """Base schema for academic semester."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Unique semester identifier, e.g. 113_1")
    year: str = Field(..., description="ROC school year, e.g. 113")
    sem: str = Field(..., description="Semester number, e.g. 1 or 2")
    link: str = Field(..., description="Catalog URL")


class SemesterModel(SemesterBase):
    """Catalog semester model with optional scraped display name."""

    name: Optional[str] = Field(default=None, description="Semester name")


class SemesterResponseSchema(SemesterBase):
    """Response schema for /courses/semesters."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    created_at: datetime
    updated_at: datetime
