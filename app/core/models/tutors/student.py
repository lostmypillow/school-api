from sqlalchemy import Column, String, Unicode

from app.core.models.base_model import Base


class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(20), primary_key=True)
    name = Column(Unicode(50), nullable=True)
    card_id = Column(String(20), nullable=True)