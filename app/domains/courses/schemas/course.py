from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseModel(BaseModel):
    """Core academic course model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Unique course identifier")
    department_year_id: str = Field(..., description="Parent department-year ID")
    year: str = Field(..., description="ROC school year")
    sem: str = Field(..., description="Semester number")
    code: Optional[str] = Field(default=None, description="Course 6-digit code")
    name: Optional[str] = Field(default=None, description="Course name")
    credits: Optional[int] = Field(default=None, description="Course credits")
    course_type: Optional[str] = Field(default=None, description="Course type, e.g. 必修/選修")
    instructor: Optional[str] = Field(default=None, description="Instructor name")
    sun: Optional[str] = Field(default=None, description="Sunday class hours")
    mon: Optional[str] = Field(default=None, description="Monday class hours")
    tue: Optional[str] = Field(default=None, description="Tuesday class hours")
    wed: Optional[str] = Field(default=None, description="Wednesday class hours")
    thu: Optional[str] = Field(default=None, description="Thursday class hours")
    fri: Optional[str] = Field(default=None, description="Friday class hours")
    sat: Optional[str] = Field(default=None, description="Saturday class hours")
    classroom: Optional[str] = Field(default=None, description="Classroom location")
    students_enrolled: Optional[int] = Field(default=None, description="Enrolled student count")
    students_dropped: Optional[int] = Field(default=None, description="Dropped student count")
    language: Optional[str] = Field(default=None, description="Teaching language")
    link: Optional[str] = Field(default=None, description="Syllabus URL")
    notes: Optional[str] = Field(default=None, description="Notes")
    with_class: Optional[str] = Field(default=None, description="With class")
    experiment: Optional[str] = Field(default=None, description="Experiment")
    cross_discipline: Optional[str] = Field(default=None, description="Cross discipline")


class CourseResponseSchema(CourseModel):
    """Response schema for /courses/courses."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    created_at: datetime
    updated_at: datetime
