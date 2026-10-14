from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SemesterResponseSchema(BaseModel):
    """Schema for /courses/semesters."""

    model_config = ConfigDict(extra="forbid")

    id: str
    year: str
    sem: str
    link: str
    created_at: datetime
    updated_at: datetime


class DepartmentResponseSchema(BaseModel):
    """Schema for /courses/departments."""

    model_config = ConfigDict(extra="forbid")

    id: str
    semester_id: str
    year: str
    sem: str
    code: str
    name: str
    link: str
    created_at: datetime
    updated_at: datetime


class DepartmentYearResponseSchema(BaseModel):
    """Schema for /courses/department_years."""

    model_config = ConfigDict(extra="forbid")

    id: str
    department_id: str
    year: str
    sem: str
    code: str
    name: str
    link: str
    created_at: datetime
    updated_at: datetime


class CourseResponseSchema(BaseModel):
    """Schema for /courses/courses."""

    model_config = ConfigDict(extra="forbid")

    id: str
    department_year_id: str
    year: str
    sem: str
    code: Optional[str] = None
    name: str
    link: Optional[str] = None
    credits: Optional[int] = None
    course_type: Optional[str] = None
    instructor: Optional[str] = None
    sun: Optional[str] = None
    mon: Optional[str] = None
    tue: Optional[str] = None
    wed: Optional[str] = None
    thu: Optional[str] = None
    fri: Optional[str] = None
    sat: Optional[str] = None
    classroom: Optional[str] = None
    students_enrolled: Optional[int] = None
    students_dropped: Optional[int] = None
    language: Optional[str] = None
    notes: Optional[str] = None
    with_class: Optional[str] = None
    experiment: Optional[str] = None
    cross_discipline: Optional[str] = None
    created_at: datetime
    updated_at: datetime
