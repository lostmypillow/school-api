from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base_model import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    teacher_id: Mapped[str] = mapped_column(String(20), nullable=True)
