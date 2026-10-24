from datetime import datetime, UTC

from sqlalchemy import Column, Unicode, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.tables.base import Base


class Semester(Base):
    __tablename__ = "semesters"

    id = Column[str](Unicode(36), primary_key=True)  # Slug: e.g., "112_1"
    year = Column[str](Unicode(10), nullable=False)
    sem = Column[str](Unicode(10), nullable=False)
    link = Column[str](Unicode(2048), nullable=False)
    created_at = Column[datetime](
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = Column[datetime](
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("year", "sem", name="uq_semesters_year_sem"),)

    departments = relationship(argument="Department", back_populates="semester_rel")
