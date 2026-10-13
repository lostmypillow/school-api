from typing import Optional

from sqlalchemy import Integer, String, CHAR, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class StudentSurveyResults(Base):
    __tablename__ = "student_survey_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(20))
    dep_number: Mapped[Optional[int]] = mapped_column(Integer)
    record_date: Mapped[Optional[str]] = mapped_column(CHAR(8))
    course_time: Mapped[Optional[str]] = mapped_column(String(20))
    subject: Mapped[Optional[str]] = mapped_column(String(20))
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(String(50))