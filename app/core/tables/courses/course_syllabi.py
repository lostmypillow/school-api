from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Unicode, UnicodeText, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class CourseSyllabus(Base):
    __tablename__ = "course_syllabi"

    id: Mapped[str] = mapped_column(Unicode(100), primary_key=True)
    course_id: Mapped[str] = mapped_column(Unicode(64), ForeignKey(column="courses.id", ondelete="CASCADE"))
    instructor_name: Mapped[Optional[str]] = mapped_column(Unicode(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)
    instructor_schedule: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)

    abstract: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    syllabus: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    grading_policy: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    materials: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)

    consultation: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    ai: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    sdg: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)

    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<CourseSyllabus(id={self.id}, instructor='{self.instructor_name}')>"
