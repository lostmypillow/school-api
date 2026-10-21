from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseSyllabusModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,  # Enables compatibility with SQLAlchemy ORM models
    )
    id:str = Field(..., description="Unique course syllabus identifier")

    course_id: str = Field(default='', description="Corresponding course_id")

    instructor_name: Optional[str] = Field(
        default=None, description="Course instructor name", examples=["王正豪"]
    )
    email: Optional[str] = Field(
        default=None,
        description="Instructor contact email",
        examples=["jhwang@ntut.edu.tw"],
    )
    instructor_schedule: Optional[str] = Field(
        default=None, description="Class time schedule"
    )

    abstract: Optional[str] = Field(
        default=None, description="Course overview and main topics"
    )
    syllabus: Optional[str] = Field(
        default=None, description="Weekly course schedule and topics"
    )
    grading_policy: Optional[str] = Field(
        default=None, description="Grading criteria and percentage breakdown"
    )
    materials: Optional[str] = Field(
        default=None, description="Textbooks, reference links, and reading materials"
    )

    consultation: Optional[str] = Field(
        default=None, description="Office hours and contact methods"
    )
    ai: Optional[str] = Field(default=None, description="Generative AI usage policy")
    notes: Optional[str] = Field(
        default=None, description="General instructions and platform links"
    )
    sdg: Optional[str] = Field(
        default=None, description="Sustainable Development Goals alignment"
    )

    last_updated: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )
