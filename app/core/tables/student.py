from sqlalchemy import Column, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base_model import Base


class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(50), nullable=True)
    card_id: Mapped[str] = mapped_column(String(20), nullable=True)