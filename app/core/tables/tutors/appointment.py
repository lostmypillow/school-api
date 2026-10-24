from datetime import datetime

from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class TutorAppointment(Base):
    __tablename__ = "tutor_appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str]= mapped_column(String(10), nullable=True)
    student_id: Mapped[str] = mapped_column(ForeignKey(column="students.student_id", ondelete="SET NULL"), nullable=True)
    teacher_id: Mapped[str]  = mapped_column(ForeignKey(column="employees.id", ondelete="SET NULL"), nullable=True)
    start_time: Mapped[datetime]  = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
