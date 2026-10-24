from sqlalchemy import Column, DateTime, Integer, String

from app.core.tables.base_model import Base


class TutorAppointment(Base):
    __tablename__ = "tutor_appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=True)
    student_id = Column(String(20), nullable=True)
    teacher_id = Column(String(20), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
