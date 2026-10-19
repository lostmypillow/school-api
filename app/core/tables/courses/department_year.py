from datetime import datetime, UTC

from sqlalchemy import Column, Unicode, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.tables.base  import Base


class DepartmentYear(Base):
    """Represents items from 'dep_year_list' (e.g. 機械四乙, 體育專項)."""

    __tablename__ = "department_years"

    id = Column[str](Unicode(64), primary_key=True)  # Slug: e.g., "112_1_01_301"
    department_id = Column[str](
        Unicode(64), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    year = Column[str](Unicode(10), nullable=False)
    sem = Column[str](Unicode(10), nullable=False)
    code = Column[str](Unicode(20), nullable=False)
    name = Column[str](Unicode(255), nullable=False)
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

    __table_args__ = (
        UniqueConstraint(
            "year", "sem", "code", name="uq_department_years_year_sem_code"
        ),
    )

    department_rel = relationship(argument="Department", back_populates="classes")
    courses = relationship(argument="Course", back_populates="department_year_rel")
