from datetime import datetime
from typing import Optional

from sqlalchemy import Unicode, ForeignKey, Integer, UnicodeText, DateTime, UniqueConstraint, text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.models.base  import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str]= mapped_column(Unicode(64), primary_key=True)
    department_year_id: Mapped[str] = mapped_column(
        Unicode(64),
        ForeignKey(column="department_years.id", ondelete="CASCADE")
    )
    year: Mapped[str] = mapped_column(Unicode(10))
    sem: Mapped[str] = mapped_column(Unicode(10))
    code: Mapped[Optional[str]] = mapped_column(Unicode(50))
    name: Mapped[str] = mapped_column(Unicode(255))
    link: Mapped[Optional[str]]  = mapped_column(Unicode(2048))
    credits: Mapped[Optional[int]] = mapped_column(Integer)
    course_type: Mapped[Optional[str]]  = mapped_column(Unicode(20))
    instructor: Mapped[Optional[str]]  = mapped_column(Unicode(255))

    # Schedule & Location
    sun: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    mon: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    tue: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    wed: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    thu: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    fri: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    sat: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    classroom: Mapped[Optional[str]]  = mapped_column(Unicode(255))

    # Metrics & Metadata
    students_enrolled: Mapped[Optional[int]] = mapped_column(Integer)
    students_dropped: Mapped[Optional[int]] = mapped_column(Integer)
    language: Mapped[Optional[str]]  = mapped_column(Unicode(50))
    notes: Mapped[Optional[str]]  = mapped_column(UnicodeText)
    with_class: Mapped[Optional[str]]  = mapped_column(Unicode(255))
    experiment: Mapped[Optional[str]]  = mapped_column(Unicode(255))
    cross_discipline: Mapped[Optional[str]]  = mapped_column(Unicode(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("SYSDATETIMEOFFSET()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("SYSDATETIMEOFFSET()"),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("id", name="uq_courses_year_sem_code"),)

    department_year_rel = relationship(argument="DepartmentYear", back_populates="courses")
