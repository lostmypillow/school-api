from datetime import UTC, datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Unicode(36), primary_key=True)  # Slug: e.g., "112_1"
    year = Column(Unicode(10), nullable=False)
    sem = Column(Unicode(10), nullable=False)
    link = Column(Unicode(2048), nullable=False)
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

    __table_args__ = (UniqueConstraint("year", "sem", name="uq_semesters_year_sem"),)

    departments = relationship("Department", back_populates="semester_rel")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Unicode(64), primary_key=True)  # Slug: e.g., "112_1_01"
    semester_id = Column(
        Unicode(36), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False
    )
    year = Column(Unicode(10), nullable=False)
    sem = Column(Unicode(10), nullable=False)
    code = Column(Unicode(20), nullable=False)
    name = Column(Unicode(255), nullable=False)
    link = Column(Unicode(2048), nullable=False)
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

    id = Column(Unicode(64), primary_key=True)  # Slug: e.g., "112_1_01_301"
    department_id = Column(
        Unicode(64), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    year = Column(Unicode(10), nullable=False)
    sem = Column(Unicode(10), nullable=False)
    code = Column(Unicode(20), nullable=False)
    name = Column(Unicode(255), nullable=False)
    link = Column(Unicode(2048), nullable=False)
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
        UniqueConstraint(
            "year", "sem", "code", name="uq_department_years_year_sem_code"
        ),
    )

    department_rel = relationship("Department", back_populates="classes")
    courses = relationship("Course", back_populates="department_year_rel")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Unicode(64), primary_key=True)  # Slug: e.g., "112_1_301_CS101"
    department_year_id = Column(
        Unicode(64),
        ForeignKey("department_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    year = Column(Unicode(10), nullable=False)
    sem = Column(Unicode(10), nullable=False)
    code = Column(Unicode(50), nullable=True)
    name = Column(Unicode(255), nullable=False)
    link = Column(Unicode(2048), nullable=True)
    credits = Column(Integer, nullable=True)  # Set to nullable=True for flexibility
    course_type = Column(Unicode(20), nullable=True)
    instructor = Column(Unicode(255), nullable=True)

    # Schedule & Location
    sun = Column(Unicode(50), nullable=True)
    mon = Column(Unicode(50), nullable=True)
    tue = Column(Unicode(50), nullable=True)
    wed = Column(Unicode(50), nullable=True)
    thu = Column(Unicode(50), nullable=True)
    fri = Column(Unicode(50), nullable=True)
    sat = Column(Unicode(50), nullable=True)
    classroom = Column(Unicode(255), nullable=True)

    # Metrics & Metadata
    students_enrolled = Column(Integer, nullable=True)
    students_dropped = Column(Integer, nullable=True)
    language = Column(Unicode(50), nullable=True)
    notes = Column(UnicodeText, nullable=True)
    with_class = Column(Unicode(255), nullable=True)
    experiment = Column(Unicode(255), nullable=True)
    cross_discipline = Column(Unicode(255), nullable=True)

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

    __table_args__ = (UniqueConstraint("id", name="uq_courses_year_sem_code"),)

    department_year_rel = relationship("DepartmentYear", back_populates="courses")
