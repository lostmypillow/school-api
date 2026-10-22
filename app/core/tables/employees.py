from typing import Optional

from sqlalchemy import String, Unicode, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class User(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(Unicode(20), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True)
    card_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=False
    )
    college: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True)
    new_college: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    __table_args__ = (
        UniqueConstraint("name", name="uq_employees_name"),
        UniqueConstraint("card_id", name="uq_employees_card_id"),
        UniqueConstraint("email", name="uq_employees_email")
    )
