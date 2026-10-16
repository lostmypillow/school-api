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


class DepartmentYearModel(BaseModel):
    """Core academic department-year (class cohort) model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Unique department-year identifier, e.g. 113_1_001_0482")
    department_id: str = Field(..., description="Parent department ID, e.g. 113_1_001")
    year: str = Field(..., description="ROC school year, e.g. 113")
    sem: str = Field(..., description="Semester number, e.g. 1 or 2")
    code: str = Field(..., description="Department-year 4-digit code, e.g. 0482")
    name: str = Field(..., description="Department-year class name")
    link: str = Field(..., description="Relative URL to courses page")


class DepartmentYearResponseSchema(DepartmentYearModel):
    """Response schema for /courses/department_years."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    created_at: datetime
    updated_at: datetime


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

    name: str = Field(..., description="Course name")
    created_at: datetime
    updated_at: datetime


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
