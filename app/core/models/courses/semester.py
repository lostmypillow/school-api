from datetime import datetime, UTC

from sqlalchemy import Unicode, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.models.base import Base


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[str] = mapped_column(Unicode(36), primary_key=True)
    year: Mapped[str] = mapped_column(Unicode(10), nullable=False)
    sem: Mapped[str] = mapped_column(Unicode(10), nullable=False)
    link: Mapped[str] = mapped_column(Unicode(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    __table_args__ = (UniqueConstraint("year", "sem", name="uq_semesters_year_sem"),)

    departments = relationship(argument="Department", back_populates="semester_rel")
