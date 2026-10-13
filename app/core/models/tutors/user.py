from sqlalchemy import Column, String, Unicode

from app.core.models.base_model import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(20), primary_key=True)
    name = Column(Unicode(50), nullable=True)
    card_id = Column(String(20), nullable=True)
    college = Column(Unicode(50), nullable=True)
    new_college = Column(Unicode(50), nullable=True)
    department = Column(String(10), nullable=True)
