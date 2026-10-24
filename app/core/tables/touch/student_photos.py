from typing import Optional

from sqlalchemy import String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class StudentPhotos(Base):
    __tablename__ = "student_photos"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    photo_bytes: Mapped[Optional[bytes]] = mapped_column(LargeBinary)