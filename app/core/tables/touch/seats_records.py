from datetime import datetime, UTC

from sqlalchemy import Integer, ForeignKey, Unicode, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class SeatRecords(Base):
    __tablename__ = "seats_records"
    
    sn: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_no: Mapped[int] = mapped_column(Integer, ForeignKey("seats_master.file_no", ondelete="CASCADE"))
    seat_no: Mapped[str] = mapped_column(Unicode(20))
    student_id: Mapped[str] = mapped_column(String(20), ForeignKey(column="students.student_id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )