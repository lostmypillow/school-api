from typing import Optional

from sqlalchemy import String, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Unicode(50))
    card_id: Mapped[Optional[str]] = mapped_column(String(20))
    gender: Mapped[Optional[str]] = mapped_column(Unicode(10))