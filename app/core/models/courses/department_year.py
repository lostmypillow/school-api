from datetime import datetime, UTC

from sqlalchemy import Unicode, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.models.base  import Base


class DepartmentYear(Base):
    """Represents items from 'dep_year_list' (e.g. 機械四乙, 體育專項)."""

    __tablename__ = "department_years"

    id: Mapped[str] = mapped_column(Unicode(64), primary_key=True)  # Slug: e.g., "112_1_01_301"
    department_id: Mapped[str] = mapped_column(
        Unicode(64), ForeignKey("departments.id", ondelete="CASCADE")
    )
    year: Mapped[str] = mapped_column(Unicode(10))
    sem: Mapped[str] = mapped_column(Unicode(10))
    code: Mapped[str] = mapped_column(Unicode(20))
    name: Mapped[str] = mapped_column(Unicode(255))
    link: Mapped[str] = mapped_column(Unicode(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "year", "sem", "code", name="uq_department_years_year_sem_code"
        ),
    )

    department_rel = relationship(argument="Department", back_populates="classes")
    courses = relationship(argument="Course", back_populates="department_year_rel")
