from datetime import datetime, UTC

from sqlalchemy import Integer, Unicode, String, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.core.tables.base import Base


class SeatMaster(Base):
    __table_name__="seats_master"

    file_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    legacy_course_num: Mapped[str] = mapped_column(Unicode(20), ForeignKey("legacy_course_num.legacy_course.num"))
    legacy_course_num_2: Mapped[str] = mapped_column(Unicode(20))
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    record_date: Mapped[str] = mapped_column(String(10))
    