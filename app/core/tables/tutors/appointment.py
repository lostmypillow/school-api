from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base_model import Base


class TutorAppointment(Base):
    __tablename__ = "tutor_appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str]= mapped_column(String(10), nullable=True)
    student_id: Mapped[str] = mapped_column(String(20), nullable=True)
    teacher_id: Mapped[str]  = mapped_column(String(20), nullable=True)
    start_time: Mapped[datetime]  = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
