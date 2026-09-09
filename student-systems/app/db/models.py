from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(String, primary_key=True)  # Slug: e.g., "112_1" (year_sem)
    year = Column(String, nullable=False)
    sem = Column(String, nullable=False)
    link = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("year", "sem", name="uq_semesters_year_sem"),
    )

    departments = relationship("Department", back_populates="semester_rel")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True)  # Slug: e.g., "112_1_01" (year_sem_code)
    semester_id = Column(
        String, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False
    )
    year = Column(String, nullable=False)
    sem = Column(String, nullable=False)
    code = Column(String, nullable=False)  # e.g., "01", "10", "30"
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    html_content = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("year", "sem", "code", name="uq_departments_year_sem_code"),
    )

    semester_rel = relationship("Semester", back_populates="departments")
    classes = relationship("DepartmentYear", back_populates="department_rel")


class DepartmentYear(Base):
    """Represents items from 'dep_year_list' (e.g. 機械四乙, 體育專項)."""

    __tablename__ = "department_years"

    id = Column(
        String, primary_key=True
    )  # Slug: e.g., "112_1_01_301" (year_sem_deptcode_code)
    department_id = Column(
        String, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    year = Column(String, nullable=False)
    sem = Column(String, nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    html_content = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("year", "sem", "code", name="uq_department_years_year_sem_code"),
    )

    department_rel = relationship("Department", back_populates="classes")
    courses = relationship("Course", back_populates="department_year_rel")


class Course(Base):
    __tablename__ = "courses"

    id = Column(
        String, primary_key=True
    )  # Slug: e.g., "112_1_301_CS101" (year_sem_depyearcode_code)
    department_year_id = Column(
        String, ForeignKey("department_years.id", ondelete="CASCADE"), nullable=False
    )
    year = Column(String, nullable=False)
    sem = Column(String, nullable=False)
    code = Column(String, nullable=False)
    department_year_code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    course_type = Column(String, nullable=False)
    instructor = Column(String, nullable=True)
    days_of_week = Column(String, nullable=False)
    times_of_day = Column(String, nullable=False)
    classroom = Column(String, nullable=False)
    students_enrolled = Column(Integer, nullable=False)
    students_dropped = Column(Integer, nullable=False)
    language = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    with_class = Column(String, nullable=True)
    experiment = Column(String, nullable=True)
    cross_discipline = Column(String, nullable=True)
    html_content = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("year", "sem", "code", name="uq_courses_year_sem_code"),
    )

    department_year_rel = relationship("DepartmentYear", back_populates="courses")
