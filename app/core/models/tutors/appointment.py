from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class TutorAppointment(Base):
    __tablename__ = "tutor_appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    teacher_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)