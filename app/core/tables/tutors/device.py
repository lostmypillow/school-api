from sqlalchemy import Column, Integer, String

from app.core.tables.base_model import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=False)
    teacher_id = Column(String(20), nullable=True)
