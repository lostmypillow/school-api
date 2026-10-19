from typing import Optional

from sqlalchemy import String, Unicode
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