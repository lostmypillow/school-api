from sqlalchemy import String, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base_model import Base


class User(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(50), nullable=True)
    card_id: Mapped[str] = mapped_column(String(20), nullable=True)
    college: Mapped[str] = mapped_column(Unicode(50), nullable=True)
    new_college: Mapped[str] = mapped_column(Unicode(50), nullable=True)
    department: Mapped[str] = mapped_column(String(10), nullable=True)
