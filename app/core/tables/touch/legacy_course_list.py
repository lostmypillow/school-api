from datetime import time
from typing import Optional

from sqlalchemy import Integer, Unicode, Time, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class LegacyCourseList(Base):
    __tablename__ = "legacy_course_list"

    classroom: Mapped[int] = mapped_column(Integer, primary_key=True)
    time_slot: Mapped[int] = mapped_column(Integer, primary_key=True)
    contents: Mapped[Optional[str]] = mapped_column(Unicode(255))
    course_time: Mapped[Optional[time]] = mapped_column(Time)
    record_date: Mapped[Optional[str]] = mapped_column(String(10))