from typing import Optional

from sqlalchemy import Unicode, Integer
from sqlalchemy.orm import mapped_column, Mapped

from app.core.models.base import Base


class TodaysSeats(Base):
    __tablename__ = "todays_seats"

    file_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_name: Mapped[Optional[str]] = mapped_column(Unicode(100))
    legacy_course_num: Mapped[Optional[str]] = mapped_column(Unicode(50))